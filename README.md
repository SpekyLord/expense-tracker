# 💰 Smart Expense Tracker

A Python-based expense tracker that combines OCR receipt scanning, Google Sheets sync, and real-time analytics.  
Easily capture expenses, auto-categorize them, and visualize spending trends.

---

## ✨ Features
- 📸 **OCR Processing** – extract merchant, total, and date from receipts  
- 📊 **Google Sheets Integration** – store and manage expenses in the cloud  
- 🧠 **Analytics & Insights** – monthly summaries, duplicates detection, smart insights  
- 💡 **Budget Management** – set budgets and get alerts when overspending  
- 📑 **PDF Reports** – generate weekly, monthly, or yearly reports  
- 🤖 **Telegram Bot** – add expenses via chat & upload receipts  
- 🌐 **Web Dashboard** – interactive charts and spending summaries  

---

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SpekyLord/expense-tracker.git
   cd expense-tracker
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv expense_env
   source expense_env/bin/activate   # On Linux/Mac
   expense_env\\Scripts\\activate      # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**  
   Create a `.env` file in the project root:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=google_credentials.json
   TELEGRAM_BOT_TOKEN=your_telegram_token
   TESSERACT_PATH=C:/Program Files/Tesseract-OCR/tesseract.exe
   ```

5. **Add your `google_credentials.json` file locally**  
   (never push it to GitHub — already ignored via `.gitignore`).

---

## 🚀 Usage

### Run the Flask Web Dashboard
```bash
python web_dashboard.py
```
Visit 👉 [http://localhost:5000](http://localhost:5000)

### Run the Telegram Bot
```bash
python simple_bot.py
```

🤖 **Enhanced Bot Running! Available Commands:**
- `/start` – Main menu and setup  
- `/analytics` – View spending analytics  
- `/budget` – Set spending budgets  
- `/report` – Generate detailed reports  
- `/insights` – Get AI-powered insights  

👉 Try it here: [t.me/my_expense_123_bot](https://t.me/my_expense_123_bot)

---

## 📂 Project Structure
```
expense-tracker/
│── __pycache__/                 # Python cache files
│── expense_env/                 # Virtual environment (local only)
│── templates/
│   └── dashboard.html           # Web dashboard template
│── .env                         # Environment variables (not tracked)
│── .gitignore                   # Git ignore rules
│── analytics_engine.py          # Analytics & insights
│── budget_manager.py            # Budget tracking & alerts
│── google_credentials.json      # Google Sheets API credentials (ignored in git)
│── ocr_processor.py             # OCR receipt scanning
│── report_generator.py          # PDF reports
│── sheets_manager.py            # Google Sheets integration
│── simple_bot.py                # Telegram bot
│── user_budgets.json            # Stores user budget data
│── web_dashboard.py             # Flask web dashboard
```

---

## ⚠️ Security Notes
- Never commit `google_credentials.json` or `.env`  
- Secrets (API keys, credentials) should stay **local only**  
- GitHub push protection is enabled to keep your repo safe  

---

## 📜 License
MIT License © 2025 [SpekyLord](https://github.com/SpekyLord)
