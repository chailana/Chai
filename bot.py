#Here is the complete updated code for your Telegram bot, incorporating the necessary adjustments to handle callback queries correctly and using the provided bot token:

#```python
import logging
import os
import yt_dlp
import asyncio
import math
import time
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO)

# Initialize user settings and history
user_preferences = {}
download_records = {}
url_format_map = {}  # To store original URL and format ID mapping

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Use /download <URL> to fetch videos. Available formats will be displayed for selection.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Commands available:\n"
        "/start - Initiate the bot\n"
        "/download <URL> - Download a video\n"
        "/settings - Check or modify your settings\n"
        "/help - Display this help information\n"
        "/history - View your download history"
    )
    await update.message.reply_text(help_text)

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    history = download_records.get(user_id, [])
    if not history:
        await update.message.reply_text("No download history found.")
    else:
        history_output = "Download History:\n" + "\n".join(history)
        await update.message.reply_text(history_output)

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query  # Get the callback query
    user_id = query.message.chat.id  # Use the chat ID from the query message

    if user_id not in user_preferences:
        user_preferences[user_id] = {'upload_as_video': True, 'upload_thumbnail': True}
    
    settings_info = "Current Settings:\n"
    settings_info += f"Upload as Video: {'Enabled' if user_preferences[user_id]['upload_as_video'] else 'Disabled'}\n"
    settings_info += f"Upload Thumbnail: {'Enabled' if user_preferences[user_id]['upload_thumbnail'] else 'Disabled'}\n"

    keyboard = [
        [InlineKeyboardButton(
            "Toggle Upload as Video 🎥" if user_preferences[user_id]['upload_as_video'] else "Toggle Upload as File 🗃️",
            callback_data='toggle_video')],
        [InlineKeyboardButton("Toggle Upload Thumbnail", callback_data='toggle_thumbnail')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(settings_info, reply_markup=reply_markup)  # Use query.message

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the button press
    user_id = query.message.chat.id

    if user_id not in user_preferences:
        user_preferences[user_id] = {'upload_as_video': True, 'upload_thumbnail': True}

    if query.data == 'toggle_video':
        user_preferences[user_id]['upload_as_video'] = not user_preferences[user_id]['upload_as_video']
    elif query.data == 'toggle_thumbnail':
        user_preferences[user_id]['upload_thumbnail'] = not user_preferences[user_id]['upload_thumbnail']

    await settings(update, context)  # Call settings to update the user

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text('Please provide a URL to download the video.')
        return

    url = context.args[0]
    user_id = update.effective_chat.id

    available_formats = fetch_available_formats(url)
    if available_formats:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        for f in available_formats:
            format_id = f['format_id']
            format_hash = hashlib.md5(format_id.encode()).hexdigest()[:10]
            url_format_map[f"{url_hash}:{format_hash}"] = (url, format_id)

        await present_format_options(update, available_formats, url_hash)
    else:
        await update.message.reply_text("No formats available for this video.")

async def present_format_options(update: Update, formats, url_hash):
    keyboard = []
    for f in formats:
        format_id = f['format_id']
        format_note = f.get('format_note', f'Quality: {f.get("width", "Unknown")}x{f.get("height", "Unknown")}')
        size = f.get('filesize', 'Unknown size')

        format_hash = hashlib.md5(format_id.encode()).hexdigest()[:10]
        
        callback_data = f"download:{url_hash}:{format_hash}"
        button_text = f"{format_id} - {format_note} - {size}" if size != 'Unknown size' else f"{format_id} - {format_note}"
        button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
        keyboard.append([button])

    keyboard.append([InlineKeyboardButton("CLOSE", callback_data="close")])  # Add a close option
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please select the desired format or file size to upload:", reply_markup=reply_markup)

async def handle_format_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    query.answer()  # Acknowledge the button press
    data = query.data.split(':')

    if data[0] == "download":
        url_hash = data[1]
        format_hash = data[2]
        original_url, selected_format = url_format_map.get(f"{url_hash}:{format_hash}", (None, None))
        
        if original_url and selected_format:
            await execute_video_download(update, original_url, selected_format)
        else:
            await query.message.reply_text("Error retrieving video details.")
    elif data[0] == "close":
        await query.message.reply_text("Selection has been closed.")

async def execute_video_download(update: Update, url: str, format_id: str):
    user_id = update.effective_chat.id
    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'progress_hooks': [lambda d: asyncio.run(track_progress(d, update))],
    }

    await update.message.reply_text("📤 Uᴘʟᴏᴀᴅɪɴɢ Pʟᴇᴀsᴇ Wᴀɪᴛ...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'No Title')

        video_file_path = f"{title}.mp4"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=open(video_file_path, 'rb'), caption=f'Title: {title}')

        if user_id not in download_records:
            download_records[user_id] = []
        download_records[user_id].append(f"{title}")

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')
    finally:
        try:
            os.remove(video_file_path)
        except:
            pass

async def track_progress(progress, update):
    if progress['status'] == 'finished':
        return
    
    if progress['status'] == 'downloading':
        total_size = progress.get('total_bytes', 1)  # Avoid division by zero
        downloaded_size = progress.get('downloaded_bytes', 0)

        percentage = downloaded_size * 100 / total_size
        speed = downloaded_size / (time.time() - start_time) if start_time else 0
        bar_length = 20
        progress_bar = "[{0}{1}] \n".format(
            ''.join(["█" for _ in range(math.floor(percentage / (100 / bar_length)))]),
            ''.join(["░" for _ in range(bar_length - math.floor(percentage / (100 / bar_length)))])
        )

        status_message = f"**Uploading...**\n\n{progress_bar}\n" \
                         f"**Progress:** {round(percentage, 2)}%\n" \
                         f"**Downloaded:** {format_bytes(downloaded_size)}\n" \
                         f"**Total Size:** {format_bytes(total_size)}\n" \
                         f"**Speed:** {format_bytes(speed)}\n" \
                         f"**ETA:** {format_time(milliseconds=(total_size - downloaded_size) / speed * 1000)}"

        try:
            await update.message.reply_text(status_message)
        except Exception as e:
            print(f"Error updating progress: {e}")

def format_bytes(size):
    if not size:
        return ""
    factor = 1024
    index = 0
    units = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > factor:
        size /= factor
        index += 1
    return str(round(size, 2)) + " " + units[index] + 'B'

def format_time(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    time_str = ((str(days) + "d, ") if days else "") + \
                ((str(hours) + "h, ") if hours else "") + \
                ((str(minutes) + "m, ") if minutes else "") + \
                ((str(seconds) + "s, ") if seconds else "")
    return time_str[:-2]

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
    application = ApplicationBuilder().token('6985164126:AAF2wxioikBvrlzzBlSklXqNpO8jG-eyaVY').build()

    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('download', download_and_send))
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CommandHandler('history', history_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CallbackQueryHandler(handle_format_selection, pattern=r'download:\S+:\S+'))

    application.run_polling()

if __name__ == '__main__':
    main()
# modifications or assistance, feel free to ask!
