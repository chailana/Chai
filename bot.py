import logging
import asyncio
import aiohttp
import os
import time
from datetime import datetime
from pyrogram import enums
from plugins.config import Config
from plugins.script import Translation
from plugins.thumbnail import *
from plugins.database.database import db
from plugins.functions.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from pyrogram import Client, filters
from pyrogram import Client

# Define your bot token here
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

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
    thumb_image_path = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".jpg"
    youtube_dl_url = update.message.reply_to_message.text
    custom_file_name = os.path.basename(youtube_dl_url)
    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        youtube_dl_url = url_parts[0]
        custom_file_name = url_parts[1].strip()
    description = Translation.CUSTOM_CAPTION_UL_FILE
    start = datetime.now()
    
    # Show quality options
    await update.message.edit_caption(caption="Choose the quality option:")
    quality_buttons = [
        [("480p", "quality_480p"), ("720p", "quality_720p"), ("1080p", "quality_1080p")]
    ]
    await bot.send_message(
        chat_id=update.message.chat.id,
        text="Select Quality:",
        reply_markup=quality_buttons
    )
    
    tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    download_directory = tmp_directory_for_each_user + "/" + custom_file_name
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
                text=Translation.SLOW_URL_DECED,
                chat_id=update.message.chat.id,
                message_id=update.message.id
            )
            return False

    if os.path.exists(download_directory):
        end_one = datetime.now()
        await update.message.edit_caption(
            caption=Translation.UPLOAD_START,
            parse_mode=enums.ParseMode.HTML
        )
        file_size = os.stat(download_directory).st_size
        if file_size > Config.TG_MAX_FILE_SIZE:
            await update.message.edit_caption(
                caption=Translation.RCHD_TG_API_LIMIT,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            start_time = time.time()
            if not (await db.get_upload_as_doc(update.from_user.id)):
                thumbnail = await Gthumb01(bot, update)
                await update.message.reply_document(
                    document=download_directory,
                    thumb=thumbnail,
                    caption=description,
                    parse_mode=enums.ParseMode.HTML,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            else:
                width, height, duration = await Mdata01(download_directory)
                thumb_image_path = await Gthumb02(bot, update, duration, download_directory)
                await update.message.reply_video(
                    video=download_directory,
                    caption=description,
                    duration=duration,
                    width=width,
                    height=height,
                    supports_streaming=True,
                    parse_mode=enums.ParseMode.HTML,
                    thumb=thumb_image_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            
            end_two = datetime.now()
            await update.message.edit_caption(
                caption=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(
                    (end_one - start).seconds, (end_two - end_one).seconds
                ),
                parse_mode=enums.ParseMode.HTML
            )

    else:
        await update.message.edit_caption(
            caption=Translation.NO_VOID_FORMAT_FOUND.format("Incorrect Link"),
            parse_mode=enums.ParseMode.HTML
        )


async def download_coroutine(bot, session, url, file_name, chat_id, message_id, start):
    downloaded = 0
    display_message = ""
    async with session.get(url, timeout=Config.PROCESS_MAX_TIMEOUT) as response:
        total_length = int(response.headers["Content-Length"])
        await bot.edit_message_text(
            chat_id,
            message_id,
            text=f"Initiating Download\n\n🔗 URL: `{url}`\n🗂️ Size: {humanbytes(total_length)}"
        )
        with open(file_name, "wb") as f_handle:
            while True:
                chunk = await response.content.read(Config.CHUNK_SIZE)
                if not chunk:
                    break
                f_handle.write(chunk)
                downloaded += Config.CHUNK_SIZE
                now = time.time()
                diff = now - start
                if round(diff % 5.00) == 0 or downloaded == total_length:
                    percentage = downloaded * 100 / total_length
                    speed = downloaded / diff
                    elapsed_time = round(diff) * 1000
                    time_to_completion = round((total_length - downloaded) / speed) * 1000
                    estimated_total_time = elapsed_time + time_to_completion
                    current_message = f"""**Download Status**\n🔗 URL: `{url}`\n🗂️ Size: {humanbytes(total_length)}\n✅ Done: {humanbytes(downloaded)}\n⏱️ ETA: {TimeFormatter(estimated_total_time)}"""
                    if current_message != display_message:
                        await bot.edit_message_text(
                            chat_id,
                            message_id,
                            text=current_message
                        )
                        display_message = current_message
        return await response.release()
