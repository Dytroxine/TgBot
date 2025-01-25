import os
from utils.db_helpers import get_db_connection
from aiogram.types import Update
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from handlers.cart_handler import add_to_cart, view_cart, handle_cart_callback
from handlers.catalog_handler import start_catalog, handle_callback
from handlers.faq_handler import inline_faq
from handlers.start_handler import handle_start_callback
from handlers.mailing_handler import manual_mailing, send_mailing
from utils.logger import logger
from telegram.ext import InlineQueryHandler
from utils.subscription_checker import require_subscription
from handlers.cart_handler import handle_delivery_data



@require_subscription
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Получаем ID пользователя Telegram
    user_id = update.effective_user.id
    connection = None
    # Подключаемся к базе данных и заносим пользователя
    try:
        connection = get_db_connection()  # Получаем подключение к базе
        with connection.cursor() as cursor:
            # Вставляем ID пользователя в таблицу telegram_users, если его там ещё нет
            cursor.execute(
                """
                INSERT INTO telegram_users (id) 
                VALUES (%s) 
                ON CONFLICT (id) DO NOTHING;
                """,
                (user_id,)
            )
        connection.commit()
    except Exception as e:
        print(f"Ошибка при добавлении пользователя в базу данных: {e}")
    finally:
        if connection:
            connection.close()

    # Формируем клавиатуру с кнопками
    keyboard = [
        [
            InlineKeyboardButton("Перейти в каталог 🛒", callback_data="open_catalog"),
            InlineKeyboardButton("Задать вопрос ❓", callback_data="ask_question")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем приветственное сообщение с кнопками
    await update.message.reply_text(
        text="Привет! Добро пожаловать в наш магазин. Вы можете:\n"
             "1. Перейти в каталог товаров.\n"
             "2. Задать вопрос, если что-то непонятно.",
        reply_markup=reply_markup
    )

def main():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    if not application.job_queue:
        application.job_queue = application.create_job_queue()


    # Хендлеры для команд


    # Обработчик сообщений для доставки данных
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delivery_data))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("catalog", start_catalog))
    application.add_handler(CommandHandler("cart", view_cart))
    application.add_handler(CommandHandler("faq", inline_faq))
    application.add_handler(CommandHandler("send_mailing", manual_mailing))

    application.add_handler(InlineQueryHandler(inline_faq))

    # Хендлеры для обработки callback'ов
    application.add_handler(CallbackQueryHandler(handle_start_callback, pattern="^open_catalog|ask_question$"))
    application.add_handler(CallbackQueryHandler(add_to_cart, pattern="^product_"))
    application.add_handler(CallbackQueryHandler(handle_cart_callback, pattern="^cart_"))
    application.add_handler(CallbackQueryHandler(handle_callback))  # Для категорий

    application.job_queue.run_repeating(send_mailing, interval=40, first=10)

    application.run_polling()


if __name__ == '__main__':
    main()
