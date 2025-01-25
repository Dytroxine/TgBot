-- Настройка доступа для всех хостов
ALTER SYSTEM SET listen_addresses = '*';
SELECT pg_reload_conf();


-- Таблица пользователей Telegram
CREATE TABLE IF NOT EXISTS telegram_users (
    id BIGINT PRIMARY KEY
);

-- Таблица обязательных подписок
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

-- Таблица корзины
CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES telegram_users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, product_id)
);

-- Таблица рассылок
CREATE TABLE IF NOT EXISTS mailings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    scheduled_at TIMESTAMP,
    is_sent BOOLEAN DEFAULT FALSE,
    image VARCHAR(255),
    last_sent_at TIMESTAMP
);
