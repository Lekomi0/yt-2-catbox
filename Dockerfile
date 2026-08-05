FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    iptables \
    iproute2 \
    net-tools \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копируем бинарник zapret из готового образа (содержит всё: сам zapret + зависимости)
COPY --from=ghcr.io/sergeydigl3/zapret-discord-youtube-linux:latest /usr/local/bin/zapret /usr/local/bin/zapret
COPY --from=ghcr.io/sergeydigl3/zapret-discord-youtube-linux:latest /usr/local/bin/zapret /usr/local/bin/
# Если нужны дополнительные файлы (например, конфиги), можно скопировать и их
# COPY --from=ghcr.io/sergeydigl3/zapret-discord-youtube-linux:latest /etc/zapret /etc/zapret

# Делаем исполняемым
RUN chmod +x /usr/local/bin/zapret

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Запускаем zapret в фоне (режим 1, порт 1080) и затем Flask
CMD bash -c "/usr/local/bin/zapret --mode=1 --port=1080 & sleep 3 && python app.py"
