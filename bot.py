import logging
import os
import requests
from moviepy.editor import VideoFileClip
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from pytube import YouTube

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the Download Bot! 🎉\n"
        "Send me a URL to download files like videos, PDFs, etc.\n"
        "/help for more information. 📚"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Here are the commands you can use:\n"
        "/start - Start the bot\n"
        "/help - Show this message\n"
        "Just send a URL to download files! 🚀"
    )

async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    context.user_data['last_url'] = url  # Save URL for later use
    await update.message.reply_text("Downloading... ⏳")

    if url.endswith(('.mp4', '.mkv', 'youtube.com')):
        # Handle YouTube links
        if 'youtube.com' in url or 'youtu.be' in url:
            yt = YouTube(url)
            video_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
            qualities = [stream.resolution for stream in video_streams]
            keyboard = [[InlineKeyboardButton(q, callback_data=q) for q in qualities]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Choose quality:", reply_markup=reply_markup)
            return
        
        # Downloading other video types directly
        response = requests.get(url, stream=True)
        file_name = url.split("/")[-1]
        with open(file_name, 'wb') as f:
            total_length = response.headers.get('content-length')
            if total_length is None:
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    percent = int(100 * dl / total_length)
                    await update.message.reply_text(f"Download progress: {percent}%")
        
        # Extract thumbnail
        clip = VideoFileClip(file_name)
        thumbnail_name = f"{file_name}.jpg"
        clip.save_frame(thumbnail_name, t=1)  # Save thumbnail at 1 second
        await update.message.reply_photo(photo=open(thumbnail_name, 'rb'), caption="Download complete! 🎉")

    elif url.endswith('.pdf'):
        response = requests.get(url, stream=True)
        file_name = url.split("/")[-1]
        with open(file_name, 'wb') as f:
            f.write(response.content)
        
        await update.message.reply_text("Download complete! 🎉")
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_name, 'rb'))

    else:
        await update.message.reply_text("Unsupported file type. Please send a video or PDF.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    quality = query.data
    url = context.user_data.get('last_url')

    await query.message.reply_text(f"Downloading video in {quality}... ⏳")
    
    yt = YouTube(url)
    video_stream = yt.streams.filter(res=quality, file_extension='mp4').first()
    
    if video_stream:
        # Download video with progress
        video_stream.download(output_path='downloads')
        await query.message.reply_text("Download complete! 🎉")
        await context.bot.send_video(chat_id=query.message.chat_id, video=open(f'downloads/{video_stream.default_filename}', 'rb'))
    else:
        await query.message.reply_text("Quality not available.")

def main() -> None:
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN")

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help_command))
    updater.dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_file))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_callback))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
