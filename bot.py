import os
import time
from dotenv import load_dotenv
from pyrogram import Client, filters
import yt_dlp
from PIL import Image
import io

load_dotenv()

API_ID = os.getenv('API_ID')  # Your API ID from https://my.telegram.org
API_HASH = os.getenv('API_HASH')  # Your API Hash from https://my.telegram.org
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Your Bot Token from BotFather

# Initialize the bot with API ID, API Hash, and Bot Token
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Global variables to store user preferences and download queue
user_preferences = {}
download_queue = []

@bot.on_message(filters.command("start"))
def send_welcome(client, message):
    client.send_message(message.chat.id, "Welcome! Send me a direct video link or a URL from supported websites (like YouTube) to download.\nUse /help for more commands.")

@bot.on_message(filters.command("help"))
def send_help(client, message):
    help_text = (
        "/start - Welcome message\n"
        "/help - List of commands\n"
        "/setformat <format> - Set your preferred download format (e.g., mp4)\n"
        "Just send a video URL to download it."
    )
    client.send_message(message.chat.id, help_text)

@bot.on_message(filters.text)
def handle_message(client, message):
    url = message.text.strip()
    if is_valid_url(url):
        # Add to download queue and process
        download_queue.append((client, message.chat.id, url))
        process_download_queue()
    else:
        client.send_message(message.chat.id, "Please send a valid URL.")

def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")

def download_video(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegVideoThumbnail',
            'output_template': '%(title)s_thumbnail.jpg',
            'preferedformat': 'jpg',  # Generate thumbnail in jpg format
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)
            thumbnail_file = f"{info_dict['title']}_thumbnail.jpg"
            return video_file, thumbnail_file  # Return both video and thumbnail paths
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def process_download_queue():
    if not download_queue:
        return

    client, chat_id, url = download_queue.pop(0)  # Get the next request from the queue

    client.send_message(chat_id, f"Downloading from {url}...")
    
    file_info = download_video(url)
    
    if file_info:
        video_file, thumbnail_file = file_info
        
        # Send progress updates while downloading (simulated here)
        for progress in range(0, 101, 10):  # Simulate progress updates
            time.sleep(1)  # Simulate time taken for each step
            client.send_message(chat_id, f"Download progress: {progress}%")
        
        # Send the video file and thumbnail after downloading is complete
        client.send_video(chat_id, video=video_file, thumb=thumbnail_file)
        
        os.remove(video_file)  # Clean up the video file after sending
        os.remove(thumbnail_file)  # Clean up the thumbnail after sending
        
    else:
        client.send_message(chat_id, "Failed to download a valid video file.")

if __name__ == '__main__':
    bot.run()
