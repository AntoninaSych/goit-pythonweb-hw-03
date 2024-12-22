# Використовуємо офіційний образ Python
FROM python:3.9

# Встановлення робочої директорії
WORKDIR /app

# Копіюємо файли до контейнера
COPY . /app

# Встановлюємо необхідні залежності
RUN pip install --no-cache-dir --upgrade pip

# Відкриваємо порт 3000
EXPOSE 3000

# Запускаємо сервер
CMD ["python", "server.py"]
