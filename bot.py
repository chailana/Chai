import logging
import asyncio
import aiohttp
import os
import time
from datetime import datetime
from pyrogram import Client, filters, enums
from dotenv import load_dotenv
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image

# Load environment variables from .env file
load_dotenv()

# Define your bot token here
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize the bot
bot = Client("my_bot", bot_token=TOKEN)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

async def ddl_call_back(bot, update):
    logger.info(update)
    cb_data = update.data
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("=")
    youtube_dl_url = update.message.reply_to_message.text
    custom_file_name = os.path.basename(youtube_dl_url)
    
    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        youtube_dl_url = url_parts[0]
        custom_file_name = url_parts[1].strip()
    
    description = "Custom caption here"  # Replace with your caption logic
    start = datetime.now()

    # Show quality options
    await update.message.edit_caption(caption="Choose the quality option:")
    quality_buttons = [
        [InlineKeyboardButton("480p", callback_data="quality_480p"),
         InlineKeyboardButton("720p", callback_data="quality_720p"),
         InlineKeyboardButton("1080p", callback_data="quality_1080p")]
    ]
    await bot.send_message(
        chat_id=update.message.chat.id,
        text="Select Quality:",
        reply_markup=InlineKeyboardMarkup(quality_buttons)
    )
    
    tmp_directory_for_each_user = "DOWNLOAD_LOCATION"  # Update with your download location
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    
    download_directory = os.path.join(tmp_directory_for_each_user, custom_file_name)
    async with aiohttp.ClientSession() as session:
        c_time = time.time()
        try:
            await download_coroutine(
                bot,
                session,
                youtube_dl_url,
                download_directory,
                update.message.chat.id,
                update.message.id,
                c_time
            )
        except asyncio.TimeoutError:
            await bot.edit_message_text(
                text="Download is too slow. Please try again.",
                chat_id=update.message.chat.id,
                message_id=update.message.id
            )
            return False

    if os.path.exists(download_directory):
        end_one = datetime.now()
        await update.message.edit_caption(
            caption="Starting upload...",
            parse_mode=enums.ParseMode.HTML
        )
        file_size = os.stat(download_directory).st_size
        
        if file_size > 52428800:  # Telegram max file size (50MB)
            await update.message.edit_caption(
                caption="File size exceeds Telegram limit.",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            start_time = time.time()
            await update.message.reply_document(
                document=download_directory,
                caption=description,
                parse_mode=enums.ParseMode.HTML,
                progress=progress_for_pyrogram,
                progress_args=(
                    "Uploading...",
                    update.message,
                    start_time
                )
            )
            
            end_two = datetime.now()
            await update.message.edit_caption(
                caption=f"Upload complete in {end_two - start_one} seconds.",
                parse_mode=enums.ParseMode.HTML
            )
    else:
        await update.message.edit_caption(
            caption="No valid format found. Please check the link.",
            parse_mode=enums.ParseMode.HTML
        )

async def download_coroutine(bot, session, url, file_name, chat_id, message_id, start):
    downloaded = 0
    display_message = ""
    async with session.get(url, timeout=30) as response:
        total_length = int(response.headers["Content-Length"])
        await bot.edit_message_text(
            chat_id,
            message_id,
            text=f"Initiating Download\n\n🔗 URL: `{url}`\n🗂️ Size: {total_length} bytes"
        )
        with open(file_name, "wb") as f_handle:
            while True:
                chunk = await response.content.read(1024)
                if not chunk:
                    break
                f_handle.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                diff = now - start
                if round(diff % 5.00) == 0 or downloaded == total_length:
                    percentage = downloaded * 100 / total_length
                    current_message = f"**Download Status**\n🔗 URL: `{url}`\n🗂️ Size: {total_length} bytes\n✅ Done: {downloaded} bytes"
                    if current_message != display_message:
                        await bot.edit_message_text(
                            chat_id,
                            message_id,
                            text=current_message
                        )
                        display_message = current_message
        return await response.release()
