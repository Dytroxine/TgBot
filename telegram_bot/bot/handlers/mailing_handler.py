from telegram.ext import ContextTypes
from utils.db_helpers import get_db_connection
from utils.subscription_checker import require_subscription
from utils.logger import logger


async def send_mailing(context: ContextTypes.DEFAULT_TYPE):
    """Периодическая задача для автоматической отправки рассылок."""
    connection = get_db_connection()
    cursor = connection.cursor()

    # Получаем все запланированные рассылки
    cursor.execute("""
        SELECT id, message, image
        FROM mailings
        WHERE is_sent = FALSE AND scheduled_at <= NOW();
    """)
    mailings = cursor.fetchall()

    # Получаем всех пользователей из таблицы telegram_users
    cursor.execute("SELECT id FROM telegram_users;")
    users = cursor.fetchall()
    user_ids = [user[0] for user in users]

    for mailing in mailings:
        mailing_id, message, image = mailing

        for user_id in user_ids:
            try:
                # Проверяем, есть ли изображение
                if image:
                    # Отправляем изображение с текстом в подписи
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=image,  # Ссылка на изображение
                        caption=message,  # Текст сообщения добавляется в подпись
                        parse_mode="Markdown"
                    )
                else:
                    # Если изображения нет, отправляем только текст
                    await context.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logger.error(f"Ошибка при отправке: {e}")

        # Помечаем рассылку как отправленную
        cursor.execute("""
            UPDATE mailings
            SET is_sent = TRUE, last_sent_at = NOW()
            WHERE id = %s;
        """, (mailing_id,))
        connection.commit()

    connection.close()


@require_subscription
async def manual_mailing(update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для ручного запуска рассылки."""
    await send_mailing(context)
    await update.message.reply_text("Рассылка выполнена.")
