import logging
import os
import yt_dlp
import asyncio
import hashlib
from dotenv import load_dotenv
from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO)

# Initialize user settings and download history
user_preferences = {}
download_records = {}
url_format_map = {}  # Store original URL and format ID mapping

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('👋 Welcome! Use /download <URL> to fetch videos. Enjoy! 🎉')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛠️ Available Commands:\n"
        "/start - Start the bot\n"
        "/download <URL> - Download a video\n"
        "/upload <URL> - Upload a video from supported sites\n"
        "/settings - View or modify your settings\n"
        "/help - Show this help message\n"
        "/history - Check your download history"
    )
    await update.message.reply_text(help_text)

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    history = download_records.get(user_id, [])
    if not history:
        await update.message.reply_text("📜 No download history available.")
    else:
        history_output = "📥 Download History:\n" + "\n".join(history)
        await update.message.reply_text(history_output)

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    if user_id not in user_preferences:
        user_preferences[user_id] = {'upload_as_video': True, 'upload_thumbnail': True}
    
    settings_info = "⚙️ Current Settings:\n"
    settings_info += f"Upload as Video: {'✅ Enabled' if user_preferences[user_id]['upload_as_video'] else '❌ Disabled'}\n"
    settings_info += f"Upload Thumbnail: {'✅ Enabled' if user_preferences[user_id]['upload_thumbnail'] else '❌ Disabled'}\n"

    keyboard = [
        [InlineKeyboardButton(
            "📹 Toggle Upload as Video" if user_preferences[user_id]['upload_as_video'] else "📂 Toggle Upload as File",
            callback_data='toggle_video')],
        [InlineKeyboardButton("🖼️ Toggle Upload Thumbnail", callback_data='toggle_thumbnail')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.reply_text(settings_info, reply_markup=reply_markup)
    else:
        await update.message.reply_text(settings_info, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the button press
    user_id = query.message.chat.id

    if user_id not in user_preferences:
        user_preferences[user_id] = {'upload_as_video': True, 'upload_thumbnail': True}

    if query.data == 'toggle_video':
        user_preferences[user_id]['upload_as_video'] = not user_preferences[user_id]['upload_as_video']
        await settings(query, context)
    elif query.data == 'toggle_thumbnail':
        user_preferences[user_id]['upload_thumbnail'] = not user_preferences[user_id]['upload_thumbnail']
        await settings(query, context)

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text('⚠️ Please provide a URL for the video download.')
        return

    url = context.args[0]
    user_id = update.effective_chat.id

    await update.message.reply_text("📤 Downloading the best available quality... Please wait.")

    try:
        # Using yt-dlp to download the best format directly
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': False,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'No Title')

        video_file_path = f"{title}.mp4"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=open(video_file_path, 'rb'), caption=f'🎥 Title: {title}')

        if user_id not in download_records:
            download_records[user_id] = []
        download_records[user_id].append(f"{title}")

    except Exception as e:
        await update.message.reply_text(f'⚠️ Error: {str(e)}')
        logging.error(f"Download error: {str(e)}")  # Log the error for debugging
    finally:
        try:
            os.remove(video_file_path)
        except:
            pass

async def upload_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text('⚠️ Please provide a URL to upload the video from.')
        return

    url = context.args[0]
    user_id = update.effective_chat.id

    await update.message.reply_text("📤 Uploading the best available quality... Please wait.")

    try:
        # Using yt-dlp to upload the best format directly
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': False,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'No Title')

        video_file_path = f"{title}.mp4"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=open(video_file_path, 'rb'), caption=f'🎥 Title: {title}')

        if user_id not in download_records:
            download_records[user_id] = []
        download_records[user_id].append(f"{title}")

    except Exception as e:
        await update.message.reply_text(f'⚠️ Error: {str(e)}')
        logging.error(f"Upload error: {str(e)}")  # Log the error for debugging
    finally:
        try:
            os.remove(video_file_path)
        except:
            pass

def fetch_available_formats(url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('formats', [])

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('download', download_and_send))
    application.add_handler(CommandHandler('upload', upload_video))  # New upload command
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CommandHandler('history', history_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
