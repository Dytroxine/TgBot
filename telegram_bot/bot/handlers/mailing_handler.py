from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.db_helpers import get_db_connection
from utils.logger import logger


async def send_mailing(bot: Bot):
    """Периодическая задача для автоматической отправки рассылок."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Получаем все запланированные рассылки
        cursor.execute(
            """
            SELECT id, message, image
            FROM mailings
            WHERE is_sent = FALSE AND scheduled_at <= NOW();
            """
        )
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
                        await bot.send_photo(
                            chat_id=user_id,
                            photo=image,
                            caption=message,
                            parse_mode="Markdown"
                        )
                    else:
                        await bot.send_message(chat_id=user_id, text=message)
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

            # Помечаем рассылку как отправленную
            cursor.execute(
                """
                UPDATE mailings
                SET is_sent = TRUE, last_sent_at = NOW()
                WHERE id = %s;
                """,
                (mailing_id,)
            )
            connection.commit()
    except Exception as e:
        logger.error(f"Ошибка в процессе рассылки: {e}")
    finally:
        connection.close()


def schedule_mailing(bot: Bot):
    """Настраивает планировщик задач для автоматической рассылки."""
    scheduler = AsyncIOScheduler()

    # Настраиваем задачу на выполнение каждую минуту (или укажите свои интервалы)
    scheduler.add_job(
        send_mailing,
        CronTrigger(minute="*/1"),  # Каждую минуту
        args=(bot,),  # Передаем объект бота
        id="mailing_job",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Планировщик рассылок запущен.")
