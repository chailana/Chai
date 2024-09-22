import os
from dotenv import load_dotenv
from pyrogram import Client, filters
import yt_dlp

load_dotenv()

API_ID = os.getenv('API_ID')  # Your API ID from https://my.telegram.org
API_HASH = os.getenv('API_HASH')  # Your API Hash from https://my.telegram.org
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Your Bot Token from BotFather

# Initialize the bot with API ID, API Hash, and Bot Token
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
def send_welcome(client, message):
    client.send_message(message.chat.id, "Welcome! Send me a direct video link or a URL from supported websites (like YouTube) to download.")

@bot.on_message(filters.text)
def handle_message(client, message):
    url = message.text
    if is_valid_url(url):
        client.send_message(message.chat.id, f"Downloading from {url}...")
        try:
            file_path = download_video(url)
            if file_path:
                send_large_file(client, message.chat.id, file_path)
                os.remove(file_path)  # Clean up the file after sending
            else:
                client.send_message(message.chat.id, "Failed to download a valid video file.")
        except Exception as e:
            client.send_message(message.chat.id, f"An error occurred: {str(e)}")
    else:
        client.send_message(message.chat.id, "Please send a valid URL.")

def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")

def download_video(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)
            return video_file
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def send_large_file(client, chat_id, file_path):
    client.send_video(chat_id, video=file_path)

if __name__ == '__main__':
    bot.run()
