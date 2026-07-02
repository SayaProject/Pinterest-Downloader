# Pinterest Downloader Telegram Bot

A Telegram bot that downloads photos and videos from Pinterest posts.

## Features

- 📸 Download Pinterest images
- 🎬 Download Pinterest videos
- 🚀 Ready to deploy on [Railway](https://railway.app)
- ✅ Error handling with user-friendly messages

## Local Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Telegram Bot Token
export BOT_TOKEN="your_token_here"

# 3. Run the bot
python bot.py
```

## Deploy to Railway

### Step 1 – Get a Telegram Bot Token
1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the steps
3. Copy the token it gives you

### Step 2 – Deploy on Railway
1. Go to [railway.app](https://railway.app) and log in
2. Click **New Project → Deploy from GitHub repo**
   - Push this folder to a GitHub repo first, **or**
   - Use **Deploy from local** by uploading the zip
3. In your Railway project, go to **Variables** tab
4. Add this environment variable:
   ```
   BOT_TOKEN = <your_telegram_bot_token>
   ```
5. Railway will auto-build and start your bot

### Step 3 – Test the bot
- Open Telegram, find your bot by its username
- Send `/start`
- Paste any Pinterest URL like:
  `https://www.pinterest.com/pin/123456789/`

## Project Structure

```
pinterest-bot/
├── bot.py            # Main bot code
├── requirements.txt  # Python dependencies
├── Procfile          # Railway/Heroku process file
├── railway.toml      # Railway deployment config
├── runtime.txt       # Python version pin
└── README.md
```

## Environment Variables

| Variable    | Required | Description                       |
|-------------|----------|-----------------------------------|
| `BOT_TOKEN` | ✅ Yes   | Your Telegram Bot API token       |

## Bugs Fixed from Original Script

| Bug | Fix |
|-----|-----|
| `input()` calls — CLI only, unusable as a bot | Replaced with Telegram message handlers |
| Typo: `pinterest_iamge.jpg` | Fixed to `pinterest_image.jpg` |
| No error handling on HTTP requests | Added `try/except` with timeouts and user messages |
| `None` download URL crashes the script | Added None-check and fallback selector |
| No User-Agent header — blocked by server | Added browser User-Agent |
| Files saved to disk (breaks cloud) | Files served from memory via `BytesIO` |
| No URL validation | Added Pinterest URL regex check |
| Script exits after one download | Bot runs indefinitely with polling |
