from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils.db_helpers import get_db_connection
from utils.logger import logger
from utils.subscription_checker import require_subscription


@require_subscription
async def start_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Получаем все категории
    cursor.execute("SELECT id, name FROM categories;")
    categories = cursor.fetchall()
    connection.close()

    # Проверяем, есть ли категории
    if not categories:
        # Если категории отсутствуют
        if update.message:  # Если вызвано через сообщение
            await update.message.reply_text("Каталог пуст. Пожалуйста, зайдите позже.")
        elif update.callback_query:  # Если вызвано через callback_query
            await update.callback_query.message.reply_text("Каталог пуст. Пожалуйста, зайдите позже.")
        return

    # Формируем кнопки для категорий
    keyboard = [
        [InlineKeyboardButton(category[1], callback_data=f"category_{category[0]}")]
        for category in categories
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с кнопками
    if update.message:  # Если вызвано через сообщение
        await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
    elif update.callback_query:  # Если вызвано через callback_query
        await update.callback_query.message.reply_text("Выберите категорию:", reply_markup=reply_markup)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    if data[0] == "category":
        category_id = int(data[1])
        page = int(data[2]) if len(data) > 2 else 1
        items_per_page = 5  # Количество кнопок на одной странице

        # Получаем подкатегории
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM subcategories WHERE category_id = %s;", (category_id,))
        subcategories = cursor.fetchall()
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
            [InlineKeyboardButton(subcategory[1], callback_data=f"subcategory_{subcategory[0]}")]
            for subcategory in current_page_items
        ]

        # Кнопки для навигации
        navigation_buttons = []
        if page > 1:
            navigation_buttons.append(InlineKeyboardButton("« Назад", callback_data=f"category_{category_id}_{page - 1}"))
        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton("Вперёд »", callback_data=f"category_{category_id}_{page + 1}"))
        if navigation_buttons:
            keyboard.append(navigation_buttons)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите подкатегорию:", reply_markup=reply_markup)

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

        for product in current_page_items:
            product_id, name, description, price, photo_url = product

            # Устанавливаем начальное количество товара
            context.user_data[f"product_{product_id}_quantity"] = context.user_data.get(
                f"product_{product_id}_quantity", 1)

            # Кнопки управления для каждого товара
            keyboard.append([
                InlineKeyboardButton("➖", callback_data=f"decrease_{product_id}"),
                InlineKeyboardButton(f"{context.user_data[f'product_{product_id}_quantity']}", callback_data=f"quantity_{product_id}"),
                InlineKeyboardButton("➕", callback_data=f"increase_{product_id}"),
            ])

            keyboard.append([
                InlineKeyboardButton("Добавить в корзину 🛒", callback_data=f"addtocart_{product_id}")
            ])

            # Отправляем фотографию и описание каждого товара
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
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
            navigation_buttons.append(InlineKeyboardButton("« Назад", callback_data=f"subcategory_{subcategory_id}_{page - 1}"))
        if page < total_pages:
            navigation_buttons.append(InlineKeyboardButton("Вперёд »", callback_data=f"subcategory_{subcategory_id}_{page + 1}"))
        if navigation_buttons:
            keyboard.append(navigation_buttons)

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем кнопки после всех фотографий
        await query.message.reply_text("Навигация:", reply_markup=reply_markup)

    elif data[0] == "increase":
        product_id = int(data[1])
        logger.warning("увеличено")
        # Увеличиваем количество
        context.user_data[f"product_{product_id}_quantity"] = context.user_data.get(f"product_{product_id}_quantity",
                                                                                    1) + 1
        quantity = context.user_data[f"product_{product_id}_quantity"]

        # Обновляем кнопки
        updated_keyboard = []
        for row in query.message.reply_markup.inline_keyboard:
            updated_row = []
            for button in row:
                if button.callback_data == f"quantity_{product_id}":
                    updated_row.append(InlineKeyboardButton(str(quantity), callback_data=button.callback_data))
                else:
                    updated_row.append(button)
            updated_keyboard.append(updated_row)

        reply_markup = InlineKeyboardMarkup(updated_keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    elif data[0] == "decrease":
        product_id = int(data[1])
        logger.warning("уменьшено")
        # Уменьшаем количество (не меньше 1)
        current_quantity = context.user_data.get(f"product_{product_id}_quantity", 1)
        if current_quantity > 1:
            context.user_data[f"product_{product_id}_quantity"] -= 1
            quantity = context.user_data[f"product_{product_id}_quantity"]

            # Обновляем кнопки
            updated_keyboard = []
            for row in query.message.reply_markup.inline_keyboard:
                updated_row = []
                for button in row:
                    if button.callback_data == f"quantity_{product_id}":
                        updated_row.append(InlineKeyboardButton(str(quantity), callback_data=button.callback_data))
                    else:
                        updated_row.append(button)
                updated_keyboard.append(updated_row)

            reply_markup = InlineKeyboardMarkup(updated_keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)




    elif data[0] == "addtocart":

        product_id = int(data[1])

        quantity = context.user_data.get(f"product_{product_id}_quantity", 1)

        user_id = update.effective_user.id  # Telegram ID пользователя

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

        # Отправляем всплывающее уведомление с галочкой
        await query.answer(f"Добавлено в корзину ✅", show_alert=True)
        # Проверяем, отличается ли текущая разметка

        current_reply_markup = query.message.reply_markup

        if current_reply_markup != query.message.reply_markup:
            await query.edit_message_reply_markup(reply_markup=current_reply_markup)



