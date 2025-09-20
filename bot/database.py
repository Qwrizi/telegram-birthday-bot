from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot.models import Base
from bot.config import Config

class Database:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def init_db(self):
        """Инициализация базы данных"""
        Base.metadata.create_all(bind=self.engine)
        print("База данных инициализирована")
    
    def get_session(self):
        """Получить сессию базы данных"""
        return self.SessionLocal()

# Глобальный экземпляр базы данных
db = Database()