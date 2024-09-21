import logging
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yt_dlp

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Use /download <URL> to download videos.')

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text('Please provide a URL.')
        return

    url = context.args[0]
    title, size, thumbnail_url = get_video_info(url)

    # Download the video
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{title}.%(ext)s'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Download the thumbnail
        thumbnail_response = requests.get(thumbnail_url)
        thumbnail_path = f"{title}_thumbnail.jpg"
        with open(thumbnail_path, 'wb') as f:
            f.write(thumbnail_response.content)

        # Send the video
        await context.bot.send_video(chat_id=update.effective_chat.id, video=open(f"{title}.mp4", 'rb'),
                                      caption=f'Title: {title}\nSize: {size}')

        # Send the thumbnail
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(thumbnail_path, 'rb'))

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')
    finally:
        # Clean up downloaded files
        try:
            os.remove(f"{title}.mp4")
            os.remove(thumbnail_path)
        except:
            pass

def get_video_info(url):
    ydl_opts = {
        'format': 'best',
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
    application = ApplicationBuilder().token('7513058089:AAHAPtJbHEPbRMbV8rv-gAZ8KVL0ykAM2pE').build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('download', download_and_send))

    application.run_polling()

if __name__ == '__main__':
    main()
