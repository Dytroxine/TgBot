from aiogram import Bot, Dispatcher, types
from aiogram.types import CallbackQuery
from functools import wraps
from utils.db_helpers import get_db_connection
from utils.logger import logger


async def check_subscription(callback_query: CallbackQuery, bot: Bot) -> bool:
    """Проверка подписки пользователя на каналы."""
    user_id = callback_query.from_user.id
    logger.warning(f"Проверка подписки для пользователя: {user_id}")

    # Подключаемся к базе данных
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT channel_id, channel_name FROM required_subscriptions;")
    channels = cursor.fetchall()
    connection.close()

    if not channels:
        logger.warning("Нет каналов для проверки в таблице required_subscriptions")
        return True  # Если нет каналов, позволяем выполнять команды

    unsubscribed_channels = []

    for channel_id, channel_name in channels:
        try:
            # Проверяем статус пользователя в канале
            logger.warning(f"Проверка канала: {channel_id} ({channel_name})")
            member_status = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            logger.warning(f"Статус пользователя: {member_status.status}")
            if member_status.status not in ["member", "administrator", "creator"]:
                unsubscribed_channels.append(channel_name or channel_id)
        except Exception as e:
            logger.warning(f"Ошибка при проверке канала {channel_id}: {e}")
            unsubscribed_channels.append(channel_name or channel_id)

    # Если есть каналы, на которые пользователь не подписан
    if unsubscribed_channels:
        channel_list = "\n".join(f"- {channel}" for channel in unsubscribed_channels)
        await callback_query.answer(
            f"Вы должны подписаться на следующие каналы, чтобы использовать бота:\n{channel_list}"
        )
        return False

    logger.warning(f"Пользователь {user_id} подписан на все каналы.")
    return True

def require_subscription(handler):
    """Декоратор для проверки подписки перед выполнением команды."""
    @wraps(handler)
    async def wrapper(callback_query: CallbackQuery, *args, **kwargs):
        logger.warning(f"Вызов require_subscription для команды: {handler.__name__}")
        if await check_subscription(callback_query, callback_query.bot):
            await handler(callback_query, *args, **kwargs)
        else:
            logger.warning(f"Пользователь {callback_query.from_user.id} не прошёл проверку подписки.")
    return wrapper
