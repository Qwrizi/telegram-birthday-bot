import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    DATABASE_URL = 'sqlite:///birthdays.db'
    
    REMINDER_HOUR = 2  # В 9 утра
    REMINDER_MINUTE = 0