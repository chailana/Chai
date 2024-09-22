import os
import requests
import telebot
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Send me a direct video link to upload.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if is_valid_url(url):
        bot.reply_to(message, f"Downloading from {url}...")
        try:
            file_path = download_file(url)
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

def download_file(url):
    local_filename = url.split('/')[-1]
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):  # 8KB chunks
                    f.write(chunk)
        # Validate if the downloaded file is indeed a video
        if not is_video_file(local_filename):
            os.remove(local_filename)  # Remove invalid file
            return None
        return local_filename
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def is_video_file(file_path):
    # Check for common video file extensions
    return file_path.endswith(('.mp4', '.mkv', '.avi', '.mov'))

if __name__ == '__main__':
    bot.polling()
