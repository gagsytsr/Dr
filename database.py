# database.py
import sqlite3

# --- Инициализация базы данных ---
# Эта функция создает базу данных и таблицы, если их еще нет.
def init_db():
    conn = sqlite3.connect('constructor.db') # Создаем или подключаемся к файлу constructor.db
    cursor = conn.cursor()

    # Создаем таблицу пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL
    )
    ''')

    # Создаем таблицу для хранения ботов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        username TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Создаем таблицу для команд (приветствие, автоответы)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_id INTEGER NOT NULL,
        keyword TEXT NOT NULL,
        response_text TEXT NOT NULL,
        FOREIGN KEY (bot_id) REFERENCES bots (id)
    )
    ''')
    conn.commit()
    conn.close()

# --- Функции для работы с данными ---
# Эти функции будут добавлять, получать и обновлять информацию.

# Добавить нового пользователя
def add_user(telegram_id):
    conn = sqlite3.connect('constructor.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (telegram_id,))
    conn.commit()
    conn.close()

# Добавить нового бота
def add_bot(telegram_id, bot_token, bot_username):
    conn = sqlite3.connect('constructor.db')
    cursor = conn.cursor()
    # Находим id пользователя по его telegram_id
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user_id = cursor.fetchone()[0]
    
    # Добавляем бота
    cursor.execute("INSERT INTO bots (user_id, token, username) VALUES (?, ?, ?)", (user_id, bot_token, bot_username))
    conn.commit()
    bot_id = cursor.lastrowid # Получаем id только что добавленного бота
    conn.close()
    return bot_id

# Установить команду для бота (например, /start)
def set_command(bot_id, keyword, response_text):
    conn = sqlite3.connect('constructor.db')
    cursor = conn.cursor()
    # Проверяем, есть ли уже такая команда, чтобы обновить ее, а не создавать дубликат
    cursor.execute("SELECT id FROM commands WHERE bot_id = ? AND keyword = ?", (bot_id, keyword))
    existing_command = cursor.fetchone()

    if existing_command:
        # Обновляем
        cursor.execute("UPDATE commands SET response_text = ? WHERE id = ?", (response_text, existing_command[0]))
    else:
        # Создаем новую
        cursor.execute("INSERT INTO commands (bot_id, keyword, response_text) VALUES (?, ?, ?)", (bot_id, keyword, response_text))
    
    conn.commit()
    conn.close()

