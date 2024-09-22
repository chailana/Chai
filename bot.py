import os
import datetime
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import motor.motor_asyncio

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
DUMP_CHANNEL_ID = -1002247666039  # Replace with your channel ID

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id):
        return dict(
            id=id,
            join_date=datetime.date.today().isoformat(),
            apply_caption=True,
            upload_as_doc=False,
            thumbnail=None,
            caption=None
        )

    async def add_user(self, id):
        user = self.new_user(id)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return bool(user)

    async def get_video_formats(self, url):
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url)
                return info_dict['formats']  # Return available formats without downloading
        except Exception as e:
            print(f"Error retrieving video formats: {e}")
            return None

# Initialize the database connection
db = Database(os.getenv("DATABASE_URL"), "UploadLinkToFileBot")

# Initialize the bot with API ID, API Hash, and Bot Token
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def send_welcome(client, message):
    if not await db.is_user_exist(message.chat.id):
        await db.add_user(message.chat.id)
    
    await client.send_message(message.chat.id, "Welcome! Send me a direct video link or a URL from supported websites (like YouTube) to download.\nUse /help for more commands.")

@bot.on_message(filters.command("help"))
async def send_help(client, message):
    help_text = (
        "/start - Welcome message\n"
        "/help - List of commands\n"
        "/setformat <format> - Set your preferred download format (e.g., mp4)\n"
        "/resetformat - Reset your preferred format to default\n"
        "Just send a video URL to download it."
    )
    await client.send_message(message.chat.id, help_text)

@bot.on_message(filters.text)
async def handle_message(client, message):
    url = message.text.strip()
    if is_valid_url(url):
        await client.send_message(message.chat.id, f"Downloading from {url}...")
        
        formats = await db.get_video_formats(url)
        
        if formats:
            keyboard = []
            seen_formats = set()  # To avoid duplicates
            
            for fmt in formats:
                if 'height' in fmt and fmt['format_id'] not in seen_formats:
                    button_label = f"{fmt.get('format_note', 'No Note')} ({fmt['height']}p)"
                    button = InlineKeyboardButton(button_label, callback_data=f"quality_{fmt['format_id']}")
                    keyboard.append([button])
                    seen_formats.add(fmt['format_id'])  # Mark this format as seen
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await client.send_message(message.chat.id, "Available quality options:", reply_markup=reply_markup)
        else:
            await client.send_message(message.chat.id, "Failed to retrieve video formats.")
    else:
        await client.send_message(message.chat.id, "Please send a valid URL.")

@bot.on_callback_query(filters.regex(r"quality_"))
async def handle_quality_selection(client, callback_query):
    user_id = callback_query.from_user.id
    selected_format_id = callback_query.data.split("_")[1]

    await callback_query.answer()  # Acknowledge the callback

    url = callback_query.message.reply_to_message.text.strip()
    
    await download_video(user_id, url, selected_format_id)

async def download_video(user_id, url, format_id):
    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title)s.%(ext)s',
         'progress_hooks': [lambda d: progress_hook(d,user_id)],
     }
    
    try:
         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
             info_dict = ydl.extract_info(url , download=True)
             final_video_file= ydl.prepare_filename(info_dict)

             await bot.send_video(DUMP_CHANNEL_ID , video=final_video_file)  # Send to dump channel
             await bot.send_video(user_id , video=final_video_file)  # Send to user
            
             os.remove(final_video_file)  # Clean up the video file after sending
            
    except Exception as e:
         print(f"Error downloading file: {e}")

def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")

def progress_hook(d,user_id):
     if d['status'] == 'downloading':
         percent= d['downloaded_bytes'] / d['total_bytes'] * 100 
         bot.send_message(user_id , f"Download progress: {percent:.2f}%")

if __name__ == '__main__':
     bot.run()
