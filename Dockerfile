FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    iptables \
    iproute2 \
    net-tools \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Скачиваем последнюю стабильную версию оригинального zapret
RUN wget -O /tmp/zapret.zip https://github.com/bol-van/zapret/releases/latest/download/zapret-linux.zip \
    && unzip /tmp/zapret.zip -d /tmp/ \
    && cp /tmp/zapret-linux/nfqws /usr/local/bin/ \
    && chmod +x /usr/local/bin/nfqws \
    && rm -rf /tmp/zapret.zip /tmp/zapret-linux

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем nfqws (основной инструмент zapret) в фоне и Flask
CMD bash -c "/usr/local/bin/nfqws --filter-tcp=80,443 --filter-udp=443 --dpi-desync=fake --dpi-desync-ttl=5 & sleep 3 && python app.py"
