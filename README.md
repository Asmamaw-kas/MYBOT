# 📚 Telegram Book & Film Fetcher Bot

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
