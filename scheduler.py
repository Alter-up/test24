"""
Task Scheduler for Automation Workflows
Uses APScheduler for recurring tasks
"""
import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from database import get_db, AutomationTask, ScheduledPost, Account, ActionLog
from x_automation import XAutomation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.running_tasks = {}  # task_id -> job_id mapping
        
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("Task scheduler started")
        
        # Load and schedule existing active tasks from DB
        self._load_existing_tasks()
    
    def _load_existing_tasks(self):
        """Load automation tasks from database"""
        db = next(get_db())
        tasks = db.query(AutomationTask).filter_by(is_active=True).all()
        
        for task in tasks:
            self.schedule_task(task)
        
        logger.info(f"Loaded {len(tasks)} automation tasks")
    
    def schedule_task(self, task: AutomationTask):
        """Schedule an automation task"""
        if task.task_type == 'lists':
            job = self.scheduler.add_job(
                self._run_lists_automation,
                IntervalTrigger(minutes=task.interval_minutes),
                args=[task.id],
                id=f"task_{task.id}",
                replace_existing=True
            )
        elif task.task_type == 'search':
            job = self.scheduler.add_job(
                self._run_search_automation,
                IntervalTrigger(minutes=task.interval_minutes),
                args=[task.id],
                id=f"task_{task.id}",
                replace_existing=True
            )
        elif task.task_type == 'autopost':
            job = self.scheduler.add_job(
                self._run_autopost,
                IntervalTrigger(minutes=task.interval_minutes),
                args=[task.id],
                id=f"task_{task.id}",
                replace_existing=True
            )
        
        self.running_tasks[task.id] = job.id
        logger.info(f"Scheduled task {task.id} ({task.task_type}) every {task.interval_minutes} min")
    
    def stop_task(self, task_id: int):
        """Stop a scheduled task"""
        job_id = self.running_tasks.get(task_id)
        if job_id:
            self.scheduler.remove_job(job_id)
            del self.running_tasks[task_id]
            logger.info(f"Stopped task {task_id}")
    
    def _run_lists_automation(self, task_id: int):
        """Run lists-based automation"""
        logger.info(f"Running lists automation for task {task_id}")
        
        db = next(get_db())
        task = db.query(AutomationTask).get(task_id)
        if not task or not task.is_active:
            return
        
        config = task.config or {}
        list_url = config.get('list_url')
        actions = config.get('actions', ['like'])  # ['like', 'retweet', 'follow']
        max_items = config.get('max_items', 10)
        
        # Update last run
        task.last_run = datetime.utcnow()
        task.next_run = datetime.utcnow() + timedelta(minutes=task.interval_minutes)
        db.commit()
        
        # Run automation (async)
        asyncio.create_task(self._execute_list_actions(task.account_id, list_url, actions, max_items))
    
    async def _execute_list_actions(self, account_id: int, list_url: str, actions: list, max_items: int):
        """Execute actions from a list"""
        db = next(get_db())
        account = db.query(Account).get(account_id)
        
        if not account:
            return
        
        x_auto = XAutomation(
            proxy=account.proxy.get_url() if account.proxy else None,
            cookies=account.cookies
        )
        
        try:
            await x_auto.start()
            
            if not account.cookies:
                # Login if no cookies
                success = await x_auto.login(account.username, account.email, account.password)
                if success:
                    account.cookies = await x_auto.get_cookies_json()
                    db.commit()
            
            # Navigate to list
            await x_auto.page.goto(list_url)
            await x_auto.human_delay(3, 5)
            
            # Get tweets from list
            tweets = await x_auto.page.query_selector_all('article a[href*="/status/"]')
            processed = 0
            
            for tweet in tweets[:max_items]:
                href = await tweet.get_attribute('href')
                if not href:
                    continue
                
                tweet_url = f"https://twitter.com{href}" if not href.startswith('http') else href
                
                for action in actions:
                    success = False
                    
                    if action == 'like':
                        success = await x_auto.like_tweet(tweet_url)
                    elif action == 'retweet':
                        success = await x_auto.retweet(tweet_url)
                    elif action == 'follow':
                        parts = href.split('/')
                        if len(parts) > 1:
                            username = parts[1]
                            success = await x_auto.follow_user(username)
                    
                    # Log action
                    log = ActionLog(
                        account_id=account_id,
                        action_type=action,
                        target_url=tweet_url,
                        status='success' if success else 'failed'
                    )
                    db.add(log)
                    
                    await x_auto.human_delay(3, 7)
                
                processed += 1
                account.actions_today += len(actions)
                db.commit()
            
            logger.info(f"Processed {processed} items from list for account {account.username}")
            
        except Exception as e:
            logger.error(f"Error in list automation: {e}")
        finally:
            await x_auto.close()
    
    def _run_search_automation(self, task_id: int):
        """Run search-based automation"""
        logger.info(f"Running search automation for task {task_id}")
        
        db = next(get_db())
        task = db.query(AutomationTask).get(task_id)
        if not task or not task.is_active:
            return
        
        config = task.config or {}
        query = config.get('query')
        action = config.get('action', 'like')
        max_results = config.get('max_results', 5)
        
        # Update last run
        task.last_run = datetime.utcnow()
        task.next_run = datetime.utcnow() + timedelta(minutes=task.interval_minutes)
        db.commit()
        
        # Run automation
        asyncio.create_task(self._execute_search_actions(
            task.account_id, query, action, max_results
        ))
    
    async def _execute_search_actions(self, account_id: int, query: str, action: str, max_results: int):
        """Execute search actions"""
        db = next(get_db())
        account = db.query(Account).get(account_id)
        
        if not account:
            return
        
        x_auto = XAutomation(
            proxy=account.proxy.get_url() if account.proxy else None,
            cookies=account.cookies
        )
        
        try:
            await x_auto.start()
            
            if not account.cookies:
                success = await x_auto.login(account.username, account.email, account.password)
                if success:
                    account.cookies = await x_auto.get_cookies_json()
                    db.commit()
            
            results = await x_auto.search_and_interact(query, action, max_results)
            
            # Log results
            for result in results:
                log = ActionLog(
                    account_id=account_id,
                    action_type=action,
                    target_url=result['url'],
                    status='success' if result['success'] else 'failed'
                )
                db.add(log)
            
            account.actions_today += len(results)
            db.commit()
            
            logger.info(f"Search automation completed: {len(results)} actions")
            
        except Exception as e:
            logger.error(f"Error in search automation: {e}")
        finally:
            await x_auto.close()
    
    def _run_autopost(self, task_id: int):
        """Run autopost scheduled posts"""
        logger.info(f"Running autopost for task {task_id}")
        
        db = next(get_db())
        task = db.query(AutomationTask).get(task_id)
        if not task or not task.is_active:
            return
        
        # Update last run
        task.last_run = datetime.utcnow()
        task.next_run = datetime.utcnow() + timedelta(minutes=task.interval_minutes)
        db.commit()
        
        # Find posts scheduled for now
        now = datetime.utcnow()
        posts = db.query(ScheduledPost).filter(
            ScheduledPost.account_id == task.account_id,
            ScheduledPost.is_posted == False,
            ScheduledPost.scheduled_at <= now
        ).all()
        
        for post in posts:
            asyncio.create_task(self._execute_post(post.id))
    
    async def _execute_post(self, post_id: int):
        """Execute a scheduled post"""
        db = next(get_db())
        post = db.query(ScheduledPost).get(post_id)
        
        if not post or post.is_posted:
            return
        
        account = post.account
        
        x_auto = XAutomation(
            proxy=account.proxy.get_url() if account.proxy else None,
            cookies=account.cookies
        )
        
        try:
            await x_auto.start()
            
            if not account.cookies:
                success = await x_auto.login(account.username, account.email, account.password)
                if success:
                    account.cookies = await x_auto.get_cookies_json()
                    db.commit()
            
            success = await x_auto.post_tweet(post.content, post.image_path)
            
            if success:
                post.is_posted = True
                post.posted_at = datetime.utcnow()
                db.commit()
                
                # Auto boost if enabled
                if post.auto_boost:
                    # TODO: Implement boost logic
                    pass
                
                logger.info(f"Posted scheduled tweet for {account.username}")
            else:
                logger.error(f"Failed to post scheduled tweet for {account.username}")
            
        except Exception as e:
            logger.error(f"Error in autopost: {e}")
        finally:
            await x_auto.close()
    
    def schedule_post(self, post: ScheduledPost):
        """Schedule a one-time post"""
        job = self.scheduler.add_job(
            self._execute_post_job,
            'date',
            run_date=post.scheduled_at,
            args=[post.id],
            id=f"post_{post.id}",
            replace_existing=True
        )
        logger.info(f"Scheduled post {post.id} for {post.scheduled_at}")
    
    def _execute_post_job(self, post_id: int):
        """Wrapper for scheduled post execution"""
        asyncio.create_task(self._execute_post(post_id))


# Global scheduler instance
scheduler = TaskScheduler()

def get_scheduler():
    return scheduler
