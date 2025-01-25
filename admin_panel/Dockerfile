# Используем базовый образ Python
FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Устанавливаем переменные среды Django
ENV PYTHONUNBUFFERED 1

# Выполняем команду запуска
CMD ["sh", "-c", "python manage.py migrate && python manage.py start"]
