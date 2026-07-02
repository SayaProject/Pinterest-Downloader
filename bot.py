import os
import logging
from dotenv import load_dotenv
load_dotenv()
import re
import requests
from io import BytesIO
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from pyquery import PyQuery as pq

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PINTEREST_RE = re.compile(
    r"https?://((www|[a-z]{2})\.)?pinterest\.(com(\.[a-z]{2})?|co\.[a-z]{2}|[a-z]{2})/.+"
    r"|https?://pin\.it/.+",
    re.IGNORECASE,
)

SMALL_CAPS = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢ"
)

WELCOME_IMAGE = "https://files.catbox.moe/3v075h.jpg"

def sc(text: str) -> str:
    return text.lower().translate(SMALL_CAPS)


def resolve_short_url(link: str) -> str:
    try:
        resp = requests.head(link, allow_redirects=True, timeout=15, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
        final = resp.url
        logger.info("Resolved %s -> %s", link, final)
        return final
    except Exception as exc:
        logger.warning("Could not resolve short URL %s: %s", link, exc)
        return link


def normalize_url(link: str) -> str:
    if "pin.it" in link:
        link = resolve_short_url(link)
    match = re.search(r"/pin/(\d+)", link, re.IGNORECASE)
    if match:
        return f"https://www.pinterest.com/pin/{match.group(1)}/"
    link = re.sub(
        r"https?://([a-z]{2}\.)?pinterest\.",
        "https://www.pinterest.",
        link,
        flags=re.IGNORECASE,
    )
    return link


def get_download_url(link: str) -> str | None:
    link = normalize_url(link)
    logger.info("Normalized URL: %s", link)
    try:
        resp = requests.post(
            "https://www.expertsphp.com/download.php",
            data={"url": link},
            timeout=30,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        resp.raise_for_status()
        doc = pq(resp.text)
        url = doc("table.table-condensed tbody td a").attr("href")
        if not url:
            for a in doc("a").items():
                href = a.attr("href") or ""
                if any(ext in href for ext in (".mp4", ".jpg", ".jpeg", ".png", ".gif")):
                    url = href
                    break
        if url and url.startswith("http"):
            return url
        logger.warning("No download URL found for: %s", link)
        return None
    except requests.RequestException as exc:
        logger.error("Request failed for %s: %s", link, exc)
        return None
    except Exception as exc:
        logger.error("Unexpected error for %s: %s", link, exc)
        return None


def fetch_media(url: str) -> bytes | None:
    try:
        resp = requests.get(url, timeout=120, stream=True, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
        resp.raise_for_status()
        return resp.content
    except Exception as exc:
        logger.error("Failed to fetch media from %s: %s", url, exc)
        return None


def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(sc("Help"), callback_data="help")]
    ])


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(sc("Back"), callback_data="back")]
    ])


async def send_welcome(update_or_message, edit: bool = False) -> None:
    text = (
        sc("Pinterest Downloader Bot") + "\n\n" +
        sc("Send me any Pinterest URL and I will download the photo or video for you") + "\n\n" +
        sc("Supported link types") + "\n" +
        "https://pin.it/xxxxxxx\n" +
        "https://in.pinterest.com/pin/ID/\n" +
        "https://www.pinterest.com/pin/ID/"
    )
    if edit:
        await update_or_message.edit_media(
            media=__import__("telegram").InputMediaPhoto(
                media=WELCOME_IMAGE,
                caption=text,
            ),
            reply_markup=welcome_keyboard(),
        )
    else:
        await update_or_message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=text,
            reply_markup=welcome_keyboard(),
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_welcome(update.message)


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        text = (
            sc("How to use") + "\n\n" +
            sc("1 Copy any Pinterest URL") + "\n" +
            sc("2 Paste it here") + "\n" +
            sc("3 I will send back the image or video") + "\n\n" +
            sc("All supported formats") + "\n" +
            "pin.it/xxxxxxx\n" +
            "pinterest.com/pin/ID/\n" +
            "in.pinterest.com/pin/ID/\n" +
            "www.pinterest.co.uk/pin/ID/"
        )
        await query.edit_message_caption(
            caption=text,
            reply_markup=help_keyboard(),
        )

    elif query.data == "back":
        text = (
            sc("Pinterest Downloader Bot") + "\n\n" +
            sc("Send me any Pinterest URL and I will download the photo or video for you") + "\n\n" +
            sc("Supported link types") + "\n" +
            "https://pin.it/xxxxxxx\n" +
            "https://in.pinterest.com/pin/ID/\n" +
            "https://www.pinterest.com/pin/ID/"
        )
        await query.edit_message_caption(
            caption=text,
            reply_markup=welcome_keyboard(),
        )


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()

    if not PINTEREST_RE.match(text):
        await update.message.reply_text(
            sc("That does not look like a Pinterest URL") + "\n" +
            sc("Supported formats") + "\n" +
            "pin.it/xxxxxxx\n" +
            "pinterest.com/pin/ID/\n" +
            "in.pinterest.com/pin/ID/"
        )
        return

    status_msg = await update.message.reply_text(sc("Fetching your media please wait"))

    download_url = get_download_url(text)

    if not download_url:
        await status_msg.edit_text(
            sc("Sorry I could not extract the download link") + "\n\n" +
            sc("Possible reasons") + "\n" +
            sc("The pin is private or deleted") + "\n" +
            sc("The third party service is temporarily down") + "\n\n" +
            sc("Please try again later")
        )
        return

    media_bytes = fetch_media(download_url)

    if not media_bytes:
        await status_msg.edit_text(
            sc("Could not download the file") + "\n" +
            sc("Please try again later")
        )
        return

    is_video = ".mp4" in download_url.lower()
    buf = BytesIO(media_bytes)

    try:
        await status_msg.edit_text(sc("Sending your file please wait"))
        if is_video:
            buf.name = "pinterest_video.mp4"
            await update.message.reply_video(
                video=InputFile(buf, filename="pinterest_video.mp4"),
                caption=sc("Here is your Pinterest video"),
                supports_streaming=True,
            )
        else:
            buf.name = "pinterest_image.jpg"
            await update.message.reply_photo(
                photo=InputFile(buf, filename="pinterest_image.jpg"),
                caption=sc("Here is your Pinterest image"),
            )
        await status_msg.delete()

    except Exception as exc:
        logger.error("Failed to send media: %s", exc)
        # Try sending as document as fallback (no size limit message)
        try:
            buf.seek(0)
            ext = "mp4" if is_video else "jpg"
            fname = f"pinterest_file.{ext}"
            buf.name = fname
            await update.message.reply_document(
                document=InputFile(buf, filename=fname),
                caption=sc("Here is your Pinterest file"),
            )
            await status_msg.delete()
        except Exception as exc2:
            logger.error("Fallback document send also failed: %s", exc2)
            await status_msg.edit_text(
                sc("Could not send the file please try again later")
            )


async def handle_non_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        sc("Please send me a Pinterest URL to download") + "\n" +
        sc("Type help for instructions")
    )


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is not set!")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(help_callback, pattern="^(help|back)$"))
    app.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(r"^https?://"), handle_url)
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_url))

    logger.info("Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
