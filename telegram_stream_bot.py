#!/usr/bin/env python3
"""
Telegram Bot for generating streaming download links.
This bot receives files from users and generates streaming links
without storing the files on the server.
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from flask import Flask, Response, stream_with_context, send_from_directory
import asyncio
import threading
import httpx
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Configuration - Replace with your actual values
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SERVER_DOMAIN = os.getenv("SERVER_DOMAIN", "http://localhost:5000")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# Store file info temporarily (in production, use Redis or similar)
file_cache = {}


def get_file_size_str(file_size: int) -> str:
    """Convert file size to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if file_size < 1024.0:
            return f"{file_size:.2f} {unit}"
        file_size /= 1024.0
    return f"{file_size:.2f} PB"


def get_file_type_str(file_type: str) -> str:
    """Get human readable file type."""
    type_mapping = {
        "document": "سند/فایل",
        "video": "ویدیو",
        "audio": "صدا",
        "voice": "پیام صوتی",
        "photo": "عکس",
        "animation": "انیمیشن",
        "video_note": "یادداشت ویدیویی",
    }
    return type_mapping.get(file_type, "نامشخص")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    welcome_message = (
        "👋 سلام! به ربات تولید لینک دانلود استریم خوش آمدید.\n\n"
        "📁 هر فایلی که می‌خواهید را برای من ارسال کنید تا لینک دانلود استریم آن را برایتان تولید کنم.\n\n"
        "✨ ویژگی‌ها:\n"
        "• پشتیبانی از تمام فرمت‌های فایل\n"
        "• بدون ذخیره فایل روی سرور\n"
        "• دانلود مستقیم از سرورهای تلگرام"
    )
    await update.message.reply_text(welcome_message)


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming files."""
    # Determine file type and get file object
    file_obj = None
    file_type = None
    file_name = None
    file_size = 0
    
    if update.message.document:
        file_obj = update.message.document
        file_type = "document"
        file_name = file_obj.file_name or "unknown_file"
        file_size = file_obj.file_size
    elif update.message.video:
        file_obj = update.message.video
        file_type = "video"
        file_name = file_obj.file_name or "video.mp4"
        file_size = file_obj.file_size
    elif update.message.audio:
        file_obj = update.message.audio
        file_type = "audio"
        file_name = file_obj.file_name or "audio.mp3"
        file_size = file_obj.file_size
    elif update.message.voice:
        file_obj = update.message.voice
        file_type = "voice"
        file_name = "voice.ogg"
        file_size = file_obj.file_size
    elif update.message.photo:
        # Get the largest photo
        file_obj = update.message.photo[-1]
        file_type = "photo"
        file_name = "photo.jpg"
        file_size = file_obj.file_size
    elif update.message.animation:
        file_obj = update.message.animation
        file_type = "animation"
        file_name = file_obj.file_name or "animation.gif"
        file_size = file_obj.file_size
    elif update.message.video_note:
        file_obj = update.message.video_note
        file_type = "video_note"
        file_name = "video_note.mp4"
        file_size = file_obj.file_size
    
    if not file_obj:
        await update.message.reply_text("❌ فایل نامعتبر است.")
        return
    
    # Get file ID and store in cache
    file_id = file_obj.file_id
    unique_id = f"{update.effective_user.id}_{file_id}"
    
    file_cache[unique_id] = {
        "file_id": file_id,
        "file_name": file_name,
        "file_type": file_type,
        "file_size": file_size,
        "user_id": update.effective_user.id,
    }
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("🔗 تولید لینک دانلود", callback_data=f"generate:{unique_id}"),
            InlineKeyboardButton("❌ لغو", callback_data=f"cancel:{unique_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Prepare message
    file_type_str = get_file_type_str(file_type)
    file_size_str = get_file_size_str(file_size)
    
    message_text = (
        f"📄 **مشخصات فایل:**\n\n"
        f"📝 نام فایل: `{file_name}`\n"
        f"📊 نوع فایل: {file_type_str}\n"
        f"💾 حجم فایل: {file_size_str}\n\n"
        f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, unique_id = data.split(":", 1)
    
    if action == "cancel":
        # Remove from cache
        if unique_id in file_cache:
            del file_cache[unique_id]
        await query.edit_message_text("❌ عملیات لغو شد.")
    
    elif action == "generate":
        if unique_id not in file_cache:
            await query.edit_message_text("❌ اطلاعات فایل یافت نشد. لطفاً فایل را دوباره ارسال کنید.")
            return
        
        file_info = file_cache[unique_id]
        
        # Generate streaming link
        stream_link = f"{SERVER_DOMAIN}/stream/{unique_id}/{file_info['file_name']}"
        
        # Generate interstitial page link (with ads and timer)
        encoded_link = quote(stream_link, safe='')
        encoded_name = quote(file_info['file_name'], safe='')
        file_size_str = get_file_size_str(file_info['file_size'])
        interstitial_link = f"{SERVER_DOMAIN}/download?link={encoded_link}&name={encoded_name}&size={file_size_str}"
        
        # Create message with link
        link_message = (
            f"✅ **لینک دانلود استریم آماده شد!**\n\n"
            f"📝 نام فایل: `{file_info['file_name']}`\n"
            f"💾 حجم: {file_size_str}\n\n"
            f"🔗 **لینک دانلود:**\n`{interstitial_link}`\n\n"
            f"⚠️ نکته: برای دریافت فایل، روی لینک کلیک کنید و پس از مشاهده تبلیغات، دکمه دانلود را بزنید."
        )
        
        # Create inline keyboard with link button
        keyboard = [
            [InlineKeyboardButton("📥 دریافت لینک دانلود", url=interstitial_link)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(link_message, reply_markup=reply_markup, parse_mode="Markdown")


def create_flask_app(bot_app: Application) -> Flask:
    """Create Flask app for serving streaming files."""
    flask_app = Flask(__name__)
    
    # Get the directory where the script is located
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ad-page', 'dist')
    
    @flask_app.route("/download")
    def download_page():
        """Serve the interstitial download page with ads and timer."""
        return send_from_directory(BASE_DIR, 'index.html')

    @flask_app.route("/assets/<path:filename>")
    def serve_assets(filename):
        """Serve static assets for the React app."""
        return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)

    @flask_app.route("/favicon.svg")
    def serve_favicon():
        """Serve favicon for the React app."""
        return send_from_directory(BASE_DIR, 'favicon.svg')

    @flask_app.route("/icons.svg")
    def serve_icons():
        """Serve icons for the React app."""
        return send_from_directory(BASE_DIR, 'icons.svg')
    
    @flask_app.route("/stream/<unique_id>/<filename>")
    def stream_file(unique_id: str, filename: str):
        """Stream file from Telegram servers."""
        if unique_id not in file_cache:
            return "File not found", 404
        
        file_info = file_cache[unique_id]
        file_id = file_info["file_id"]
        
        try:
            # Get file from Telegram
            bot = bot_app.bot
            file = asyncio.run(bot.get_file(file_id))
            
            # Get the file URL
            file_url = file.file_path
            
            logger.info(f"Streaming file: {filename} from {file_url}")
            
            def generate():
                with httpx.stream("GET", file_url, follow_redirects=True) as response:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        yield chunk
            
            headers = {
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/octet-stream",
                "Accept-Ranges": "bytes",
            }
            
            return Response(stream_with_context(generate()), headers=headers)
        
        except Exception as e:
            logger.error(f"Error streaming file: {e}")
            return "Error streaming file", 500
    
    return flask_app


def run_flask(flask_app: Flask):
    """Run Flask app in a separate thread."""
    flask_app.run(host="0.0.0.0", port=FLASK_PORT, threaded=True)


def main() -> None:
    """Start the bot."""
    # Create Telegram bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create Flask app for streaming
    flask_app = create_flask_app(application)
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, args=(flask_app,), daemon=True)
    flask_thread.start()
    logger.info(f"Flask server started on port {FLASK_PORT}")
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_file))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
