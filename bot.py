import os
import time
from dotenv import load_dotenv
from pyrogram import Client, filters
import yt_dlp

load_dotenv()

API_ID = os.getenv('API_ID')  # Your API ID from https://my.telegram.org
API_HASH = os.getenv('API_HASH')  # Your API Hash from https://my.telegram.org
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Your Bot Token from BotFather
DUMP_CHANNEL_ID = -1002247666039  # Replace with your channel ID

# Initialize the bot with API ID, API Hash, and Bot Token
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Global variables to store user preferences and download queue
user_preferences = {}
download_queue = {}
quality_requests = {}  # To track quality selection requests

@bot.on_message(filters.command("start"))
def send_welcome(client, message):
    client.send_message(message.chat.id, "Welcome! Send me a direct video link or a URL from supported websites (like YouTube) to download.\nUse /help for more commands.")

@bot.on_message(filters.command("help"))
def send_help(client, message):
    help_text = (
        "/start - Welcome message\n"
        "/help - List of commands\n"
        "/setformat <format> - Set your preferred download format (e.g., mp4)\n"
        "/resetformat - Reset your preferred format to default\n"
        "Just send a video URL to download it."
    )
    client.send_message(message.chat.id, help_text)

@bot.on_message(filters.command("setformat"))
def set_format(client, message):
    format_choice = message.text.split(maxsplit=1)
    if len(format_choice) == 2:
        user_preferences[message.chat.id] = format_choice[1]
        client.send_message(message.chat.id, f"Your preferred format has been set to: {format_choice[1]}")
    else:
        client.send_message(message.chat.id, "Please specify a valid format after the command.")

@bot.on_message(filters.command("resetformat"))
def reset_format(client, message):
    if message.chat.id in user_preferences:
        del user_preferences[message.chat.id]
        client.send_message(message.chat.id, "Your preferred format has been reset to default.")
    else:
        client.send_message(message.chat.id, "You have not set a preferred format yet.")

@bot.on_message(filters.text)
def handle_message(client, message):
    url = message.text.strip()
    if is_valid_url(url):
        # Add to download queue and process
        download_queue[message.chat.id] = url  # Store the URL for the user
        client.send_message(message.chat.id, f"Downloading from {url}...")
        
        # Start downloading and get available formats
        formats = get_video_formats(url)
        
        if formats:
            quality_options = "\n".join(
                [f"{fmt.get('format_note', 'No Note')} ({fmt.get('height', 'N/A')}p)" for fmt in formats if 'height' in fmt]
            )
            quality_requests[message.chat.id] = formats  # Store available formats for the user
            
            client.send_message(message.chat.id, f"Available quality options:\n{quality_options}\n\nPlease reply with the desired quality (e.g., 720p).")
        else:
            client.send_message(message.chat.id, "Failed to retrieve video formats.")
    else:
        client.send_message(message.chat.id, "Please send a valid URL.")

@bot.on_message(filters.text & filters.private)
def handle_quality_selection(client, message):
    user_id = message.chat.id
    if user_id in quality_requests:
        selected_quality = message.text.strip()
        
        # Get available formats for this user
        formats = quality_requests[user_id]
        
        # Find the selected format
        selected_format = next((fmt for fmt in formats if selected_quality in fmt.get('format_note', '')), None)
        
        if selected_format:
            client.send_message(user_id, f"You selected: {selected_quality}. Downloading...")
            download_video(user_id, download_queue[user_id], selected_format['format_id'])
            del download_queue[user_id]  # Remove from queue after processing
            del quality_requests[user_id]  # Clear the quality request after processing
        else:
            client.send_message(user_id, "Selected quality not available. Please choose from the available options.")
    else:
        client.send_message(user_id, "Please send a valid video URL first.")

def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")

def get_video_formats(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url)
            return info_dict['formats']  # Return available formats without downloading
    except Exception as e:
        print(f"Error retrieving video formats: {e}")
        return None

def download_video(user_id, url, format_id):
    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [lambda d: progress_hook(d, user_id)],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            final_video_file = ydl.prepare_filename(info_dict)

            # Send the video file and also upload it to the dump channel
            bot.send_video(DUMP_CHANNEL_ID, video=final_video_file)  # Send to dump channel
            bot.send_video(user_id, video=final_video_file)  # Send to user
            
            os.remove(final_video_file)  # Clean up the video file after sending
            
    except Exception as e:
        print(f"Error downloading file: {e}")

def progress_hook(d, user_id):
    if d['status'] == 'downloading':
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        bot.send_message(user_id, f"Download progress: {percent:.2f}%")

if __name__ == '__main__':
    bot.run()
