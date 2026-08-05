from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import requests
import uuid

app = Flask(__name__)
CORS(app)

# Твой прокси (HTTP)
PROXY = "http://173.212.245.136:8888"

@app.route('/download', methods=['GET', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 200

    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    filename = f"audio_{uuid.uuid4().hex}.mp3"

    try:
        cmd = [
            "yt-dlp",
            "--proxy", PROXY,
            "-x", "--audio-format", "mp3",
            "--audio-quality", "0",
            "--extractor-args", "youtube:player-client=web,default",
            "-o", filename,
            url
        ]
        subprocess.run(cmd, check=True, timeout=300)

        with open(filename, 'rb') as f:
            upload_resp = requests.post(
                'https://catbox.moe/user/api.php',
                data={'reqtype': 'fileupload'},
                files={'fileToUpload': f}
            )
        direct_link = upload_resp.text.strip()
        os.remove(filename)

        return jsonify({'link': direct_link})

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Conversion timeout'}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'yt-dlp error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
