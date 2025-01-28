from multiprocessing import Process, set_start_method
from django.core.management import BaseCommand
import os
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent   # Путь до директории admin_panel
main_py_path = base_dir / "telegram_bot" / "bot" / "main.py"
manage_py_path = base_dir / "admin_panel" / "manage.py"


def run_django():
    os.system(f"python {manage_py_path} runserver 0.0.0.0:8000")

def run_bot():
    print("Запускается Telegram-бот...")
    os.system(f"python {main_py_path}")

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
