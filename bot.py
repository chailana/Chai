import os
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL

# Initialize bot
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("url_uploader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start command
@bot.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply_text("Hello! Send me a video URL to download.")

# Video download from URL
@bot.on_message(filters.text & ~filters.edited)
async def download_video(_, message: Message):
    url = message.text
    await message.reply_text(f"Downloading video from: {url}")

    # Download video using yt-dlp
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        # Send video to the user
        await message.reply_video(file_name)
        os.remove(file_name)  # Remove file after sending

    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

# Run the bot
bot.run()
