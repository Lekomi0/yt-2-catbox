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

    # Генерируем уникальное имя для файла, чтобы не было конфликтов
    filename = f"audio_{uuid.uuid4().hex}.mp3"

    try:
        # Скачиваем и конвертируем видео в MP3 с помощью yt-dlp
        subprocess.run([
    "yt-dlp",
    "--cookies", "cookies.txt",   # <-- ЭТА НОВАЯ СТРОКА
    "-x",
    "--audio-format", "mp3",
    "--audio-quality", "0",
    "-o", filename,
    url
], check=True, timeout=300)

        # Загружаем получившийся файл на Catbox
        with open(filename, 'rb') as f:
            response = requests.post(
                'https://catbox.moe/user/api.php',
                data={'reqtype': 'fileupload'},
                files={'fileToUpload': f}
            )
        direct_link = response.text.strip()

        # Удаляем файл с сервера
        os.remove(filename)

        return jsonify({'link': direct_link})

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Conversion timed out'}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'yt-dlp failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
