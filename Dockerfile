FROM python:3.11-slim

# Устанавливаем FFmpeg и curl (для проверки)
RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Устанавливаем zapret из готового образа
COPY --from=pirst/zsylx:latest /opt/zapret /opt/zapret
COPY --from=pirst/zsylx:latest /usr/local/bin/zapret /usr/local/bin/zapret

# Запускаем zapret в фоне и Flask-приложение
CMD bash -c "zapret --daemon --mode=1 --port=1080 && python app.py"
