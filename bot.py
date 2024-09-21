import logging
import os
import requests
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Use /download <URL> <quality> to download videos. Available qualities: best, worst.')

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text('Please provide a URL and quality (best or worst).')
        return

    url = context.args[0]
    quality = context.args[1]
    title, size, thumbnail_url = get_video_info(url)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if quality == 'best' else 'worst',
        'outtmpl': f'{title}.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'progress_hooks': [lambda d: update_progress(update, d)],
    }

    await update.message.reply_text("📤 Uᴘʟᴏᴀᴅɪɴɢ Pʟᴇᴀsᴇ Wᴀɪᴛ\n\n[░░░░░░░░░░░░░░░░░░░░]")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'No Title')

        # Download the thumbnail
        thumbnail_response = requests.get(thumbnail_url)
        thumbnail_path = f"{title}_thumbnail.jpg"
        with open(thumbnail_path, 'wb') as f:
            f.write(thumbnail_response.content)

        # Send the video
        video_path = f"{title}.mp4"
        await context.bot.send_video(chat_id=update.effective_chat.id, video=open(video_path, 'rb'),
                                      caption=f'Title: {title}\nSize: {size}')

    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')
    finally:
        # Clean up downloaded files
        try:
            os.remove(video_path)
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
            asyncio.run(update.message.reply_text(progress_message))

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
    application = ApplicationBuilder().token('7513058089:AAHAPtJbHEPbRMbV8rv-gAZ8KVL0ykAM2pE').build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('download', download_and_send))

    application.run_polling()

if __name__ == '__main__':
    main()
