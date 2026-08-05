FROM python:3.11-slim

# Устанавливаем зависимости: curl, unzip, iptables, и для сборки (если понадобится)
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    iptables \
    iproute2 \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Скачиваем официальный релиз Zapret (версия 1.10.0)
WORKDIR /opt
RUN curl -L -o zapret.zip https://github.com/Flowseal/zapret-discord-youtube/releases/download/1.10.0/zapret-1.10.0.zip \
    && unzip zapret.zip \
    && rm zapret.zip \
    && mv zapret-* zapret

# Копируем конфигурационный файл (пример базовых настроек)
# Можно создать свой config.txt или оставить дефолтный
COPY zapret-config.txt /opt/zapret/config.txt

# Устанавливаем рабочую директорию приложения
WORKDIR /app
COPY . .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Стартуем Zapret в фоне и затем Flask-приложение
# Запускаем через bash, чтобы выполнить несколько команд
CMD bash -c "cd /opt/zapret && ./zapret.sh --start && cd /app && python app.py"
