import logging
import os
import requests
from moviepy.editor import VideoFileClip
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from pytube import YouTube

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Create downloads directory if it doesn't exist
os.makedirs('downloads', exist_ok=True)

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the Download Bot! 🎉\n"
        "Send me a URL to download files like videos, PDFs, etc.\n"
        "/help for more information. 📚"
    )

# /help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Here are the commands you can use:\n"
        "/start - Start the bot\n"
        "/help - Show this message\n"
        "Just send a URL to download files! 🚀"
    )

# File download handler
async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    context.user_data['last_url'] = url  # Save URL for later use
    await update.message.reply_text("Downloading... ⏳")

    try:
        if url.endswith(('.mp4', '.mkv', 'youtube.com', 'youtu.be')):
            if 'youtube.com' in url or 'youtu.be' in url:
                yt = YouTube(url)
                video_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
                qualities = [stream.resolution for stream in video_streams]
                keyboard = [[InlineKeyboardButton(q, callback_data=q) for q in qualities]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Choose quality:", reply_markup=reply_markup)
                return
            
            # Handle direct video file download
            response = requests.get(url, stream=True)
            file_name = os.path.join('downloads', url.split("/")[-1])
            total_length = response.headers.get('content-length')
            with open(file_name, 'wb') as f:
                if total_length is None:
                    f.write(response.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    message = await update.message.reply_text("Download progress: 0%")
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        percent = int(100 * dl / total_length)
                        await message.edit_text(f"Download progress: {percent}%")
            
            # Generate and send video thumbnail
            clip = VideoFileClip(file_name)
            thumbnail_name = f"{file_name}.jpg"
            clip.save_frame(thumbnail_name, t=1)
            await update.message.reply_photo(photo=open(thumbnail_name, 'rb'), caption="Download complete! 🎉")
            os.remove(thumbnail_name)

        elif url.endswith('.pdf'):
            # Handle PDF download
            response = requests.get(url, stream=True)
            file_name = os.path.join('downloads', url.split("/")[-1])
            with open(file_name, 'wb') as f:
                f.write(response.content)
            
            await update.message.reply_text("Download complete! 🎉")
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_name, 'rb'))

        else:
            await update.message.reply_text("Unsupported file type. Please send a video or PDF.")
    
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

# Callback handler for video quality selection
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    quality = query.data
    url = context.user_data.get('last_url')

    await query.message.reply_text(f"Downloading video in {quality}... ⏳")
    
    try:
        yt = YouTube(url)
        video_stream = yt.streams.filter(res=quality, file_extension='mp4').first()
        
        if video_stream:
            file_path = os.path.join('downloads', video_stream.default_filename)
            video_stream.download(output_path='downloads')
            await query.message.reply_text("Download complete! 🎉")
            await context.bot.send_video(chat_id=query.message.chat_id, video=open(file_path, 'rb'))
        else:
            await query.message.reply_text("Quality not available.")
    
    except Exception as e:
        await query.message.reply_text(f"An error occurred: {str(e)}")

# Main function to start the bot
def main() -> None:
    application = Application.builder().token("7513058089:AAHAPtJbHEPbRMbV8rv-gAZ8KVL0ykAM2pE").build()

    # Handlers for commands and messages
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_file))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
