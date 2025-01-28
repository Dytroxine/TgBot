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

# Запуск приложения с миграциями и созданием суперпользователя
CMD ["sh", "-c", "python admin_panel/manage.py migrate && \
                   echo \"from django.contrib.auth.models import User; \
                   User.objects.create_superuser(username='${DJANGO_SUPERUSER_USERNAME}', email='${DJANGO_SUPERUSER_EMAIL}', password='${DJANGO_SUPERUSER_PASSWORD}') if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME}').exists() else print('Superuser exists.')\" | python admin_panel/manage.py shell && \
                   python admin_panel/manage.py start"]
