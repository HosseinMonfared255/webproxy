"""
Telegram service for handling bot operations and file streaming.
"""
import logging
from typing import Optional, Dict, Any, Tuple

import httpx
from telegram import Bot

from config import BOT_TOKEN

logger = logging.getLogger(__name__)


def get_file_size_str(file_size: int) -> str:
    """Convert file size to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if file_size < 1024.0:
            return f"{file_size:.2f} {unit}"
        file_size /= 1024.0
    return f"{file_size:.2f} PB"


def get_file_type_str(file_type: str) -> str:
    """Get human readable file type in Persian."""
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


def extract_file_info(update_message) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Extract file information from a Telegram message.
    Returns (file_info_dict, error_message).
    """
    file_obj = None
    file_type = None
    file_name = None
    file_size = 0
    mime_type = None
    
    if update_message.document:
        file_obj = update_message.document
        file_type = "document"
        file_name = file_obj.file_name or "unknown_file"
        file_size = file_obj.file_size
        mime_type = file_obj.mime_type
    elif update_message.video:
        file_obj = update_message.video
        file_type = "video"
        file_name = file_obj.file_name or "video.mp4"
        file_size = file_obj.file_size
        mime_type = file_obj.mime_type
    elif update_message.audio:
        file_obj = update_message.audio
        file_type = "audio"
        file_name = file_obj.file_name or "audio.mp3"
        file_size = file_obj.file_size
        mime_type = file_obj.mime_type
    elif update_message.voice:
        file_obj = update_message.voice
        file_type = "voice"
        file_name = "voice.ogg"
        file_size = file_obj.file_size
        mime_type = file_obj.mime_type
    elif update_message.photo:
        # Get the largest photo
        file_obj = update_message.photo[-1]
        file_type = "photo"
        file_name = "photo.jpg"
        file_size = file_obj.file_size
        mime_type = "image/jpeg"
    elif update_message.animation:
        file_obj = update_message.animation
        file_type = "animation"
        file_name = file_obj.file_name or "animation.gif"
        file_size = file_obj.file_size
        mime_type = file_obj.mime_type
    elif update_message.video_note:
        file_obj = update_message.video_note
        file_type = "video_note"
        file_name = "video_note.mp4"
        file_size = file_obj.file_size
        mime_type = "video/mp4"
    
    if not file_obj:
        return None, "❌ فایل نامعتبر است."
    
    return {
        "file_id": file_obj.file_id,
        "file_name": file_name,
        "file_type": file_type,
        "file_size": file_size,
        "mime_type": mime_type,
    }, None


async def get_telegram_file_url(bot: Bot, file_id: str) -> Optional[str]:
    """
    Get the direct download URL for a file from Telegram.
    """
    try:
        file = await bot.get_file(file_id)
        return file.file_path
    except Exception as e:
        logger.error(f"Error getting file URL from Telegram: {e}")
        return None


async def stream_file_from_telegram(file_url: str, range_header: Optional[str] = None):
    """
    Async generator that streams file content from Telegram.
    Supports range requests for resume capability.
    """
    headers = {}
    if range_header:
        headers["Range"] = range_header
    
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", file_url, headers=headers, follow_redirects=True) as response:
            async for chunk in response.aiter_bytes(chunk_size=8192):
                yield chunk
