# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Открываем порт для Django
EXPOSE 8000

# Запуск приложения
CMD ["sh", "-c", "python admin_panel/manage.py migrate && python admin_panel/manage.py start"]

