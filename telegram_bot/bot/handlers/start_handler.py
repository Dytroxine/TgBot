from telegram import Update
from telegram.ext import ContextTypes
from handlers.catalog_handler import start_catalog


async def handle_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Обрабатываем callback_data
    if query.data == "open_catalog":
        # Переход в каталог
        await start_catalog(update, context)
    elif query.data == "ask_question":
        # Отправляем сообщение с инструкциями для вопроса
        await query.edit_message_text(
            text="Вы можете задать вопрос, отправив сообщение сюда, или воспользоваться нашим Inline-режимом, "
                 "введя `@ник вашего бота` в строке ввода!"
        )
