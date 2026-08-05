from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import uuid
import os
import re

app = Flask(__name__)

CONVERTER_URL = "https://media.ytmp3.gg/tools/youtube-to-mp3-320kbps-converter/"

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    try:
        # 1. Отправляем запрос к конвертеру
        response = requests.post(
            CONVERTER_URL,
            data={'url': url},
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        if response.status_code != 200:
            return jsonify({'error': f'Converter error {response.status_code}'}), 500

        html = response.text

        # 2. Ищем ссылку по паттерну, который ты нашёл в F12
        pattern = r'https://vps-[^/]+\.mnmnmnmnmnnm\.site/files/[^/]+/output\.mp3\?token=[^&\s]+&expires=\d+'
        match = re.search(pattern, html)
        if match:
            download_link = match.group(0)
        else:
            # Если не нашлось — пробуем искать в тегах <a> с href, содержащим .mp3
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                if '.mp3' in a['href']:
                    download_link = a['href']
                    if download_link.startswith('/'):
                        download_link = 'https://media.ytmp3.gg' + download_link
                    break
            else:
                # Ищем в любых скриптах
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        match = re.search(pattern, script.string)
                        if match:
                            download_link = match.group(0)
                            break

        if not download_link:
            return jsonify({'error': 'Could not extract MP3 link'}), 500

        # 3. Скачиваем MP3
        mp3_response = requests.get(download_link, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
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
        os.remove(filename)

        return jsonify({'link': direct_link})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
