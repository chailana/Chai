import os
import tempfile
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Load environment variables
load_dotenv()

# Get bot token from environment variable
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Send me a video URL to download.')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.effective_chat.id

    await update.message.reply_text('Starting download...')

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),  # Use temp directory
        'socket_timeout': 100000,
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

        os.remove(filename)  # Clean up the file
        await update.message.reply_text('Upload complete!')

    except yt_dlp.utils.DownloadError:
        await update.message.reply_text('Failed to download the video. Please check the URL and try again.')
    except Exception as e:
        await update.message.reply_text(f'An error occurred: {str(e)}')

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    application.run_polling()

if __name__ == '__main__':
    main()
