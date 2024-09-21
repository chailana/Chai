import logging
import os
import yt_dlp
import asyncio
import math
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s', level=logging.INFO)

# Initialize user settings and history
user_settings = {}
download_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Use /download <URL> to download videos. Available qualities will be listed if needed.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/download <URL> - Download a video\n"
        "/settings - View or change your settings\n"
        "/help - Show this help message\n"
        "/history - Show your download history"
    )
    await update.message.reply_text(help_text)

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    history = download_history.get(user_id, [])
    if not history:
        await update.message.reply_text("No download history found.")
    else:
        history_text = "Download History:\n" + "\n".join(history)
        await update.message.reply_text(history_text)

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
    if len(context.args) < 1:
        await update.message.reply_text('Please provide a URL to download the video.')
        return

    url = context.args[0]
    user_id = update.effective_chat.id

    formats = get_available_formats(url)
    if formats:
        await send_format_options(update, formats, url)
    else:
        await update.message.reply_text("No available formats found for this video.")

async def send_format_options(update: Update, formats, url):
    keyboard = []
    for f in formats:
        format_id = f['format_id']
        format_note = f.get('format_note', f'Quality: {f.get("width", "Unknown")}x{f.get("height", "Unknown")}')
        size = f.get('filesize', 'Unknown size')  # Get the file size if available
        
        # Limit the size of the callback data
        callback_data = f"download:{url}:{format_id[:20]}"  # Shorten format_id if necessary
        button_text = f"{format_id} - {format_note} - {size}" if size != 'Unknown size' else f"{format_id} - {format_note}"
        button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
        keyboard.append([button])

    keyboard.append([InlineKeyboardButton("CLOSE", callback_data="close")])  # Add a close button
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select the desired format or file size to upload:", reply_markup=reply_markup)

async def handle_format_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    query.answer()  # Acknowledge the button press
    data = query.data.split(':')
    
    if data[0] == "download":
        url = data[1]
        chosen_format = data[2]
        await download_video(update, url, chosen_format)
    elif data[0] == "close":
        await query.message.reply_text("Selection closed.")

async def download_video(update: Update, url: str, format_id: str):
    user_id = update.effective_chat.id
    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'progress_hooks': [lambda d: asyncio.run(progress_for_telegram(d, update))],
    }

    await update.message.reply_text("📤 Uᴘʟᴏᴀᴅɪɴɢ Pʟᴇᴀsᴇ Wᴀɪᴛ...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'No Title')

        video_path = f"{title}.mp4"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=open(video_path, 'rb'), caption=f'Title: {title}')

        # Add to download history
        if user_id not in download_history:
            download_history[user_id] = []
        download_history[user_id].append(f"{title}")

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')
    finally:
        # Clean up downloaded files
        try:
            os.remove(video_path)
        except:
            pass

async def progress_for_telegram(progress, update):
    if progress['status'] == 'finished':
        return
    
    if progress['status'] == 'downloading':
        total_size = progress.get('total_bytes', 1)  # Avoid division by zero
        downloaded_size = progress.get('downloaded_bytes', 0)

        percentage = downloaded_size * 100 / total_size
        speed = downloaded_size / (time.time() - start) if start else 0
        bar_width = 20
        progress_bar = "[{0}{1}] \n".format(
            ''.join(["█" for _ in range(math.floor(percentage / (100 / bar_width)))]),
            ''.join(["░" for _ in range(bar_width - math.floor(percentage / (100 / bar_width)))])
        )

        status_message = f"**Uploading...**\n\n{progress_bar}\n" \
                         f"**Progress:** {round(percentage, 2)}%\n" \
                         f"**Done:** {humanbytes(downloaded_size)}\n" \
                         f"**Total Size:** {humanbytes(total_size)}\n" \
                         f"**Speed:** {humanbytes(speed)}\n" \
                         f"**ETA:** {TimeFormatter(milliseconds=(total_size - downloaded_size) / speed * 1000)}"

        try:
            await update.message.reply_text(status_message)
        except Exception as e:
            print(f"Error updating progress: {e}")

def humanbytes(size):
    if not size:
        return ""
    power = 1024
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2]

def get_available_formats(url):
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

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('download', download_and_send))
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CommandHandler('history', history_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CallbackQueryHandler(handle_format_selection, pattern=r'download:\S+:\S+'))

    application.run_polling()

if __name__ == '__main__':
    main()
