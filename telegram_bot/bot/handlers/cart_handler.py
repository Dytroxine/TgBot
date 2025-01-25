from utils.logger import logger
import os
import hmac
import hashlib
import stripe
import requests
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils.db_helpers import get_db_connection
from utils.subscription_checker import require_subscription
import openpyxl
from openpyxl import Workbook

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
stripe.api_key = STRIPE_API_KEY


# Добавление товара в корзину
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logger.warning("Добавление в корзину: пользователь %s", update.effective_user.id)
    await query.answer("✅ Товар добавлен в корзину!")
    await query.edit_message_text("Товар добавлен в корзину!")

# Показ корзины
@require_subscription
async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(update.effective_user.id)
    logger.warning("Показ корзины для пользователя %s", user_id)
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT p.name, c.quantity, p.price, (p.price * c.quantity) AS total
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s;
    """, (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        logger.warning("Корзина пуста для пользователя %s", user_id)
        if update.message:
            await update.message.reply_text("Ваша корзина пуста.")
        elif update.callback_query:
            await update.callback_query.message.reply_text("Ваша корзина пуста.")
        connection.close()
        return

    cart_text = "**Ваша корзина:**\n\n"
    cart_keyboard = []

    for index, (name, quantity, price, total) in enumerate(cart_items):
        cart_text += (
            f"{index + 1}. **{name}**\n"
            f"Цена: {price} ₽\n"
            f"Количество: {quantity}\n"
            f"Итого: {total} ₽\n\n"
        )
        cart_keyboard.append([
            InlineKeyboardButton("➖", callback_data=f"cart_decrease_{index + 1}"),
            InlineKeyboardButton(f"{quantity}", callback_data=f"cart_quantity_{index + 1}"),
            InlineKeyboardButton("➕", callback_data=f"cart_increase_{index + 1}")
        ])

    total_sum = sum(item[3] for item in cart_items)
    context.user_data["cart_total"] = total_sum
    cart_keyboard.append([InlineKeyboardButton(f"Заказать ({total_sum} ₽)", callback_data="cart_order")])

    reply_markup = InlineKeyboardMarkup(cart_keyboard)

    logger.warning("Корзина пользователя %s: %s", user_id, cart_items)
    if update.message:
        await update.message.reply_text(cart_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(cart_text, parse_mode="Markdown", reply_markup=reply_markup)
    connection.close()


def write_to_excel(user_id, delivery_name, delivery_address, delivery_phone, total_sum):
    """Записывает данные о заказе в таблицу Excel."""
    file_name = "orders.xlsx"
    logger.warning("Запись в таблицу")
    try:
        # Открываем файл, если он существует
        workbook = openpyxl.load_workbook(file_name)
        sheet = workbook.active
    except FileNotFoundError:
        # Если файл не существует, создаём новый
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["User ID", "Имя", "Адрес доставки", "Телефон", "Сумма заказа"])  # Заголовки

    # Добавляем данные в последнюю строку
    sheet.append([user_id, delivery_name, delivery_address, delivery_phone, total_sum])

    # Сохраняем изменения
    workbook.save(file_name)
    workbook.close()


# Обработка данных для доставки
async def handle_delivery_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_delivery_data"):
        delivery_data = update.message.text.split("\n")
        if len(delivery_data) < 3:
            await update.message.reply_text(
                "Пожалуйста, введите все данные в формате:\n"
                "1. Ваше имя и фамилия\n"
                "2. Адрес доставки\n"
                "3. Ваш номер телефона"
            )
            return

        context.user_data["delivery_name"] = delivery_data[0]
        context.user_data["delivery_address"] = delivery_data[1]
        context.user_data["delivery_phone"] = delivery_data[2]
        context.user_data["awaiting_delivery_data"] = False
        total_sum = context.user_data.get("cart_total", 0)  # Получаем сумму корзины из контекста

        # Проверяем, есть ли данные для записи
        if total_sum == 0:
            await update.message.reply_text("Ошибка: Корзина пуста или сумма заказа неизвестна.")
            return

        write_to_excel(update.effective_user.id, delivery_data[0], delivery_data[1], delivery_data[2], total_sum)

        await update.message.reply_text("Спасибо! Теперь вы будете перенаправлены на платёж.")
        await initiate_payment(update, context)

def create_stripe_invoice(amount, currency="rub", description="Оплата заказа через Telegram-бот"):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": description},
                    "unit_amount": int(amount * 100),  # Сумма в центах
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        return session.url
    except Exception as e:
        logger.error(f"Ошибка создания платежа через Stripe: {e}")
        raise


# Инициация платежа
async def initiate_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        # Извлекаем данные корзины из базы данных
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
                    SELECT p.name, c.quantity, p.price, (p.price * c.quantity) AS total
                    FROM cart c
                    JOIN products p ON c.product_id = p.id
                    WHERE c.user_id = %s;
                """, (user_id,))
        cart_items = cursor.fetchall()
        connection.close()

        if not cart_items:
            await update.message.reply_text("Ваша корзина пуста. Невозможно создать платёж.")
            return
        total_sum = sum(item[3] for item in cart_items)
        currency = "rub"

        # Создание инвойса
        payment_url = create_stripe_invoice(amount=total_sum, currency=currency)

        # Отправка пользователю
        keyboard = [[InlineKeyboardButton("Оплатить", url=payment_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Нажмите на кнопку ниже, чтобы перейти к оплате:",
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


# Обработка callback'ов корзины
async def handle_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(update.effective_user.id)
    logger.warning("Обработка callback'а: пользователь %s, данные %s", user_id, query.data)
    connection = get_db_connection()
    cursor = connection.cursor()

    # Разбиваем callback_data
    data = query.data.split("_")

    # Проверяем, что action и product_index существуют
    if len(data) == 2 and data[1] == "order":
        # Обработка кнопки "Заказать"
        await query.message.reply_text(
            "Пожалуйста, введите данные для доставки:\n\n"
            "1. Ваше имя и фамилия\n"
            "2. Адрес доставки\n"
            "3. Ваш номер телефона"
        )
        context.user_data["awaiting_delivery_data"] = True
        connection.close()
        return
    elif len(data) < 3:
        logger.error("Некорректные данные callback_data: %s", query.data)
        await query.message.reply_text("Произошла ошибка. Попробуйте ещё раз.")
        connection.close()
        return

    action = data[1]
    product_index = int(data[2])

    cursor.execute("""
        SELECT p.id, c.quantity FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
        LIMIT 1 OFFSET %s;
    """, (user_id, product_index - 1))
    product_row = cursor.fetchone()

    if not product_row:
        logger.error("Продукт не найден для пользователя %s на позиции %s", user_id, product_index)
        await query.edit_message_text("Ошибка: Продукт не найден.")
        connection.close()
        return

    product_id, current_quantity = product_row

    if action == "increase":
        cursor.execute("""
            UPDATE cart
            SET quantity = quantity + 1, updated_at = NOW()
            WHERE user_id = %s AND product_id = %s;
        """, (user_id, product_id))
        logger.warning("Увеличено количество товара %s для пользователя %s", product_id, user_id)

    elif action == "decrease":
        if current_quantity > 1:
            cursor.execute("""
                UPDATE cart
                SET quantity = quantity - 1, updated_at = NOW()
                WHERE user_id = %s AND product_id = %s;
            """, (user_id, product_id))
            logger.warning("Уменьшено количество товара %s для пользователя %s", product_id, user_id)
        else:
            cursor.execute("""
                DELETE FROM cart 
                WHERE user_id = %s AND product_id = %s;
            """, (user_id, product_id))
            logger.warning("Удалён товар %s для пользователя %s", product_id, user_id)

    connection.commit()
    connection.close()

    await view_cart(update, context)
