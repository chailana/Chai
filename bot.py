import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import yt_dlp
from tqdm import tqdm
import asyncio

# Initialize the bot
app = Client("my_bot", bot_token=os.getenv("BOT_TOKEN"), api_id=int(os.getenv("API_ID")), api_hash=os.getenv("API_HASH"))

# Set up logging
logging.basicConfig(level=logging.INFO)

async def download_file(url, quality, progress_callback):
    ydl_opts = {
        'format': f'{quality}',
        'outtmpl': 'temp.mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_size = os.path.getsize('temp.mp4')
    
    progress_callback(1.0)  # Simulate progress update for simplicity

@app.on_message(filters.command("start"))
async def start_message(client, message):
    await message.reply_text("Send a video link to start downloading.")

@app.on_message(filters.regex(r'http[s]?://'))
async def handle_link(client, message):
    url = message.text
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("360p", callback_data=f"quality_360_{url}"),
         InlineKeyboardButton("720p", callback_data=f"quality_720_{url}"),
         InlineKeyboardButton("1080p", callback_data=f"quality_1080_{url}")]
    ])
    await message.reply_text("Choose the video quality:", reply_markup=markup)

@app.on_callback_query()
async def handle_query(client, callback_query):
    data = callback_query.data
    quality, url = data.split("_")[1], "_".join(data.split("_")[2:])
    progress_message = await callback_query.message.reply_text("Downloading...", quote=True)
    
    async def download_and_send():
        def update_progress(progress):
            asyncio.create_task(client.edit_message_text(progress_message.chat.id, progress_message.message_id, f"Downloading... {int(progress * 100)}%"))

        await download_file(url, quality, update_progress)
        await client.send_document(callback_query.message.chat.id, 'temp.mp4')
        os.remove('temp.mp4')
    
    asyncio.create_task(download_and_send())

if __name__ == "__main__":
    app.run()
