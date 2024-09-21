import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import asyncio

# Set your bot token here
BOT_TOKEN = '7513058089:AAHAPtJbHEPbRMbV8rv-gAZ8KVL0ykAM2pE'  # Replace with your actual bot token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Send me a video URL!')

async def get_formats(url: str):
    with yt_dlp.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        available_formats = {f['format_id']: f['resolution'] for f in formats if 'resolution' in f}
        return available_formats

def format_buttons(format_options):
    buttons = [[InlineKeyboardButton(text=resolution, callback_data=format_id) for format_id, resolution in format_options.items()]]
    return InlineKeyboardMarkup(buttons)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text('Fetching available formats...')
    
    try:
        formats = await get_formats(url)
        if formats:
            reply_markup = format_buttons(formats)
            await update.message.reply_text('Select a video format:', reply_markup=reply_markup)
            context.user_data['video_url'] = url  # Store URL for later use
        else:
            await update.message.reply_text('No formats available.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

async def download_video(url: str, format_id: str):
    ydl_opts = {
        'format': format_id,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_title = info_dict.get('title', None)
        return f'downloads/{video_title}.{info_dict["ext"]}'

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    format_id = query.data
    url = context.user_data.get('video_url')

    if url:
        await query.message.edit_text('Downloading your video...')
        try:
            video_file = await download_video(url, format_id)
            with open(video_file, 'rb') as video:
                await query.message.reply_video(video, caption='Here is your video!')
        except Exception as e:
            await query.message.reply_text(f'Error: {str(e)}')

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    await app.run_polling()

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)  # Create downloads directory
    asyncio.run(main())  # Run the main function directly
