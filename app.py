from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import requests
import uuid
import time
import logging

app = Flask(__name__)
CORS(app)

# Настройка логирования (для отладки)
logging.basicConfig(level=logging.INFO)

# Адрес прокси, который поднимает Zapret внутри контейнера
PROXY = "socks5://127.0.0.1:1080"

@app.route('/download', methods=['GET', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 200

    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    filename = f"audio_{uuid.uuid4().hex}.mp3"

    # Попытки конвертации (до 3 раз)
    for attempt in range(3):
        try:
            logging.info(f"Attempt {attempt+1} for {url}")
            
            # Команда yt-dlp с прокси
            cmd = [
                "yt-dlp",
                "--proxy", PROXY,
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",  # 0 = лучшее качество (обычно 320kbps)
                "--extractor-args", "youtube:player-client=web,default",
                "-o", filename,
                url
            ]

            # Запускаем с таймаутом 180 секунд
            subprocess.run(cmd, check=True, timeout=180)

            # Если успешно — загружаем на Catbox
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

        except subprocess.TimeoutExpired:
            logging.error("yt-dlp timeout")
            continue
        except subprocess.CalledProcessError as e:
            logging.error(f"yt-dlp error: {e.stderr}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            continue

    # Если все попытки провалились
    return jsonify({'error': 'Conversion failed after multiple attempts'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
