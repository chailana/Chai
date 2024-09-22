import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Load environment variables
load_dotenv()

# Get bot token from environment variable
TOKEN = os.getenv('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Send me a video URL to download.')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.effective_chat.id

    await update.message.reply_text('Starting download...')

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await update.message.reply_text('Download complete. Uploading to Telegram...')
        
        with open(filename, 'rb') as video_file:
            message = await context.bot.send_document(chat_id=chat_id, document=video_file, filename=filename)
            file_id = message.document.file_id
            
        await context.bot.send_video(chat_id=chat_id, video=file_id, supports_streaming=True)
        
        os.remove(filename)
        await update.message.reply_text('Upload complete!')

    except Exception as e:
        await update.message.reply_text(f'An error occurred: {str(e)}')

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    application.run_polling()

if __name__ == '__main__':
    main()
