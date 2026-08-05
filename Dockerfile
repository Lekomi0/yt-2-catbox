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

# Скачиваем бинарник zapret с релизов (используем wget с правильными заголовками)
RUN wget --header="Accept: application/octet-stream" \
         --header="User-Agent: Mozilla/5.0" \
         -O /tmp/zapret.zip \
         https://github.com/Flowseal/zapret-discord-youtube/releases/download/1.10.0/zapret-1.10.0.zip \
    && unzip /tmp/zapret.zip -d /tmp/ \
    && cp /tmp/zapret-1.10.0/bin/zapret /usr/local/bin/ \
    && chmod +x /usr/local/bin/zapret \
    && rm -rf /tmp/zapret.zip /tmp/zapret-1.10.0

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD bash -c "/usr/local/bin/zapret --mode=1 --port=1080 & sleep 3 && python app.py"
