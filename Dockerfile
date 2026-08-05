FROM python:3.11-slim

# Устанавливаем системные зависимости: git, python, iptables, ffmpeg и др.
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    iptables \
    iproute2 \
    net-tools \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Клонируем официальный репозиторий zapret-discord-youtube
WORKDIR /opt
RUN git clone https://github.com/Flowseal/zapret-discord-youtube.git zapret

# Устанавливаем права на выполнение (если нужно)
RUN chmod +x /opt/zapret/zapret.py

# Рабочая папка для приложения
WORKDIR /app
COPY . .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем zapret в фоне (режим 1, порт 1080) и затем Flask-приложение
CMD bash -c "cd /opt/zapret && python zapret.py --mode=1 --port=1080 & sleep 3 && cd /app && python app.py"
