import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Set your bot token here
BOT_TOKEN = 'YOUR_BOT_TOKEN'

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Send me a video URL!')

def get_formats(url: str):
    with yt_dlp.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        available_formats = {f['format_id']: f['resolution'] for f in formats if 'resolution' in f}
        return available_formats

def format_buttons(format_options):
    buttons = [[InlineKeyboardButton(text=resolution, callback_data=format_id) for format_id, resolution in format_options.items()]]
    return InlineKeyboardMarkup(buttons)

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text
    update.message.reply_text('Fetching available formats...')
    
    try:
        formats = get_formats(url)
        if formats:
            reply_markup = format_buttons(formats)
            update.message.reply_text('Select a video format:', reply_markup=reply_markup)
        else:
            update.message.reply_text('No formats available.')
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

def download_video(url: str, format_id: str):
    ydl_opts = {
        'format': format_id,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_title = info_dict.get('title', None)
        return f'downloads/{video_title}.{info_dict["ext"]}'

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    format_id = query.data
    url = context.user_data.get('video_url')

    if url:
        update.callback_query.edit_message_text('Downloading your video...')
        try:
            video_file = download_video(url, format_id)
            with open(video_file, 'rb') as video:
                query.message.reply_video(video, caption='Here is your video!')
        except Exception as e:
            query.message.reply_text(f'Error: {str(e)}')

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    main()
