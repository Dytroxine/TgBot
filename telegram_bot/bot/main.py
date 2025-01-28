import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from utils.db_helpers import get_db_connection
from handlers.cart_handler import add_to_cart, view_cart, handle_cart_callback, handle_delivery_data, initiate_payment, process_user_input
from handlers.catalog_handler import start_catalog, handle_callback
from handlers.start_handler import handle_start_callback
from handlers.faq_handler import inline_faq
from handlers.mailing_handler import schedule_mailing
from utils.logger import logger
from aiogram.types import Message
from utils.subscription_checker import require_subscription

# Инициализация бота и диспетчера
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Обработчик команды /start
@require_subscription
async def start_command(message: Message):
    """Обработчик команды /start."""
    user_id = message.from_user.id

    # Подключаемся к базе данных
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Проверяем, существует ли пользователь в таблице
        cursor.execute("SELECT id FROM telegram_users WHERE id = %s", (user_id,))
        user_exists = cursor.fetchone()

        # Если пользователя нет, добавляем его
        if not user_exists:
            cursor.execute("INSERT INTO telegram_users (id) VALUES (%s)", (user_id,))
            connection.commit()  # Фиксируем изменения в базе

    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")

    finally:
        # Закрываем соединение
        cursor.close()
        connection.close()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Перейти в каталог 🛒", callback_data="open_catalog"),
            InlineKeyboardButton(text="Задать вопрос ❓", callback_data="ask_question")
        ]
    ])
    await message.answer(
        text=(
            "Привет! Добро пожаловать в наш магазин. Вы можете:\n"
            "1. Перейти в каталог товаров.\n"
            "2. Задать вопрос, если что-то непонятно."
        ),
        reply_markup=keyboard
    )


# Основная функция для запуска бота
async def main():
    schedule_mailing(bot)
    # Регистрация обработчиков
    dp.message.register(start_command, Command("start"))
    dp.message.register(start_catalog, Command("catalog"))
    dp.message.register(view_cart, Command("cart"))
    dp.message.register(inline_faq, Command("faq"))
    dp.message.register(process_user_input)
    dp.inline_query.register(inline_faq)

    dp.callback_query.register(handle_start_callback, lambda callback: callback.data in ["open_catalog", "ask_question"])
    dp.callback_query.register(add_to_cart, lambda callback: callback.data.startswith("product_"))
    dp.callback_query.register(handle_delivery_data, lambda callback: callback.data.startswith("start_delivery"))
    dp.callback_query.register(handle_cart_callback, lambda callback: callback.data.startswith("cart_"))
    dp.callback_query.register(handle_callback)

    # Запуск бота
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    asyncio.run(main())
