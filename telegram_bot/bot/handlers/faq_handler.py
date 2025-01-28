import uuid
from aiogram import types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from utils.subscription_checker import require_subscription

FAQ_DATA = [
    {"question": "Как оформить заказ?", "answer": "Вы можете оформить заказ через наш каталог."},
    {"question": "Какие способы оплаты вы принимаете?", "answer": "Мы принимаем карты, PayPal и другие способы оплаты."},
    {"question": "Как связаться с поддержкой?", "answer": "Вы можете написать нам через форму обратной связи."},
    {"question": "Как отследить мой заказ?", "answer": "После оформления заказа вы получите трекинг-номер."},
]

# Обработка Inline-запросов для FAQ
@require_subscription
async def inline_faq(inline_query: types.InlineQuery):
    search_query = inline_query.query.lower().strip()

    results = []
    for item in FAQ_DATA:
        if search_query in item["question"].lower():
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=item["question"],
                    input_message_content=InputTextMessageContent(
                        message_text=f"**Вопрос:** {item['question']}\n**Ответ:** {item['answer']}",
                        parse_mode="Markdown"
                    ),
                    description=item["answer"][:50]
                )
            )

    await inline_query.answer(
        results=results,
        cache_time=10,
        is_personal=True
    )
