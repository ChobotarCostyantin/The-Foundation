FROM python:3.10-slim

# Встановлюємо робочу директорію в контейнері
WORKDIR /app

# Копіюємо файл залежностей та встановлюємо їх
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо решту файлів проєкту (app.py, templates, static)
COPY . .

# Відкриваємо порт, на якому працює Flask
EXPOSE 8080

# Команда для запуску додатку
# Використовуємо gunicorn (або просто flask run) для Production
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8080"]