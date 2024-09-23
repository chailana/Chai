import os
import logging
import re
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Load environment variables from .env file
load_dotenv()

# Initialize the bot with API ID, API Hash, and Bot Token
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
DUMP_CHANNEL_ID = -1002247666039  # Replace with your actual channel ID

# Initialize the bot client
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def send_welcome(client, message):
    await client.send_message(message.chat.id, "Welcome! Send me a direct video link or a URL from supported websites (like YouTube) to download.\nUse /help for more commands.")

@bot.on_message(filters.command("help"))
async def send_help(client, message):
    help_text = (
        "/start - Welcome message\n"
        "/help - List of commands\n"
        "/download <URL> - Get available quality options for a video\n"
        "Just send a video URL to download it in the best quality."
    )
    await client.send_message(message.chat.id, help_text)

@bot.on_message(filters.text)
async def handle_message(client, message):
    url = message.text.strip()
    
    if is_valid_url(url):
        # Download the video in best quality when a URL is sent directly
        await download_video(message.chat.id, url, 'best')
    else:
        await client.send_message(message.chat.id, "Please send a valid URL.")

@bot.on_message(filters.command("download"))
async def handle_download_command(client, message):
    if len(message.command) < 2:
        await client.send_message(message.chat.id, "Please provide a URL after the /download command.")
        return
    
    url = message.command[1].strip()
    
    if is_valid_url(url):
        formats = await get_video_formats(url)
        
        if formats:
            keyboard = []
            seen_formats = set()  # To avoid duplicates
            
            for fmt in formats:
                if 'height' in fmt and fmt['format_id'] not in seen_formats:
                    button_label = f"{fmt.get('format_note', 'No Note')} ({fmt['height']}p)"
                    button = InlineKeyboardButton(button_label, callback_data=f"quality_{fmt['format_id']}")
                    keyboard.append([button])
                    seen_formats.add(fmt['format_id'])  # Mark this format as seen
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await client.send_message(message.chat.id, "Available quality options:", reply_markup=reply_markup)
        else:
            await client.send_message(message.chat.id, "Failed to retrieve video formats.")
    else:
        await client.send_message(message.chat.id, "Please send a valid URL.")

@bot.on_callback_query(filters.regex(r"quality_"))
async def handle_quality_selection(client, callback_query):
    user_id = callback_query.from_user.id
    selected_format_id = callback_query.data.split("_")[1]

    await callback_query.answer()  # Acknowledge the callback

    url = callback_query.message.reply_to_message.text.strip()
    
    await download_video(user_id, url, selected_format_id)

async def download_video(user_id, url, format_id):
    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title)s.%(ext)s',
         'progress_hooks': [lambda d: progress_hook(d,user_id)],
     }
    
    try:
         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
             info_dict = ydl.extract_info(url , download=True)
             final_video_file= ydl.prepare_filename(info_dict)

             await bot.send_video(DUMP_CHANNEL_ID , video=final_video_file)  # Send to dump channel
             await bot.send_video(user_id , video=final_video_file)  # Send to user
            
             os.remove(final_video_file)  # Clean up the video file after sending
            
    except Exception as e:
         logger.error(f"Error downloading file: {e}")

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

async def get_video_formats(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url)
            return info_dict['formats']  # Return available formats without downloading
    except Exception as e:
        logger.error(f"Error retrieving video formats: {e}")
        return None

def progress_hook(d,user_id):
     if d['status'] == 'downloading':
         percent= d['downloaded_bytes'] / d['total_bytes'] * 100 
         bot.send_message(user_id , f"Download progress: {percent:.2f}%")

if __name__ == '__main__':
     bot.run()
