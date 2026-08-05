from flask import Flask, request, jsonify
import subprocess
import os
import requests
import uuid

app = Flask(__name__)

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    filename = f"audio_{uuid.uuid4().hex}.mp3"

    try:
        # Проверим, существует ли файл cookies.txt
        if os.path.exists('cookies.txt'):
            cookie_arg = ['--cookies', 'cookies.txt']
        else:
            cookie_arg = []
            print("WARNING: cookies.txt not found, proceeding without")

        cmd = [
            "yt-dlp",
            *cookie_arg,
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--extractor-args", "youtube:player-client=web,default",  # добавляем обход
            "-o", filename,
            url
        ]

        # Запускаем с захватом вывода
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            # Возвращаем подробную ошибку
            error_message = result.stderr.strip() or result.stdout.strip()
            return jsonify({'error': f'yt-dlp failed: {error_message}'}), 500

        # Если успешно — загружаем на Catbox
        with open(filename, 'rb') as f:
            response = requests.post(
                'https://catbox.moe/user/api.php',
                data={'reqtype': 'fileupload'},
                files={'fileToUpload': f}
            )
        direct_link = response.text.strip()
        os.remove(filename)
        return jsonify({'link': direct_link})

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Conversion timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
