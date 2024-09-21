import logging
import os
import requests
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO)

# Initialize user settings
user_settings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Use /download <URL> <quality> to download videos. Available qualities: best, worst.')

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id not in user_settings:
        user_settings[user_id] = {'upload_as_video': True, 'upload_thumbnail': True}
    
    settings_text = "Current Settings:\n"
    settings_text += f"Upload as Video: {'Enabled' if user_settings[user_id]['upload_as_video'] else 'Disabled'}\n"
    settings_text += f"Upload Thumbnail: {'Enabled' if user_settings[user_id]['upload_thumbnail'] else 'Disabled'}\n"

    keyboard = [
        [InlineKeyboardButton(
            "Toggle Upload as Video 🎥" if user_settings[user_id]['upload_as_video'] else "Toggle Upload as File 🗃️",
            callback_data='toggle_video')],
        [InlineKeyboardButton("Toggle Upload Thumbnail", callback_data='toggle_thumbnail')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(settings_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.message.chat.id

    if user_id not in user_settings:
        user_settings[user_id] = {'upload_as_video': True, 'upload_thumbnail': True}

    if query.data == 'toggle_video':
        user_settings[user_id]['upload_as_video'] = not user_settings[user_id]['upload_as_video']
    elif query.data == 'toggle_thumbnail':
        user_settings[user_id]['upload_thumbnail'] = not user_settings[user_id]['upload_thumbnail']

    await settings(update, context)

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text('Please provide a URL and quality (best or worst).')
        return

    url = context.args[0]
    quality = context.args[1]
    title, size, thumbnail_url = get_video_info(url)

    user_id = update.effective_chat.id
    if user_id not in user_settings:
        user_settings[user_id] = {'upload_as_video': True, 'upload_thumbnail': True}

    upload_as_video = user_settings[user_id]['upload_as_video']
    upload_thumbnail = user_settings[user_id]['upload_thumbnail']

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if quality == 'best' else 'worst',
        'outtmpl': f'{title}.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'progress_hooks': [lambda d: update_progress(update, d)],
    }

    await update.message.reply_text("wair dawg trying to download and upload the video😎")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'No Title')

        # Download the thumbnail if enabled
        if upload_thumbnail:
            thumbnail_response = requests.get(thumbnail_url)
            thumbnail_path = f"{title}_thumbnail.jpg"
            with open(thumbnail_path, 'wb') as f:
                f.write(thumbnail_response.content)

        # Send the video or file based on user settings
        video_path = f"{title}.mp4"
        if upload_as_video:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=open(video_path, 'rb'),
                                          caption=f'Title: {title}\nSize: {size}')
        else:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(video_path, 'rb'),
                                             caption=f'Title: {title}\nSize: {size}')

        if upload_thumbnail:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(thumbnail_path, 'rb'))

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')
    finally:
        # Clean up downloaded files
        try:
            os.remove(video_path)
            if upload_thumbnail:
                os.remove(thumbnail_path)
        except:
            pass

def update_progress(update, progress):
    if progress['status'] == 'downloading':
        total_size = progress.get('total_bytes', None)
        downloaded_size = progress.get('downloaded_bytes', 0)

        if total_size:
            percent = downloaded_size / total_size * 100
            progress_message = f"Download progress: {percent:.2f}%"
            # Update the progress message in the chat
            asyncio.create_task(update.message.reply_text(progress_message))

def get_video_info(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    title = info.get('title', 'No title')
    size = info.get('filesize', 'Unknown size')
    thumbnail = info.get('thumbnail', '')

    return title, size, thumbnail

def main():
    application = ApplicationBuilder().token('6985164126:AAF2wxioikBvrlzzBlSklXqNpO8jG-eyaVY').build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('download', download_and_send))
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
