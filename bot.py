import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import requests
import threading
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DUMP_CHAT_ID = os.getenv("DUMP_CHAT_ID")

# Initialize the bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Set up logging
logging.basicConfig(level=logging.INFO)

def download_file(url, quality, progress_callback):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024)

    with open(f"temp_{quality}.mp4", 'wb') as file:
        for data in response.iter_content(chunk_size=8192):
            file.write(data)
            progress_bar.update(len(data))
            progress_callback(progress_bar.n / total_size)

    progress_bar.close()

@app.on_message(filters.command("start"))
def start_message(client, message):
    client.send_message(message.chat.id, "Send a video link to start downloading.")

@app.on_message(filters.regex(r'http[s]?://'))
def handle_link(client, message):
    url = message.text
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("360p", callback_data=f"quality_360_{url}"),
         InlineKeyboardButton("720p", callback_data=f"quality_720_{url}"),
         InlineKeyboardButton("1080p", callback_data=f"quality_1080_{url}")]
    ])
    message.reply_text("Choose the video quality:", reply_markup=markup)

@app.on_callback_query()
def handle_query(client, callback_query):
    data = callback_query.data
    quality, url = data.split("_")[1], "_".join(data.split("_")[2:])
    progress_message = callback_query.message.reply_text("Downloading...", quote=True)

    def download_and_send():
        def update_progress(progress):
            client.edit_message_text(progress_message.chat.id, progress_message.message_id, f"Downloading... {int(progress * 100)}%")

        download_file(url, quality, update_progress)
        client.send_document(callback_query.message.chat.id, f"temp_{quality}.mp4")
        os.remove(f"temp_{quality}.mp4")

    threading.Thread(target=download_and_send).start()

if __name__ == "__main__":
    app.run()
