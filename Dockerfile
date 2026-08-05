FROM python:3.11-slim

# Устанавливаем зависимости для сборки и работы
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    autoconf \
    automake \
    libtool \
    pkg-config \
    libnet1-dev \
    libpcap0.8-dev \
    iptables \
    iproute2 \
    net-tools \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Клонируем репозиторий zapret-discord-youtube
WORKDIR /opt
RUN git clone https://github.com/Flowseal/zapret-discord-youtube.git zapret

# Собираем zapret из исходников
WORKDIR /opt/zapret
RUN make -C src -j$(nproc) && \
    make -C src install

# Копируем приложение
WORKDIR /app
COPY . .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем zapret в фоне (режим 1, порт 1080) и Flask
CMD bash -c "/usr/local/bin/zapret --mode=1 --port=1080 & sleep 3 && python app.py"
