FROM pirst/zsylx:latest

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD bash -c "supervisord -c /etc/supervisor/conf.d/supervisord.conf & sleep 5 && python app.py"
