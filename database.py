"""
Database models and connection for X Automation Bot
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String)
    password = Column(String, nullable=False)
    cookies = Column(Text)  # JSON serialized cookies
    is_active = Column(Boolean, default=True)
    proxy_id = Column(Integer, ForeignKey('proxies.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    
    # Limits and settings
    daily_actions_limit = Column(Integer, default=100)
    actions_today = Column(Integer, default=0)
    last_action_time = Column(DateTime)
    
    proxy = relationship("Proxy", back_populates="accounts")
    actions = relationship("ActionLog", back_populates="account")
    scheduled_posts = relationship("ScheduledPost", back_populates="account")

class Proxy(Base):
    __tablename__ = 'proxies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    accounts = relationship("Account", back_populates="proxy")
    
    def get_url(self):
        if self.username and self.password:
            return f"socks5://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"socks5://{self.host}:{self.port}"

class ActionLog(Base):
    __tablename__ = 'action_logs'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    action_type = Column(String, nullable=False)  # like, retweet, reply, follow, post, etc.
    target_url = Column(String)
    target_username = Column(String)
    content = Column(Text)  # For replies/posts
    status = Column(String, default='pending')  # pending, success, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    account = relationship("Account", back_populates="actions")

class ScheduledPost(Base):
    __tablename__ = 'scheduled_posts'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    content = Column(Text, nullable=False)
    image_path = Column(String)
    scheduled_at = Column(DateTime, nullable=False)
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime)
    auto_boost = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("Account", back_populates="scheduled_posts")

class AutomationTask(Base):
    __tablename__ = 'automation_tasks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    task_type = Column(String, nullable=False)  # lists, search, autopost
    config = Column(JSON)  # Task-specific configuration
    is_active = Column(Boolean, default=True)
    interval_minutes = Column(Integer, default=60)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

# Database initialization
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///x_automation.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if 'sqlite' in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
