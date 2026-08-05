from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import uuid
import os
import subprocess

app = Flask(__name__)

# Выбираем сайт-конвертер (первый из вашего списка — ytmp3.gg)
CONVERTER_URL = "https://media.ytmp3.gg/tools/youtube-to-mp3-320kbps-converter/"

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    try:
        # 1. Отправляем запрос к сайту-конвертеру
        # Сайт ожидает POST-запрос с параметром "url"
        response = requests.post(
            CONVERTER_URL,
            data={'url': url},
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        if response.status_code != 200:
            return jsonify({'error': 'Converter site returned error'}), 500

        # 2. Парсим HTML, ищем ссылку на скачивание MP3
        soup = BeautifulSoup(response.text, 'html.parser')
        # Ищем тег <a> с классом, содержащим "download" или ссылкой на .mp3
        download_link = None
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.endswith('.mp3') or 'download' in href.lower():
                download_link = href
                break
        # Если не нашли — пробуем найти в JavaScript-скрипте или в data-атрибутах
        if not download_link:
            # Ищем скрипт с переменной download_url
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'download' in script.string.lower():
                    import re
                    match = re.search(r'(https?://[^\s"\']+\.mp3)', script.string)
                    if match:
                        download_link = match.group(1)
                        break

        if not download_link:
            return jsonify({'error': 'Could not extract MP3 link from converter'}), 500

        # Если ссылка относительная — добавляем домен
        if download_link.startswith('/'):
            download_link = 'https://media.ytmp3.gg' + download_link

        # 3. Скачиваем MP3 по прямой ссылке
        mp3_response = requests.get(download_link, stream=True)
        if mp3_response.status_code != 200:
            return jsonify({'error': 'Failed to download MP3'}), 500

        filename = f"audio_{uuid.uuid4().hex}.mp3"
        with open(filename, 'wb') as f:
            for chunk in mp3_response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 4. Загружаем на Catbox
        with open(filename, 'rb') as f:
            upload_response = requests.post(
                'https://catbox.moe/user/api.php',
                data={'reqtype': 'fileupload'},
                files={'fileToUpload': f}
            )
        direct_link = upload_response.text.strip()

        # Чистим
        os.remove(filename)

        return jsonify({'link': direct_link})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
