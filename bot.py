import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import BusinessMessagesDeleted, Message

# Твои данные уже вставлены:
BOT_TOKEN = "8990389861:AAHsYC5uAUNYuxU-BQZL5mfLy1DESTcDo2Y"
MY_USER_ID = 8821016133

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
memory_db = {}


# Запоминаем новые сообщения
@dp.business_message(F.text | F.caption)
async def track_incoming(message: Message):
    text = message.text or message.caption
    sender_name = message.from_user.full_name if message.from_user else "Собеседник"
    chat_name = message.chat.full_name or "Личный чат"

    memory_db[(message.chat.id, message.message_id)] = {
        "text": text,
        "sender": sender_name,
        "chat": chat_name,
    }


# Изменённые сообщения
@dp.edited_business_message(F.text | F.caption)
async def track_edits(message: Message):
    key = (message.chat.id, message.message_id)
    saved = memory_db.get(key)

    old_text = saved["text"] if saved else "[Не было в памяти]"
    new_text = message.text or message.caption
    sender = message.from_user.full_name if message.from_user else "Собеседник"

    alert_text = (
        f"✏️ <b>ИЗМЕНЕНО СООБЩЕНИЕ</b>\n"
        f"👤 <b>От:</b> {sender}\n"
        f"💬 <b>Чат:</b> {message.chat.full_name}\n\n"
        f"❌ <b>Было:</b>\n{old_text}\n\n"
        f"✅ <b>Стало:</b>\n{new_text}"
    )

    if key in memory_db:
        memory_db[key]["text"] = new_text

    await bot.send_message(chat_id=MY_USER_ID, text=alert_text, parse_mode="HTML")


# Удалённые сообщения
@dp.deleted_business_messages()
async def track_deletions(event: BusinessMessagesDeleted):
    for msg_id in event.message_ids:
        key = (event.chat.id, msg_id)
        saved = memory_db.get(key)

        if saved:
            alert_text = (
                f"🗑 <b>УДАЛЕНО СООБЩЕНИЕ</b>\n"
                f"👤 <b>От:</b> {saved['sender']}\n"
                f"💬 <b>Чат:</b> {saved['chat']}\n\n"
                f"📄 <b>Текст:</b>\n{saved['text']}"
            )
            await bot.send_message(
                chat_id=MY_USER_ID, text=alert_text, parse_mode="HTML"
            )
            del memory_db[key]


# Веб-сервер для поддержания работы на Render
async def handle_ping(request):
    return web.Response(text="Bot is online and working!")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    await start_web_server()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
