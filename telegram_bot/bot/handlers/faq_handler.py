from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler, ContextTypes
import uuid
from utils.subscription_checker import require_subscription


FAQ_DATA = [
    {"question": "Как оформить заказ?", "answer": "Вы можете оформить заказ через наш каталог."},
    {"question": "Какие способы оплаты вы принимаете?", "answer": "Мы принимаем карты, PayPal и другие способы оплаты."},
    {"question": "Как связаться с поддержкой?", "answer": "Вы можете написать нам через форму обратной связи."},
    {"question": "Как отследить мой заказ?", "answer": "После оформления заказа вы получите трекинг-номер."},
]


@require_subscription
async def inline_faq(update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка Inline-запросов для FAQ."""
    # Проверяем, есть ли Inline-запрос
    if not update.inline_query or not update.inline_query.query:
        return

    query = update.inline_query.query.lower().strip()

    # Если пользователь ничего не ввёл, не показываем ничего
    if not query:
        await update.inline_query.answer([], cache_time=10)
        return

    # Поиск подходящих вопросов по ключевым словам
    results = []
    for item in FAQ_DATA:
        if query in item["question"].lower():
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),  # Уникальный ID
                    title=item["question"],  # Вопрос
                    input_message_content=InputTextMessageContent(
                        f"**Вопрос:** {item['question']}\n**Ответ:** {item['answer']}",
                        parse_mode="Markdown"  # Форматирование текста
                    ),
                    description=item["answer"][:50]  # Краткое описание ответа
                )
            )

    # Если результаты найдены, отправляем их
    if results:
        await update.inline_query.answer(results, cache_time=10)
    else:
        # Если ничего не найдено, отправляем пустой список
        await update.inline_query.answer([], cache_time=10)

