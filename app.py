from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

def shorten_url(long_url):
    """
    Сокращает ссылку через API clck.ru.
    """
    try:
        # API clck.ru не требует ключа. Просто отправляем GET-запрос.
        # Документация: https://clck.ru/--?url=ДЛИННАЯ_ССЫЛКА
        short_api_url = f"https://clck.ru/--?url={long_url}"
        response = requests.get(short_api_url, timeout=10)
        
        if response.status_code == 200:
            # API возвращает просто текст с короткой ссылкой
            short_url = response.text.strip()
            logging.info(f"Ссылка сокращена: {short_url}")
            return short_url
        else:
            logging.warning(f"Не удалось сократить ссылку, статус: {response.status_code}")
            # Если не удалось сократить, возвращаем исходную длинную ссылку
            return long_url
    except Exception as e:
        logging.error(f"Ошибка при сокращении ссылки: {e}")
        # В случае любой ошибки возвращаем исходную ссылку
        return long_url

@app.route('/download', methods=['GET', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 200

    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    logging.info(f"Получен URL: {url}")

    try:
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'origin': 'https://media.ytmp3.gg',
            'referer': 'https://media.ytmp3.gg/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        payload = {
            "url": url,
            "os": "windows",
            "output": {"type": "audio", "format": "mp3"},
            "audio": {"bitrate": "320k"}
        }

        resp = requests.post('https://hub.convert1s.com/api/download', json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            return jsonify({'error': f'API error: {resp.status_code}'}), 500

        data = resp.json()
        status_url = data.get('statusUrl')
        if not status_url:
            return jsonify({'error': 'No statusUrl'}), 500

        # Опрашиваем статус до получения ссылки
        for _ in range(30):  # до 60 секунд
            time.sleep(2)
            status_resp = requests.get(status_url, timeout=20)
            if status_resp.status_code != 200:
                continue
            status_data = status_resp.json()
            if 'downloadUrl' in status_data and status_data['downloadUrl']:
                long_mp3_url = status_data['downloadUrl']
                logging.info(f"Получена длинная ссылка на MP3: {long_mp3_url}")
                
                # --- НОВЫЙ ШАГ: сокращаем ссылку ---
                short_mp3_url = shorten_url(long_mp3_url)
                # Возвращаем уже короткую ссылку
                return jsonify({'link': short_mp3_url})
            if status_data.get('status') == 'error' or status_data.get('state') == 'error':
                break

        return jsonify({'error': 'Conversion timeout'}), 500

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
