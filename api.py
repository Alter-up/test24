"""
FastAPI Backend for X Automation Bot
Provides REST API and Web Dashboard
"""
import os
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from database import get_db, init_db, Account, Proxy, ActionLog, ScheduledPost, AutomationTask, User
from x_automation import XAutomation, AIReplyGenerator
from scheduler import TaskScheduler

# Initialize DB on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="X Automation API",
    description="Backend API for X Automation Bot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize components
scheduler = TaskScheduler()
ai_generator = AIReplyGenerator(os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None

# ============== Pydantic Models ==============

class AccountCreate(BaseModel):
    username: str
    email: str
    password: str
    proxy_id: Optional[int] = None

class AccountResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    proxy_id: Optional[int]
    actions_today: int
    daily_actions_limit: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProxyCreate(BaseModel):
    name: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None

class ProxyResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    is_active: bool
    
    class Config:
        from_attributes = True

class ActionRequest(BaseModel):
    account_id: int
    action_type: str  # like, retweet, reply, follow, post
    target_url: Optional[str] = None
    target_username: Optional[str] = None
    content: Optional[str] = None  # For replies/posts
    use_ai: bool = False
    ai_tone: Optional[str] = "friendly"

class ScheduledPostCreate(BaseModel):
    account_id: int
    content: str
    scheduled_at: datetime
    image_path: Optional[str] = None
    auto_boost: bool = False

class AutomationTaskCreate(BaseModel):
    name: str
    account_id: int
    task_type: str  # lists, search, autopost
    config: dict
    interval_minutes: int = 60

# ============== API Endpoints ==============

@app.get("/")
async def dashboard():
    """Serve the web dashboard"""
    return FileResponse("static/dashboard.html")

@app.get("/api")
async def api_info():
    return {
        "name": "X Automation API",
        "version": "1.0.0",
        "status": "running"
    }

# ============== ACCOUNTS ==============

@app.get("/api/accounts", response_model=List[AccountResponse])
async def get_accounts(db: Session = Depends(get_db)):
    """Get all accounts"""
    return db.query(Account).all()

@app.post("/api/accounts", response_model=AccountResponse)
async def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """Create new account"""
    db_account = Account(**account.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@app.get("/api/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get account by ID"""
    account = db.query(Account).get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Delete account"""
    account = db.query(Account).get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete(account)
    db.commit()
    return {"message": "Account deleted"}

@app.post("/api/accounts/{account_id}/test-login")
async def test_account_login(account_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Test login for account"""
    account = db.query(Account).get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    async def do_login():
        x_auto = XAutomation(
            proxy=account.proxy.get_url() if account.proxy else None,
            cookies=account.cookies
        )
        try:
            await x_auto.start()
            success = await x_auto.login(account.username, account.email, account.password)
            if success:
                account.cookies = await x_auto.get_cookies_json()
                db.commit()
            return {"success": success}
        finally:
            await x_auto.close()
    
    # Run in background
    background_tasks.add_task(do_login)
    return {"message": "Login test started"}

# ============== PROXIES ==============

@app.get("/api/proxies", response_model=List[ProxyResponse])
async def get_proxies(db: Session = Depends(get_db)):
    """Get all proxies"""
    return db.query(Proxy).all()

@app.post("/api/proxies", response_model=ProxyResponse)
async def create_proxy(proxy: ProxyCreate, db: Session = Depends(get_db)):
    """Create new proxy"""
    db_proxy = Proxy(**proxy.dict())
    db.add(db_proxy)
    db.commit()
    db.refresh(db_proxy)
    return db_proxy

@app.delete("/api/proxies/{proxy_id}")
async def delete_proxy(proxy_id: int, db: Session = Depends(get_db)):
    """Delete proxy"""
    proxy = db.query(Proxy).get(proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    db.delete(proxy)
    db.commit()
    return {"message": "Proxy deleted"}

# ============== ACTIONS ==============

@app.post("/api/actions/execute")
async def execute_action(action: ActionRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Execute an action"""
    account = db.query(Account).get(action.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    async def do_action():
        x_auto = XAutomation(
            proxy=account.proxy.get_url() if account.proxy else None,
            cookies=account.cookies
        )
        
        try:
            await x_auto.start()
            
            # Login if needed
            if not account.cookies:
                success = await x_auto.login(account.username, account.email, account.password)
                if success:
                    account.cookies = await x_auto.get_cookies_json()
            
            # Generate AI reply if requested
            content = action.content
            if action.use_ai and action.target_url and ai_generator:
                # Get tweet content first (simplified)
                content = await ai_generator.generate_reply("Tweet content", action.ai_tone)
            
            # Execute action
            success = False
            if action.action_type == 'like':
                success = await x_auto.like_tweet(action.target_url)
            elif action.action_type == 'retweet':
                success = await x_auto.retweet(action.target_url)
            elif action.action_type == 'reply':
                success = await x_auto.reply_to_tweet(action.target_url, content)
            elif action.action_type == 'follow':
                success = await x_auto.follow_user(action.target_username)
            elif action.action_type == 'post':
                success = await x_auto.post_tweet(content)
            
            # Log action
            log = ActionLog(
                account_id=action.account_id,
                action_type=action.action_type,
                target_url=action.target_url,
                target_username=action.target_username,
                content=content,
                status='success' if success else 'failed'
            )
            db.add(log)
            account.actions_today += 1
            db.commit()
            
            return {"success": success}
            
        finally:
            await x_auto.close()
    
    background_tasks.add_task(do_action)
    return {"message": f"Action {action.action_type} started"}

# ============== SCHEDULED POSTS ==============

@app.get("/api/posts/scheduled")
async def get_scheduled_posts(db: Session = Depends(get_db)):
    """Get all scheduled posts"""
    return db.query(ScheduledPost).filter_by(is_posted=False).all()

@app.post("/api/posts/scheduled")
async def create_scheduled_post(post: ScheduledPostCreate, db: Session = Depends(get_db)):
    """Create scheduled post"""
    db_post = ScheduledPost(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    # Schedule with scheduler
    scheduler.schedule_post(db_post)
    
    return db_post

# ============== AUTOMATION TASKS ==============

@app.get("/api/automation/tasks")
async def get_automation_tasks(db: Session = Depends(get_db)):
    """Get all automation tasks"""
    return db.query(AutomationTask).all()

@app.post("/api/automation/tasks")
async def create_automation_task(task: AutomationTaskCreate, db: Session = Depends(get_db)):
    """Create automation task"""
    db_task = AutomationTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Schedule task
    scheduler.schedule_task(db_task)
    
    return db_task

@app.post("/api/automation/tasks/{task_id}/stop")
async def stop_automation_task(task_id: int, db: Session = Depends(get_db)):
    """Stop automation task"""
    task = db.query(AutomationTask).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.is_active = False
    db.commit()
    
    scheduler.stop_task(task_id)
    
    return {"message": "Task stopped"}

# ============== LOGS & STATS ==============

@app.get("/api/logs")
async def get_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent action logs"""
    return db.query(ActionLog).order_by(ActionLog.created_at.desc()).limit(limit).all()

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics"""
    total_accounts = db.query(Account).count()
    active_accounts = db.query(Account).filter_by(is_active=True).count()
    total_actions = db.query(ActionLog).count()
    today_actions = db.query(ActionLog).filter(
        ActionLog.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
    ).count()
    active_tasks = db.query(AutomationTask).filter_by(is_active=True).count()
    
    return {
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "total_actions": total_actions,
        "today_actions": today_actions,
        "active_automations": active_tasks
    }

# ============== START SERVER ==============

if __name__ == "__main__":
    import uvicorn
    init_db()
    scheduler.start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
