import os
import logging
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import threading

# Initialize the bot
app = Client("my_bot", bot_token="YOUR_BOT_TOKEN")

# Set up logging
logging.basicConfig(level=logging.INFO)

def is_valid_url(url):
    return url.startswith('http://') or url.startswith('https://')

async def download_video(client, message):
    url = message.text.strip()
    
    if not is_valid_url(url):
        await message.reply_text("Invalid URL. Please send a valid video URL.")
        return
    
    progress_message = await message.reply_text("Downloading...", quote=True)
    
    def update_progress(progress):
        client.loop.create_task(
            client.edit_message_text(progress_message.chat.id, progress_message.message_id, 
                                     f"Downloading... {int(progress * 100)}%"))
    
    def download_and_send():
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'temp_video.%(ext)s',
                'progress_hooks': [lambda d: update_progress(d['downloaded_bytes'] / d['total_bytes'])],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
            client.loop.create_task(
                client.send_document(message.chat.id, 'temp_video.mp4'))
            os.remove('temp_video.mp4')
            client.loop.create_task(
                client.edit_message_text(progress_message.chat.id, progress_message.message_id, 
                                         f"Download complete: {info['title']}"))
        except yt_dlp.utils.DownloadError as e:
            client.loop.create_task(
                client.edit_message_text(progress_message.chat.id, progress_message.message_id, 
                                         f"Error: {str(e)}"))
        except Exception as e:
            client.loop.create_task(
                client.edit_message_text(progress_message.chat.id, progress_message.message_id, 
                                         f"An unexpected error occurred: {str(e)}"))

    threading.Thread(target=download_and_send).start()

@app.on_message(filters.command("start"))
async def start_message(client, message):
    await message.reply_text("Send a video link to start downloading.")

@app.on_message(filters.regex(r'http[s]?://'))
async def handle_link(client, message):
    url = message.text.strip()
    if not is_valid_url(url):
        await message.reply_text("Invalid URL. Please send a valid video URL.")
        return
    
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
    await download_video(client, callback_query.message)

if __name__ == "__main__":
    app.run()
