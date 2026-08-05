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
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Клонируем оригинальный репозиторий zapret
WORKDIR /opt
RUN git clone https://github.com/bol-van/zapret.git zapret

# Собираем nfqws (основной бинарник) из исходников
WORKDIR /opt/zapret/src
RUN make -j$(nproc) && \
    cp nfqws /usr/local/bin/ && \
    chmod +x /usr/local/bin/nfqws

# Копируем приложение
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем nfqws в фоне (стандартные параметры для обхода DPI) и Flask
CMD bash -c "/usr/local/bin/nfqws --filter-tcp=80,443 --filter-udp=443 --dpi-desync=fake --dpi-desync-ttl=5 & sleep 3 && python app.py"
