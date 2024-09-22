import os
import telebot
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Send me a direct video link or a URL from supported websites (like YouTube) to download.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if is_valid_url(url):
        bot.reply_to(message, f"Downloading from {url}...")
        try:
            file_path = download_video(url)
            if file_path:
                with open(file_path, 'rb') as video:
                    bot.send_video(message.chat.id, video)
                os.remove(file_path)  # Clean up the file after sending
            else:
                bot.reply_to(message, "Failed to download a valid video file.")
        except Exception as e:
            bot.reply_to(message, f"An error occurred: {str(e)}")
    else:
        bot.reply_to(message, "Please send a valid URL.")

def is_valid_url(url):
    # Simple URL validation (you can expand this)
    return url.startswith("http://") or url.startswith("https://")

def download_video(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
        'progress_hooks': [hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)
            return video_file
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def hook(d):
    if d['status'] == 'finished':
        print(f"\nDone downloading video: {d['filename']}")

if __name__ == '__main__':
    bot.polling()
