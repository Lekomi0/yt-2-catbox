# Используем готовый образ с zapret и SOCKS5-прокси
FROM pirst/zsylx:latest

# Копируем ваш код приложения в образ
WORKDIR /app
COPY . .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем zapret (уже внутри образа) и Flask-приложение
CMD bash -c "supervisord -c /etc/supervisor/conf.d/supervisord.conf & sleep 5 && python app.py"
