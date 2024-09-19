import os
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL
from pyrogram.errors import FloodWait
import requests

# Initialize bot
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DUMP_CHAT_ID = os.getenv("DUMP_CHAT_ID")  # ID of the chat where you want to dump logs

bot = Client("url_uploader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Command handlers
@bot.on_message(filters.command("start"))
async def start(_, message: Message):
    start_msg = (
        "Hello! I'm your video downloader bot. Here are some commands you can use:\n"
        "/start - Start the bot\n"
        "/help - Get help on how to use the bot\n"
        "/quality - List available quality options for downloading videos\n"
    )
    await message.reply_text(start_msg)

@bot.on_message(filters.command("help"))
async def help(_, message: Message):
    help_msg = (
        "To use this bot, send me a video URL. I support various platforms like YouTube.\n\n"
        "You can choose the quality of the video by sending:\n"
        "/quality - List available quality options\n"
        "\nThe bot will send the video and its thumbnail."
    )
    await message.reply_text(help_msg)

@bot.on_message(filters.command("quality"))
async def quality(_, message: Message):
    quality_msg = (
        "Available quality options:\n"
        "1. Best\n"
        "2. 720p\n"
        "3. 480p\n"
        "4. 360p\n"
        "\nSend the quality option number before the URL to select."
    )
    await message.reply_text(quality_msg)

# Video download from URL
@bot.on_message(filters.text)
async def download_video(_, message: Message):
    text = message.text.split()
    quality = "best"  # Default quality
    url = None

    # Parse quality and URL
    if len(text) > 1 and text[0].isdigit():
        quality = text[0]
        url = " ".join(text[1:])
    else:
        url = " ".join(text)

    if not url:
        await message.reply_text("Please provide a URL.")
        return

    await message.reply_text(f"Downloading video from: {url} with quality: {quality}")

    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': f'bestvideo[height<={quality}]+bestaudio/best' if quality.isdigit() else 'best',
        'noplaylist': True,
        'quiet': True,
        'progress_hooks': [progress_hook],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)
            thumbnail_url = info.get('thumbnail', '')

        # Send video with thumbnail
        with open(file_name, 'rb') as video_file:
            await message.reply_video(video_file, caption=f"Downloaded video from {url}")

        # Send thumbnail
        if thumbnail_url:
            thumb = requests.get(thumbnail_url).content
            await message.reply_photo(thumb)

        os.remove(file_name)  # Remove file after sending

        # Log in dump chat
        if DUMP_CHAT_ID:
            await bot.send_message(DUMP_CHAT_ID, f"Video downloaded from {url}")

    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

def progress_hook(d):
    if d['status'] == 'finished':
        file_size = d.get('total_bytes', 'unknown')
        file_size_str = f"{file_size / (1024 * 1024):.2f} MB" if file_size != 'unknown' else 'unknown'
        print(f"Done downloading {file_size_str}!")

# Run the bot
bot.run()
