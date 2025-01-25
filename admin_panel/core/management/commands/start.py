from multiprocessing import Process, set_start_method
from django.core.management import BaseCommand
import os
import sys

# Устанавливаем метод запуска процессов
set_start_method("spawn", force=True)


def run_django():
    os.system("python manage.py runserver")

def run_bot():
    print("Запускается Telegram-бот...")
    os.system(f"python {os.path.abspath('../telegram_bot/bot/main.py')}")

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Создаем процессы
        django_process = Process(target=run_django)
        bot_process = Process(target=run_bot)

        # Запускаем процессы
        django_process.start()
        bot_process.start()

        # Ожидаем завершения процессов
        django_process.join()
        bot_process.join()
