#!/usr/bin/env python3
"""
Telegram Bot for generating streaming download links.
This bot receives files from users and generates streaming links
without storing the files on the server.

Migrated from Flask to FastAPI/Uvicorn.
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
import asyncio
import httpx
from urllib.parse import quote

from config import BOT_TOKEN, SERVER_DOMAIN, SERVER_PORT
from database import save_file_metadata, delete_file_metadata
from telegram_service import extract_file_info, get_file_size_str, get_file_type_str
from fastapi_app import app, set_bot_instance

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


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
    # Extract file info using the service function
    file_info, error = extract_file_info(update.message)
    
    if not file_info:
        await update.message.reply_text(error or "❌ فایل نامعتبر است.")
        return
    
    # Generate unique ID for this file
    user_id = update.effective_user.id
    file_id = file_info["file_id"]
    unique_id = f"{user_id}_{file_id}"
    
    # Save file metadata to database
    success = save_file_metadata(
        unique_id=unique_id,
        file_id=file_id,
        file_name=file_info["file_name"],
        file_type=file_info["file_type"],
        file_size=file_info["file_size"],
        user_id=user_id,
        mime_type=file_info.get("mime_type"),
    )
    
    if not success:
        await update.message.reply_text("❌ خطا در ذخیره اطلاعات فایل. لطفاً دوباره تلاش کنید.")
        return
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("🔗 تولید لینک دانلود", callback_data=f"generate:{unique_id}"),
            InlineKeyboardButton("❌ لغو", callback_data=f"cancel:{unique_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Prepare message
    file_type_str = get_file_type_str(file_info["file_type"])
    file_size_str = get_file_size_str(file_info["file_size"])
    
    message_text = (
        f"📄 **مشخصات فایل:**\n\n"
        f"📝 نام فایل: `{file_info['file_name']}`\n"
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
        # Delete from database
        delete_file_metadata(unique_id)
        await query.edit_message_text("❌ عملیات لغو شد.")
    
    elif action == "generate":
        # Call FastAPI endpoint to generate token
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"http://localhost:{SERVER_PORT}/generate-token/{unique_id}"
                )
                response.raise_for_status()
                result = response.json()
                
                interstitial_link = result["interstitial_url"]
                
                # Get file info for message
                from database import get_file_metadata
                file_info = get_file_metadata(unique_id)
                
                if not file_info:
                    await query.edit_message_text("❌ اطلاعات فایل یافت نشد. لطفاً فایل را دوباره ارسال کنید.")
                    return
                
                file_size_str = get_file_size_str(file_info["file_size"])
                
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
                
            except httpx.HTTPError as e:
                logger.error(f"Error generating token: {e}")
                await query.edit_message_text("❌ خطا در تولید لینک. لطفاً دوباره تلاش کنید.")


async def run_bot():
    """Start the bot."""
    # Create Telegram bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Set bot instance for FastAPI app
    set_bot_instance(application.bot)
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_file))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logger.info("Starting bot...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point - runs both FastAPI and Telegram bot."""
    import uvicorn
    
    # Run FastAPI and bot concurrently
    async def run_all():
        # Start FastAPI server using asyncio.to_thread to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Run FastAPI in a thread pool executor
        fastapi_task = loop.run_in_executor(
            None,
            lambda: uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT, log_level="info")
        )
        
        # Give FastAPI a moment to start
        await asyncio.sleep(2)
        
        # Start the bot
        bot_task = run_bot()
        
        # Wait for both to complete (bot will run until stopped)
        await bot_task
    
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()
