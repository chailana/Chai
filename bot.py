import os
import logging
import re
import asyncio
import time
import math
from dotenv import load_dotenv
from pyrogram import Client, filters, enums
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

# Initialize the bot client
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

last_percentage = 0  # To track the last reported percentage

def clean_url(url):
    """Clean the URL by removing unnecessary query parameters."""
    return url.split('?')[0]  # Keep only the base URL

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
    
    cleaned_url = clean_url(url)  # Clean the URL before processing
    
    if is_valid_url(cleaned_url):
        await download_video(message.chat.id, cleaned_url, 'best')  # Download video in best quality
    else:
        await client.send_message(message.chat.id, "Please send a valid URL.")

@bot.on_message(filters.command("download"))
async def handle_download_command(client, message):
    if len(message.command) < 2:
        await client.send_message(message.chat.id, "Please provide a URL after the /download command.")
        return
    
    url = message.command[1].strip()
    
    cleaned_url = clean_url(url)  # Clean the URL before processing
    
    if is_valid_url(cleaned_url):
        formats = await get_video_formats(cleaned_url)
        
        if formats:
            keyboard = []
            for format_id, height, note in formats:
                button_label = f"{note} ({height}p)"
                button = InlineKeyboardButton(button_label, callback_data=f"quality_{format_id}")
                keyboard.append([button])
            
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
    """Download the video and send it to the user."""
    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [lambda d: progress_hook(d,user_id)],
    }
    
    try:
         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
             info_dict = ydl.extract_info(url , download=True)
             final_video_file= ydl.prepare_filename(info_dict)

             # Send the video directly to the user only
             await bot.send_video(user_id , video=final_video_file)  # Send to user
            
             os.remove(final_video_file)  # Clean up the video file after sending
            
    except KeyError as e:
         logger.error(f"KeyError: {e} - This may indicate that 'total_bytes' was not found.")
         await bot.send_message(user_id, "There was an error downloading the video. Please check the URL and try again.")
    except Exception as e:
         logger.error(f"Error downloading file: {e}")
         await bot.send_message(user_id, "An unexpected error occurred while downloading the video.")

def is_valid_url(url):
    """Check if the provided URL is valid."""
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
    """Retrieve available video formats for a given URL."""
    ydl_opts = {
        'format': 'bestvideo[height<=?1080]+bestaudio/best',  # Limits to 1080p
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)  # Set download=False to just retrieve info
            formats = info_dict.get('formats', [])
            
            # Filter and display the desired formats
            available_formats = []
            for fmt in formats:
                if 'height' in fmt:
                    available_formats.append((fmt['format_id'], fmt['height'], fmt.get('format_note', '')))
            
            return available_formats
        
    except Exception as e:
        logger.error(f"Error retrieving video formats: {e}")
        return None

async def progress_for_pyrogram(current, total, ud_type, message, start_time):
    """Provide detailed progress feedback during downloads."""
    
    now = time.time()
    diff = now - start_time
    
    percentage = current * 100 / total if total else 0
    speed = current / diff if diff > 0 else 0
    
    elapsed_time_str = TimeFormatter(milliseconds=round(diff * 1000))
    
    if total > current:
        time_to_completion_str = TimeFormatter(milliseconds=round((total - current) / speed * 1000)) if speed > 0 else "Unknown"
        
        status_message = (
            f"**{ud_type}**\n"
            f"Progress: [{current}/{total}] ({percentage:.2f}%)\n"
            f"Speed: {humanbytes(speed)}\n"
            f"Elapsed Time: {elapsed_time_str}\n"
            f"Estimated Time to Completion: {time_to_completion_str}"
        )
        
        try:
            await message.edit(text=status_message,
                               parse_mode=enums.ParseMode.MARKDOWN,
                               reply_markup=InlineKeyboardMarkup(
                                   [[InlineKeyboardButton('⛔️ Cancel', callback_data='close')]]
                               ))
        except Exception as e:
            logger.error(f"Error updating progress message: {e}")

def humanbytes(size):
    """Convert bytes to a human-readable format."""
    if size is None or size < 0:
        return ""
    
    power = 1024
    n = 0
    Dic_powerN = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    
    while size >= power and n < len(Dic_powerN) - 1:
        size /= power
        n += 1
        
    return f"{round(size)} {Dic_powerN[n]}B"

def TimeFormatter(milliseconds: int) -> str:
    """Format time in milliseconds to a human-readable string."""
    
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    
    minutes, seconds = divmod(seconds, 60)
    
    hours, minutes = divmod(minutes, 60)
    
    days, hours = divmod(hours, 24)
    
    tmp = ((str(days) + "d ") if days else "") + \
          ((str(hours) + "h ") if hours else "") + \
          ((str(minutes) + "m ") if minutes else "") + \
          ((str(seconds) + "s ") if seconds else "") + \
          ((str(milliseconds) + "ms") if milliseconds else "")
          
    return tmp.strip()

def progress_hook(d,user_id):
     """Provide feedback on download progress."""
     global last_percentage  
     
     if d['status'] == 'downloading':
         total_bytes = d.get('total_bytes', None)
         downloaded_bytes = d.get('downloaded_bytes', 0)
         
         if total_bytes is not None:
             percent = downloaded_bytes / total_bytes * 100
            
             if percent >= last_percentage + 5:  # Update every 5%
                 asyncio.create_task(bot.send_message(user_id , f"Download progress: {percent:.2f}% ({downloaded_bytes} bytes)"))
                 last_percentage = percent  
         else:
             asyncio.create_task(bot.send_message(user_id , f"Downloaded {downloaded_bytes} bytes so far."))

if __name__ == '__main__':
     bot.run()
