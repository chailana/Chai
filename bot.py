import os
import yt_dlp
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

# Set your bot token here
BOT_TOKEN = 'YOUR_BOT_TOKEN'

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Send me a video URL!')

def download_video(url: str):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegThumbnail',
            'already_have_thumbnail': True,
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_title = info_dict.get('title', None)
        thumbnail = info_dict.get('thumbnail', None)
        return f'downloads/{video_title}.{info_dict["ext"]}', thumbnail

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    update.message.reply_text('Downloading your video...')
    
    try:
        video_file, thumbnail = download_video(url)
        with open(video_file, 'rb') as video:
            update.message.reply_video(video, caption='Here is your video!', thumb=thumbnail)
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.text & ~filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    main()
