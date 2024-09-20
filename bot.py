import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.utils.request import Request
from telegram import Bot
import requests
from bs4 import BeautifulSoup
import re
import json

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('TOKEN')
BOT = Bot(TOKEN)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hello! I\'m your URL bot.')

def handle_url(update, context):
    url = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id, text='Processing URL...')
    try:
        file_info = get_file_info(url)
        if file_info:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Title: {file_info["title"]}')
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Size: {file_info["size"]}')
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Resolution: {file_info["resolution"]}')
            upload_file(update, context, url, file_info)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Failed to retrieve file information.')
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Error: {str(e)}')

def get_file_info(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.find('title').text
    size = None
    resolution = None
    # Extract size and resolution from the HTML content
    # This may vary depending on the website and file type
    # For demonstration purposes, let's assume we can extract this information
    size_match = re.search(r'Size: (\d+(?:\.\d+)? (KB|MB|GB))', response.text)
    if size_match:
        size = size_match.group(1)
    resolution_match = re.search(r'Resolution: (\d+x\d+)', response.text)
    if resolution_match:
        resolution = resolution_match.group(1)
    return {'title': title, 'size': size, 'resolution': resolution}

def upload_file(update, context, url, file_info):
    file_path = download_file(url)
    if file_path:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Uploading file...')
        file_id = upload_file_to_telegram(file_path, file_info)
        if file_id:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'File uploaded successfully! File ID: {file_id}')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Failed to upload file.')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Failed to download file.')

def download_file(url):
    file_path = f'/tmp/{os.path.basename(url)}'
    response = requests.get(url, stream=True)
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)
    return file_path

def upload_file_to_telegram(file_path, file_info):
    file_id = None
    with open(file_path, 'rb') as f:
        file_id = BOT.send_document(chat_id=update.effective_chat.id, document=f, filename=file_info['title']).document.file_id
    return file_id

def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, handle_url))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
