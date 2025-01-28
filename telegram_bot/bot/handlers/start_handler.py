from aiogram import types
from aiogram.types import CallbackQuery
from handlers.catalog_handler import start_catalog
from utils.subscription_checker import require_subscription


@require_subscription
async def handle_start_callback(callback: CallbackQuery):
    """Обработчик для нажатий на кнопки из /start."""
    await callback.answer()

    # Обрабатываем callback_data
    if callback.data == "open_catalog":
        # Переход в каталог
        await start_catalog(callback.message)
    elif callback.data == "ask_question":
        # Отправляем сообщение с инструкциями для вопроса
        await callback.message.edit_text(
            text=(
                "Вы можете задать вопрос, отправив сообщение сюда, или воспользоваться нашим Inline-режимом, "
                "введя `@ник вашего бота` в строке ввода!"
            )
        )
