from sqlalchemy import Column, Integer, String, Date, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Birthday(Base):
    __tablename__ = "birthdays"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True)
    birth_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Birthday(username='{self.username}', birth_date='{self.birth_date}')>"

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, unique=True, nullable=False)
    title = Column(String)
    added_at = Column(DateTime, default=func.now())