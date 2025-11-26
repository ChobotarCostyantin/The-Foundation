# Використовуємо офіційний образ Python
FROM python:3.9-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файл залежностей
COPY requirements.txt .

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код проєкту
COPY . .

# Відкриваємо порт 5000 (стандартний для Flask)
EXPOSE 5000

# Команда для запуску (використовуємо gunicorn для продакшну, або python для тестів)
# Для простоти використовуємо запуск через python, як у вашому app.py
CMD ["python", "run.py"]