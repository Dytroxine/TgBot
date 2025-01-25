CREATE TABLE IF NOT EXISTS required_subscriptions (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(255) NOT NULL,
    channel_name VARCHAR(255)
);

-- Таблица категорий
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Таблица подкатегорий
CREATE TABLE IF NOT EXISTS subcategories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE
);

-- Таблица товаров
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    photo_url VARCHAR(255),
    subcategory_id INTEGER REFERENCES subcategories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES telegram_users(id) ON DELETE CASCADE,
    product_id INT NOT NULL,
    quantity INT DEFAULT 1,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, product_id)
);


CREATE TABLE telegram_users (
    id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS mailings (
    id SERIAL PRIMARY KEY,                      -- Уникальный идентификатор рассылки
    title VARCHAR(255) NOT NULL,                -- Название рассылки
    message TEXT NOT NULL,                      -- Текст сообщения рассылки
    created_at TIMESTAMP DEFAULT NOW(),         -- Время создания рассылки
    scheduled_at TIMESTAMP,                     -- Время запланированной рассылки
    is_sent BOOLEAN DEFAULT FALSE,               -- JSON-список пользователей для рассылки
    image VARCHAR(255),                  -- JSON-список URL изображений
    last_sent_at TIMESTAMP                      -- Время последней отправки рассылки
);
