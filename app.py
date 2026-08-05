from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import uuid
import os
import time

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['GET', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 200

    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://media.ytmp3.gg',
        'referer': 'https://media.ytmp3.gg/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'
    }
    payload = {
        "url": url,
        "os": "windows",
        "output": {"type": "audio", "format": "mp3"},
        "audio": {"bitrate": "320k"}
    }

    for attempt in range(5):
        try:
            resp = requests.post('https://hub.convert1s.com/api/download', json=payload, headers=headers, timeout=30)
            if resp.status_code != 200:
                continue

            data = resp.json()
            status_url = data.get('statusUrl')
            if not status_url:
                continue

            download_link = None
            for _ in range(50):
                time.sleep(2)
                status_resp = requests.get(status_url, headers={'user-agent': headers['user-agent']}, timeout=20)
                if status_resp.status_code != 200:
                    continue
                status_data = status_resp.json()
                if 'downloadUrl' in status_data and status_data['downloadUrl']:
                    download_link = status_data['downloadUrl']
                    break
                elif 'url' in status_data and status_data['url']:
                    download_link = status_data['url']
                    break
                if (status_data.get('status') == 'error' or status_data.get('state') == 'error') and _ > 5:
                    break

            if download_link:
                mp3_resp = requests.get(download_link, stream=True, headers={'user-agent': headers['user-agent']}, timeout=60)
                if mp3_resp.status_code != 200:
                    continue

                filename = f"audio_{uuid.uuid4().hex}.mp3"
                with open(filename, 'wb') as f:
                    for chunk in mp3_resp.iter_content(chunk_size=8192):
                        f.write(chunk)

                with open(filename, 'rb') as f:
                    upload_resp = requests.post(
                        'https://catbox.moe/user/api.php',
                        data={'reqtype': 'fileupload'},
                        files={'fileToUpload': f},
                        timeout=30
                    )
                direct_link = upload_resp.text.strip()
                os.remove(filename)
                return jsonify({'link': direct_link})

        except Exception:
            continue

    return jsonify({'error': 'Conversion failed after multiple attempts'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
