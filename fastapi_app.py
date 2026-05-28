"""
FastAPI application for serving streaming files and the ad-page frontend.
"""
import logging
import os
from datetime import datetime
from typing import Optional
from urllib.parse import quote, unquote

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from telegram import Bot

from config import SERVER_DOMAIN, AD_PAGE_DIST, BOT_TOKEN
from database import (
    save_file_metadata,
    generate_secure_token,
    validate_token,
    delete_file_metadata,
    cleanup_expired_tokens,
)
from telegram_service import get_telegram_file_url, stream_file_from_telegram

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Telegram Stream Bot API")

# Store bot instance for file URL retrieval
bot_instance: Optional[Bot] = None


def set_bot_instance(bot: Bot):
    """Set the Telegram bot instance."""
    global bot_instance
    bot_instance = bot


def get_bot() -> Bot:
    """Get the Telegram bot instance."""
    if bot_instance is None:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    return bot_instance


# Mount static files for the React ad-page
if os.path.exists(AD_PAGE_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(AD_PAGE_DIST, "assets")), name="assets")


@app.on_event("startup")
async def startup_event():
    """Clean up expired tokens on startup."""
    cleanup_expired_tokens()
    logger.info("FastAPI server started")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Telegram Stream Bot API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/register-file/{unique_id}")
async def register_file(
    unique_id: str,
    file_id: str = Query(...),
    file_name: str = Query(...),
    file_type: str = Query(...),
    file_size: int = Query(...),
    user_id: int = Query(...),
    mime_type: Optional[str] = Query(None),
):
    """
    Register a file in the database.
    Called by the Telegram bot when a user sends a file.
    """
    try:
        success = save_file_metadata(
            unique_id=unique_id,
            file_id=file_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            user_id=user_id,
            mime_type=mime_type,
        )
        if success:
            return {"status": "success", "unique_id": unique_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to save file metadata")
    except Exception as e:
        logger.error(f"Error registering file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cancel-file/{unique_id}")
async def cancel_file(unique_id: str):
    """
    Cancel a file operation and delete metadata.
    Called when user cancels the download.
    """
    try:
        success = delete_file_metadata(unique_id)
        if success:
            return {"status": "cancelled", "unique_id": unique_id}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error cancelling file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generate-token/{unique_id}")
async def generate_token(unique_id: str):
    """
    Generate a secure download token for a file.
    Returns the token and the interstitial page URL.
    """
    try:
        token = generate_secure_token(unique_id)
        interstitial_url = f"{SERVER_DOMAIN}/download?token={token}"
        return {
            "status": "success",
            "token": token,
            "interstitial_url": interstitial_url,
        }
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download", response_class=HTMLResponse)
async def download_page(token: str = Query(...)):
    """
    Serve the interstitial download page with ads and timer.
    Validates the token and passes file info to the frontend.
    """
    # Validate token
    file_info = validate_token(token)
    if not file_info:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Read the index.html file
    index_path = os.path.join(AD_PAGE_DIST, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=500, detail="Frontend not built. Run: cd ad-page && npm run build")
    
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Inject file info into the page via JavaScript
    file_data = {
        "token": token,
        "file_name": file_info["file_name"],
        "file_size": file_info["file_size"],
        "file_type": file_info["file_type"],
    }
    
    # Add script to inject file data
    inject_script = f"""
    <script>
        window.FILE_DATA = {str(file_data).replace("'", '"')};
    </script>
    """
    
    # Inject before closing head tag
    html_content = html_content.replace("</head>", f"{inject_script}</head>")
    
    return HTMLResponse(content=html_content)


@app.get("/stream/{token}/{filename}")
async def stream_file(token: str, filename: str, request: Request):
    """
    Stream a file from Telegram servers.
    Supports range requests for resume capability.
    Token must be valid and will be marked as used after first chunk.
    """
    # Validate token
    file_info = validate_token(token)
    if not file_info:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    file_id = file_info["file_id"]
    original_filename = file_info["file_name"]
    mime_type = file_info.get("mime_type") or "application/octet-stream"
    
    # Get file URL from Telegram
    bot = get_bot()
    file_url = await get_telegram_file_url(bot, file_id)
    
    if not file_url:
        raise HTTPException(status_code=500, detail="Failed to get file from Telegram")
    
    logger.info(f"Streaming file: {original_filename} from {file_url}")
    
    # Handle range requests
    range_header = request.headers.get("range")
    
    async def stream_generator():
        async for chunk in stream_file_from_telegram(file_url, range_header):
            yield chunk
    
    headers = {
        "Content-Disposition": f'attachment; filename="{original_filename}"',
        "Content-Type": mime_type,
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache",
    }
    
    return StreamingResponse(
        stream_generator(),
        media_type=mime_type,
        headers=headers,
    )


@app.get("/favicon.svg")
async def serve_favicon():
    """Serve favicon for the React app."""
    favicon_path = os.path.join(AD_PAGE_DIST, "favicon.svg")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/icons.svg")
async def serve_icons():
    """Serve icons for the React app."""
    icons_path = os.path.join(AD_PAGE_DIST, "icons.svg")
    if os.path.exists(icons_path):
        return FileResponse(icons_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Icons not found")
