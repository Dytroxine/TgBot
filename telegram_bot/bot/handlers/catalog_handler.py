import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from utils.db_helpers import get_db_connection
from utils.logger import logger
from utils.subscription_checker import require_subscription


@require_subscription
async def start_catalog(callback_query: CallbackQuery):
    """Обработчик для старта каталога."""
    connection = get_db_connection()
    cursor = connection.cursor()

    # Получаем категории из базы данных
    cursor.execute("SELECT id, name FROM categories;")
    categories = cursor.fetchall()
    connection.close()

    if not categories:
        await callback_query.message.answer("Каталог пуст. Пожалуйста, зайдите позже.")
        return

    # Формируем клавиатуру с кнопками категорий
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=category[1], callback_data=f"category_{category[0]}")]
            for category in categories
        ]
    )

    # Отправляем сообщение с категориями
    await callback_query.answer("Выберите категорию:", reply_markup=keyboard)





async def handle_callback(callback: CallbackQuery):
    global user_data
    if 'user_data' not in globals():
        user_data = {}
    await callback.answer()
    data = callback.data.split("_")
    product_id = int(data[1])
    if f"product_{product_id}_quantity" not in user_data:
        user_data[f"product_{product_id}_quantity"] = 1

    if data[0] == "category":
        category_id = int(data[1])
        page = int(data[2]) if len(data) > 2 else 1
        items_per_page = 5  # Количество кнопок на одной странице

        # Получаем подкатегории
        connection = get_db_connection()  # Обычный вызов функции
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM subcategories WHERE category_id = %s;", (category_id,))
        subcategories = cursor.fetchall()
        cursor.close()
        connection.close()

        if not subcategories:
            await query.edit_message_text("В этой категории пока нет подкатегорий.")
            return

        # Пагинация подкатегорий
        total_items = len(subcategories)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        current_page_items = subcategories[start_index:end_index]

        # Формируем кнопки для текущей страницы
        keyboard = [
            [InlineKeyboardButton(text=subcategory[1], callback_data=f"subcategory_{subcategory[0]}")]
            for subcategory in current_page_items
        ]

        # Добавляем кнопки для навигации
        if page > 1:
            keyboard.append([InlineKeyboardButton(text="« Назад", callback_data=f"category_{category_id}_{page - 1}")])
        if page < total_pages:
            keyboard.append([InlineKeyboardButton(text="Вперёд »", callback_data=f"category_{category_id}_{page + 1}")])

        # Создаем объект InlineKeyboardMarkup
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        # Обновляем сообщение
        await callback.message.edit_text(f"Страница {page} из {total_pages}:", reply_markup=reply_markup)

    if data[0] == "subcategory":
        subcategory_id = int(data[1])
        page = int(data[2]) if len(data) > 2 else 1
        items_per_page = 3  # Количество товаров на одной странице

        # Получаем товары для подкатегории
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, description, price, photo_url FROM products WHERE subcategory_id = %s;",
                       (subcategory_id,))
        products = cursor.fetchall()
        connection.close()

        if not products:
            await query.edit_message_text("В этой подкатегории пока нет товаров.")
            return

        # Пагинация товаров
        total_items = len(products)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        current_page_items = products[start_index:end_index]

        # Формируем сообщения с товарами и кнопками
        keyboard = []
        user_data = {}
        for product in current_page_items:
            product_id, name, description, price, photo_url = product
            user_data[f"product_{product_id}_quantity"] = user_data.get(f"product_{product_id}_quantity", 1)

            # Кнопки управления для каждого товара
            keyboard.append([
                InlineKeyboardButton(text="➖", callback_data=f"decrease_{product_id}"),
                InlineKeyboardButton(text=f"{user_data[f'product_{product_id}_quantity']}",
                                     callback_data=f"quantity_{product_id}"),
                InlineKeyboardButton(text="➕", callback_data=f"increase_{product_id}"),
            ])

            keyboard.append([
                InlineKeyboardButton(text="Добавить в корзину 🛒", callback_data=f"addtocart_{product_id}")
            ])

            # Отправляем фотографию и описание каждого товара
            await callback.message.answer_photo(
                photo=photo_url,
                caption=(
                    f"**{name}**\n"
                    f"{description}\n"
                    f"💰 Цена: {price} ₽\n"
                ),
                parse_mode="Markdown"
            )

        # Навигация по страницам
        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(
                InlineKeyboardButton(text="« Назад", callback_data=f"subcategory_{subcategory_id}_{page - 1}"))
        if page < total_pages:
            navigation_buttons.append(
                InlineKeyboardButton(text="Вперёд »", callback_data=f"subcategory_{subcategory_id}_{page + 1}"))
        if navigation_buttons:
            keyboard.append(navigation_buttons)

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        # Отправляем кнопки после всех фотографий
        await callback.message.answer(text="Навигация:", reply_markup=reply_markup)
    # Увеличение количества товара
    elif data[0] == "increase":
        product_id = int(data[1])
        if f"product_{product_id}_quantity" not in user_data:
            user_data[f"product_{product_id}_quantity"] = 1  # Инициализация, если ключа нет
        user_data[f"product_{product_id}_quantity"] += 1
        quantity = user_data[f"product_{product_id}_quantity"]

        # Обновляем кнопки
        updated_keyboard = []
        for row in callback.message.reply_markup.inline_keyboard:
            updated_row = []
            for button in row:
                if button.callback_data == f"quantity_{product_id}":
                    updated_row.append(InlineKeyboardButton(text=str(quantity), callback_data=button.callback_data))
                else:
                    updated_row.append(button)
            updated_keyboard.append(updated_row)

        reply_markup = InlineKeyboardMarkup(inline_keyboard=updated_keyboard)
        await callback.message.edit_reply_markup(reply_markup=reply_markup)

    # Уменьшение количества товара
    elif data[0] == "decrease":
        product_id = int(data[1])
        current_quantity = user_data.get(f"product_{product_id}_quantity", 1)
        if current_quantity > 1:
            user_data[f"product_{product_id}_quantity"] = current_quantity - 1
            quantity = user_data[f"product_{product_id}_quantity"]

            # Обновляем кнопки
            updated_keyboard = []
            for row in callback.message.reply_markup.inline_keyboard:
                updated_row = []
                for button in row:
                    if button.callback_data == f"quantity_{product_id}":
                        updated_row.append(InlineKeyboardButton(text=str(quantity), callback_data=button.callback_data))
                    else:
                        updated_row.append(button)
                updated_keyboard.append(updated_row)

            reply_markup = InlineKeyboardMarkup(inline_keyboard=updated_keyboard)
            await callback.message.edit_reply_markup(reply_markup=reply_markup)

    # Добавление в корзину
    elif data[0] == "addtocart":
        product_id = int(data[1])
        quantity = user_data.get(f"product_{product_id}_quantity", 1)
        user_id = callback.from_user.id  # Telegram ID пользователя

        # Подключение к базе данных
        connection = get_db_connection()
        cursor = connection.cursor()

        # Запрос для добавления или обновления корзины
        cursor.execute(
            """
            INSERT INTO cart (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, product_id) DO UPDATE
            SET quantity = cart.quantity + EXCLUDED.quantity, updated_at = NOW();
            """,
            (user_id, product_id, quantity)
        )

        connection.commit()
        connection.close()

        # Отправляем всплывающее уведомление
        await callback.answer(f"Добавлено в корзину ✅", show_alert=True)