# bot.py
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from urllib.parse import urlparse

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Telegram bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! Send me a URL to upload.')

def download_file(url: str, file_name: str):
    """Downloads a file from a given URL."""
    with open(file_name, 'wb') as f:
        response = requests.get(url, stream=True)
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def process_url(update: Update, context: CallbackContext) -> None:
    """Processes the URL sent by the user."""
    url = update.message.text
    parsed_url = urlparse(url)

    if not all([parsed_url.scheme, parsed_url.netloc]):
        update.message.reply_text("Invalid URL format. Please provide a valid URL.")
        return

    try:
        response = requests.head(url, allow_redirects=True)
        response.raise_for_status()

        file_name = os.path.basename(parsed_url.path) or 'uploaded_file'

        update.message.reply_text("Downloading & Uploading file... Please be patient, this might take a while.")
        download_file(url, file_name)

        # Send the downloaded file
        with open(file_name, 'rb') as f:
            context.bot.send_document(chat_id=update.effective_chat.id, document=f)

        os.remove(file_name) 

    except requests.exceptions.RequestException as e:
        update.message.reply_text(f"Error downloading or uploading file: {e}")

def main() -> None:
    """Start the bot."""
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_url))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
