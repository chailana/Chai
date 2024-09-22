import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import requests
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')

logging.basicConfig(level=logging.INFO)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hello! I can upload files, videos, and photos to the internet. Send me a file, video, or photo to get started!')

def upload_file(update, context):
    file = update.message.document
    file_name = file.file_name
    file_id = file.file_id
    file_info = context.bot.get_file(file_id)
    file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}'
    response = requests.get(file_url, stream=True)
    with open(file_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)
    uploaded_url = upload_to_internet(file_name)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'File uploaded successfully! URL: {uploaded_url}')

def upload_video(update, context):
    video = update.message.video
    video_id = video.file_id
    video_info = context.bot.get_file(video_id)
    video_url = f'https://api.telegram.org/file/bot{TOKEN}/{video_info.file_path}'
    response = requests.get(video_url, stream=True)
    with open('video.mp4', 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)
    uploaded_url = upload_to_internet('video.mp4')
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Video uploaded successfully! URL: {uploaded_url}')

def upload_photo(update, context):
    photo = update.message.photo[-1]
    photo_id = photo.file_id
    photo_info = context.bot.get_file(photo_id)
    photo_url = f'https://api.telegram.org/file/bot{TOKEN}/{photo_info.file_path}'
    response = requests.get(photo_url, stream=True)
    with open('photo.jpg', 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)
    uploaded_url = upload_to_internet('photo.jpg')
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Photo uploaded successfully! URL: {uploaded_url}')

def download_youtube_video(update, context):
    url = update.message.text
    ydl_opts = {'outtmpl': '%(title)s.%(ext)s'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)
    video_title = ydl.prepare_filename(url)
    uploaded_url = upload_to_internet(video_title)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'YouTube video downloaded and uploaded successfully! URL: {uploaded_url}')

def upload_to_internet(file_name):
    api_url = 'https://api.anonfiles.com/upload'
    files = {'file': open(file_name, 'rb')}
    response = requests.post(api_url, files=files)
    uploaded_url = response.json()['data']['file']['url']['full']
    return uploaded_url

def error(update, context):
    logging.error(f'Update {update} caused error {context.error}')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.document, upload_file))
    dp.add_handler(MessageHandler(Filters.video, upload_video))
    dp.add_handler(MessageHandler(Filters.photo, upload_photo))
    dp.add_handler(MessageHandler(Filters.text, download_youtube_video))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
