# main.py
import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message

import database as db
import handlers # Импортируем наши обработчики

# --- Глобальные переменные ---
# Словарь для хранения запущенных ботов-воркеров и их диспетчеров
# Формат: { "токен_бота": {"bot": объект_Bot, "dp": объект_Dispatcher} }
worker_bots = {}

# --- Логика для ботов-воркеров ---
# Эта функция будет обрабатывать сообщения для всех ДОБАВЛЕННЫХ ботов
async def handle_worker_message(message: Message, bot: Bot):
    # Находим нашего бота в БД по токену
    conn = db.sqlite3.connect('constructor.db')
    cursor = conn.cursor()
    
    # Получаем ID бота из таблицы bots по его токену
    cursor.execute("SELECT id FROM bots WHERE token = ?", (bot.token,))
    bot_db_id_tuple = cursor.fetchone()
    if not bot_db_id_tuple:
        conn.close()
        return

    bot_db_id = bot_db_id_tuple[0]
    
    # Ищем ответ на команду (текст сообщения) в нашей БД
    user_message_text = message.text
    cursor.execute("SELECT response_text FROM commands WHERE bot_id = ? AND keyword = ?", (bot_db_id, user_message_text))
    response = cursor.fetchone()
    conn.close()

    if response:
        # Если нашли команду, отправляем ответ
        await message.answer(response[0])
    else:
        # Можно добавить ответ по умолчанию, если команда не найдена
        # await message.answer("Команда не распознана.")
        pass

# --- Функции для запуска и управления ---
async def start_worker_bot(token: str):
    """Запускает и регистрирует нового бота-воркера."""
    if token in worker_bots:
        return # Бот уже запущен

    try:
        bot = Bot(token=token)
        dp = Dispatcher()
        
        # Регистрируем наш универсальный обработчик для всех сообщений
        dp.message.register(handle_worker_message)
        
        worker_bots[token] = {"bot": bot, "dp": dp}
        
        # Запускаем бота в фоновом режиме
        asyncio.create_task(dp.start_polling(bot))
        print(f"Воркер для бота с токеном {token[:10]}... запущен.")
    except Exception as e:
        print(f"Не удалось запустить воркера с токеном {token[:10]}...: {e}")

async def load_and_start_all_workers():
    """Загружает всех ботов из БД и запускает их."""
    conn = db.sqlite3.connect('constructor.db')
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM bots")
    all_tokens = cursor.fetchall()
    conn.close()
    
    for token_tuple in all_tokens:
        await start_worker_bot(token_tuple[0])

async def main():
    # Инициализируем базу данных при старте
    db.init_db()

    # --- Запускаем главного бота (конструктор) ---
    # Токен берем из переменных окружения (безопасный способ)
    # На Railway ты добавишь его в настройках проекта.
    CONSTRUCTOR_BOT_TOKEN = os.getenv("CONSTRUCTOR_BOT_TOKEN")
    
    if not CONSTRUCTOR_BOT_TOKEN:
        print("Ошибка: не найден CONSTRUCTOR_BOT_TOKEN. Укажи его в переменных окружения.")
        return

    main_bot = Bot(token=CONSTRUCTOR_BOT_TOKEN)
    main_dp = Dispatcher()
    
    # Подключаем роутер с нашими командами (/start, /newbot)
    main_dp.include_router(handlers.router)
    
    # --- Запускаем ботов-воркеров ---
    await load_and_start_all_workers()

    print("Основной бот-конструктор запущен...")
    # Запускаем основного бота
    await main_dp.start_polling(main_bot)


if __name__ == "__main__":
    asyncio.run(main())

