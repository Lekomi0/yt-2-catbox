FROM python:3.11-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    git \
    iptables \
    iproute2 \
    net-tools \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Клонируем репозиторий с бинарниками
WORKDIR /opt
RUN git clone https://github.com/Flowseal/zapret-discord-youtube.git zapret
# Делаем бинарник исполняемым (он уже должен быть, но на всякий случай)
RUN chmod +x /opt/zapret/bin/zapret

# Рабочая папка приложения
WORKDIR /app
COPY . .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем zapret в фоне (режим 1, порт 1080) и затем Flask
CMD bash -c "/opt/zapret/bin/zapret --mode=1 --port=1080 & sleep 3 && python app.py"
