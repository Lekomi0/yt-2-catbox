from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import uuid
import os
import time
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

@app.route('/download', methods=['GET', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 200

    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    logging.info(f"Received URL: {url}")

    # Пробуем два API по очереди
    apis = [
        {
            "name": "convert1s",
            "endpoint": "https://hub.convert1s.com/api/download",
            "method": "POST",
            "payload": {
                "url": url,
                "os": "windows",
                "output": {"type": "audio", "format": "mp3"},
                "audio": {"bitrate": "320k"}
            },
            "timeout": 60
        },
        {
            "name": "vevioz",
            "endpoint": "https://api.vevioz.com/api/button/mp3/",
            "method": "GET",
            "url_param": True,
            "timeout": 60
        }
    ]

    for api in apis:
        try:
            logging.info(f"Trying API: {api['name']}")
            if api['method'] == 'GET':
                resp = requests.get(api['endpoint'] + url, timeout=api['timeout'])
            else:
                resp = requests.post(api['endpoint'], json=api['payload'], timeout=api['timeout'])
            if resp.status_code != 200:
                logging.warning(f"API {api['name']} returned {resp.status_code}")
                continue

            data = resp.json()

            # Для convert1s
            if 'statusUrl' in data:
                status_url = data['statusUrl']
                for _ in range(30):  # 30 попыток * 2 сек = 60 сек
                    time.sleep(2)
                    status_resp = requests.get(status_url, timeout=20)
                    if status_resp.status_code != 200:
                        continue
                    status_data = status_resp.json()
                    if 'downloadUrl' in status_data and status_data['downloadUrl']:
                        mp3_url = status_data['downloadUrl']
                        logging.info(f"Got MP3 URL from {api['name']}: {mp3_url}")
                        return process_mp3(mp3_url)
                    if status_data.get('status') == 'error' or status_data.get('state') == 'error':
                        break

            # Для вевиоза
            if 'download' in data and data['download']:
                mp3_url = data['download']
                logging.info(f"Got MP3 URL from {api['name']}: {mp3_url}")
                return process_mp3(mp3_url)

        except Exception as e:
            logging.error(f"API {api['name']} error: {str(e)}")
            continue

    return jsonify({'error': 'All APIs failed'}), 500

def process_mp3(mp3_url):
    """Скачивает MP3 и загружает на Catbox"""
    try:
        logging.info("Downloading MP3...")
        # Увеличенный таймаут на скачивание
        mp3_resp = requests.get(mp3_url, stream=True, timeout=120)
        if mp3_resp.status_code != 200:
            logging.error(f"Failed to download MP3: {mp3_resp.status_code}")
            return jsonify({'error': 'Failed to download MP3'}), 500

        filename = f"audio_{uuid.uuid4().hex}.mp3"
        with open(filename, 'wb') as f:
            for chunk in mp3_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logging.info("MP3 downloaded successfully")

        logging.info("Uploading to Catbox...")
        with open(filename, 'rb') as f:
            upload_resp = requests.post(
                'https://catbox.moe/user/api.php',
                data={'reqtype': 'fileupload'},
                files={'fileToUpload': f},
                timeout=60
            )
        if upload_resp.status_code != 200:
            logging.error(f"Catbox upload failed: {upload_resp.status_code}")
            os.remove(filename)
            return jsonify({'error': 'Catbox upload failed'}), 500

        direct_link = upload_resp.text.strip()
        os.remove(filename)
        logging.info(f"Uploaded to Catbox: {direct_link}")
        return jsonify({'link': direct_link})

    except requests.exceptions.Timeout:
        logging.error("Timeout during MP3 download or upload")
        return jsonify({'error': 'Request timeout'}), 500
    except Exception as e:
        logging.error(f"Error in process_mp3: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
