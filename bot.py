from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

app = Client("my_bot", api_id="your_api_id", api_hash="your_api_hash", bot_token="your_bot_token")

@app.on_message()
async def handle_link(client, message):
    # Define the buttons with valid callback data
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Quality 720p", callback_data="720p")],
        [InlineKeyboardButton("Quality 1080p", callback_data="1080p")]
    ])
    
    # Send the message with the buttons
    await message.reply_text("Choose the video quality:", reply_markup=markup)

@app.on_callback_query()
async def handle_query(client, callback_query: CallbackQuery):
    # Handle the callback query
    callback_data = callback_query.data
    await callback_query.answer(f"You selected {callback_data}")

if __name__ == "__main__":
    app.run()
