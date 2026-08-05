from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import uuid
import os

app = Flask(__name__)

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    try:
        # Отправляем запрос к конвертеру
        converter_url = "https://pokojedanusia.pl/"
        response = requests.post(
            converter_url,
            data={'u': url},  # параметр называется 'u', как в твоей ссылке
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        if response.status_code != 200:
            return jsonify({'error': 'Converter site error'}), 500

        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем ссылку на MP3: обычно это тег <a> с текстом "Download MP3" или ссылкой на .mp3
        download_link = None
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'mp3' in href.lower() or 'download' in href.lower() or 'pobierz' in href.lower():
                download_link = href
                break

        # Если не нашли — ищем в скриптах
        if not download_link:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'mp3' in script.string.lower():
                    import re
                    match = re.search(r'(https?://[^\s"\']+\.mp3)', script.string)
                    if match:
                        download_link = match.group(1)
                        break

        if not download_link:
            # Попробуем найти в любом элементе с атрибутом data-url или подобным
            for tag in soup.find_all(attrs={'data-url': True}):
                if 'mp3' in tag['data-url'].lower():
                    download_link = tag['data-url']
                    break

        if not download_link:
            return jsonify({'error': 'Could not extract MP3 link'}), 500

        # Если ссылка относительная — делаем абсолютной
        if download_link.startswith('/'):
            download_link = 'https://pokojedanusia.pl' + download_link

        # Скачиваем MP3
        mp3_response = requests.get(download_link, stream=True)
        if mp3_response.status_code != 200:
            return jsonify({'error': 'Failed to download MP3'}), 500

        filename = f"audio_{uuid.uuid4().hex}.mp3"
        with open(filename, 'wb') as f:
            for chunk in mp3_response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Загружаем на Catbox
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
