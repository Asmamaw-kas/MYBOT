# 📚 Telegram Book & Film Fetcher Bot

A Telegram bot that fetches books or films from a private channel and sends them to users based on a code or request.  
Built with **Python** and hosted on **Railway** for 24/7 uptime.

---

## 🚀 Features
- Fetch books or films from a **private Telegram channel**.
- Works in **public or private channels**.
- Uses **webhook mode** for fast and conflict-free updates.
- Hosted on **Railway** for free 24/7 availability.
- Written in **Python** with the `python-telegram-bot` library.

---

## 🛠 Requirements
- Python 3.9+
- Telegram account
- Bot token from [BotFather](https://t.me/BotFather)
- Railway account (for deployment)

---

## 📦 Installation (Local)
```bash
# 1️⃣ Clone this repo
git clone https://github.com/yourusername/telegram-bot.git
cd telegram-bot

# 2️⃣ Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Create .env file and add:
BOT_TOKEN=your_telegram_bot_token
WEBHOOK_URL=https://your-railway-app-url/

# 5️⃣ Run locally
python bot.py
