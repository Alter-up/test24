"""
X (Twitter) Automation Module using Playwright
Emulates human behavior without using X API
"""
import asyncio
import json
import random
import logging
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XAutomation:
    def __init__(self, proxy: Optional[str] = None, cookies: Optional[str] = None):
        self.proxy = proxy
        self.cookies = json.loads(cookies) if cookies else None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        
    async def start(self):
        """Initialize browser with optional proxy"""
        playwright = await async_playwright().start()
        
        browser_args = {
            'headless': False,  # Set to True for production
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        }
        
        if self.proxy:
            browser_args['proxy'] = {'server': self.proxy}
        
        self.browser = await playwright.chromium.launch(**browser_args)
        
        context_args = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        self.context = await self.browser.new_context(**context_args)
        
        # Inject anti-detection script
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            window.chrome = { runtime: {} };
        """)
        
        # Load cookies if available
        if self.cookies:
            await self.context.add_cookies(self.cookies)
        
        self.page = await self.context.new_page()
        logger.info("Browser started successfully")
        
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
    
    async def human_delay(self, min_sec: float = 2, max_sec: float = 5):
        """Random delay to mimic human behavior"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    async def scroll_randomly(self, times: int = 3):
        """Random scrolling like a human"""
        for _ in range(times):
            scroll_amount = random.randint(300, 800)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await self.human_delay(0.5, 1.5)
    
    async def login(self, username: str, email: str, password: str) -> bool:
        """Login to X"""
        try:
            logger.info(f"Attempting login for {username}")
            await self.page.goto('https://twitter.com/i/flow/login')
            await self.human_delay(3, 5)
            
            # Enter username/email
            await self.page.fill('input[autocomplete="username"]', email)
            await self.human_delay(0.5, 1)
            await self.page.keyboard.press('Enter')
            await self.human_delay(2, 3)
            
            # Handle unusual activity check (phone/username verification)
            unusual_activity = await self.page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
            if unusual_activity:
                await self.page.fill('input[data-testid="ocfEnterTextTextInput"]', username)
                await self.human_delay(0.5, 1)
                await self.page.keyboard.press('Enter')
                await self.human_delay(2, 3)
            
            # Enter password
            await self.page.fill('input[name="password"]', password)
            await self.human_delay(0.5, 1)
            await self.page.keyboard.press('Enter')
            await self.human_delay(4, 6)
            
            # Check if logged in
            if '/home' in self.page.url or await self.page.query_selector('[data-testid="AppTabBar_Home_Link"]'):
                self.is_logged_in = True
                logger.info(f"Successfully logged in as {username}")
                
                # Save cookies for future use
                cookies = await self.context.cookies()
                return True
            else:
                logger.error(f"Login failed for {username}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    async def like_tweet(self, tweet_url: str) -> bool:
        """Like a tweet"""
        try:
            await self.page.goto(tweet_url)
            await self.human_delay(2, 4)
            await self.scroll_randomly(1)
            
            like_button = await self.page.query_selector('[data-testid="like"]')
            if like_button:
                await like_button.click()
                await self.human_delay(1, 2)
                logger.info(f"Liked tweet: {tweet_url}")
                return True
            else:
                logger.warning(f"Like button not found for: {tweet_url}")
                return False
        except Exception as e:
            logger.error(f"Error liking tweet: {e}")
            return False
    
    async def retweet(self, tweet_url: str) -> bool:
        """Retweet a tweet"""
        try:
            await self.page.goto(tweet_url)
            await self.human_delay(2, 4)
            
            retweet_button = await self.page.query_selector('[data-testid="retweet"]')
            if retweet_button:
                await retweet_button.click()
                await self.human_delay(1, 2)
                
                confirm_button = await self.page.query_selector('[data-testid="retweetConfirm"]')
                if confirm_button:
                    await confirm_button.click()
                    await self.human_delay(1, 2)
                
                logger.info(f"Retweeted: {tweet_url}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error retweeting: {e}")
            return False
    
    async def reply_to_tweet(self, tweet_url: str, message: str) -> bool:
        """Reply to a tweet"""
        try:
            await self.page.goto(tweet_url)
            await self.human_delay(2, 4)
            
            reply_button = await self.page.query_selector('[data-testid="reply"]')
            if reply_button:
                await reply_button.click()
                await self.human_delay(1, 2)
                
                # Find reply textarea
                reply_input = await self.page.query_selector('[data-testid="tweetTextarea_0"]')
                if reply_input:
                    await reply_input.fill(message)
                    await self.human_delay(1, 3)
                    
                    # Click reply button
                    send_button = await self.page.query_selector('[data-testid="tweetButton"]')
                    if send_button:
                        await send_button.click()
                        await self.human_delay(2, 3)
                        logger.info(f"Replied to: {tweet_url}")
                        return True
            return False
        except Exception as e:
            logger.error(f"Error replying: {e}")
            return False
    
    async def follow_user(self, username: str) -> bool:
        """Follow a user"""
        try:
            await self.page.goto(f'https://twitter.com/{username}')
            await self.human_delay(2, 4)
            
            follow_button = await self.page.query_selector('[data-testid="follow"]')
            if follow_button:
                await follow_button.click()
                await self.human_delay(1, 2)
                logger.info(f"Followed user: {username}")
                return True
            else:
                logger.info(f"Already following or button not found: {username}")
                return False
        except Exception as e:
            logger.error(f"Error following user: {e}")
            return False
    
    async def post_tweet(self, content: str, image_path: Optional[str] = None) -> bool:
        """Post a new tweet"""
        try:
            await self.page.goto('https://twitter.com/compose/tweet')
            await self.human_delay(2, 4)
            
            # Fill tweet content
            tweet_input = await self.page.query_selector('[data-testid="tweetTextarea_0"]')
            if tweet_input:
                await tweet_input.fill(content)
                await self.human_delay(1, 2)
                
                # Upload image if provided
                if image_path:
                    file_input = await self.page.query_selector('input[type="file"]')
                    if file_input:
                        await file_input.set_input_files(image_path)
                        await self.human_delay(2, 4)
                
                # Click tweet button
                tweet_button = await self.page.query_selector('[data-testid="tweetButton"]')
                if tweet_button:
                    await tweet_button.click()
                    await self.human_delay(2, 4)
                    logger.info(f"Posted tweet: {content[:50]}...")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            return False
    
    async def search_and_interact(self, query: str, action: str = 'like', max_results: int = 5) -> List[Dict]:
        """Search for tweets and perform actions"""
        results = []
        try:
            await self.page.goto(f'https://twitter.com/search?q={query}&src=typed_query&f=live')
            await self.human_delay(3, 5)
            
            # Get tweet links
            tweets = await self.page.query_selector_all('article a[href*="/status/"]')
            tweet_urls = []
            
            for tweet in tweets[:max_results]:
                href = await tweet.get_attribute('href')
                if href and '/status/' in href:
                    full_url = f'https://twitter.com{href}' if not href.startswith('http') else href
                    if full_url not in tweet_urls:
                        tweet_urls.append(full_url)
            
            # Perform action on each tweet
            for url in tweet_urls[:max_results]:
                success = False
                if action == 'like':
                    success = await self.like_tweet(url)
                elif action == 'retweet':
                    success = await self.retweet(url)
                elif action == 'follow':
                    # Extract username from URL
                    parts = url.split('/')
                    if len(parts) > 3:
                        username = parts[3]
                        success = await self.follow_user(username)
                
                results.append({'url': url, 'success': success})
                await self.human_delay(3, 6)
            
        except Exception as e:
            logger.error(f"Error in search and interact: {e}")
        
        return results
    
    async def get_cookies_json(self) -> str:
        """Get current cookies as JSON string"""
        cookies = await self.context.cookies()
        return json.dumps(cookies)


class AIReplyGenerator:
    """Generate AI replies using OpenAI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def generate_reply(self, tweet_content: str, tone: str = 'friendly') -> str:
        """Generate a reply based on tweet content"""
        try:
            import openai
            openai.api_key = self.api_key
            
            prompt = f"""Tweet: "{tweet_content}"
            
Generate a short, natural reply (under 280 characters) in a {tone} tone.
Make it conversational and relevant to the tweet content."""
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates natural Twitter replies."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            reply = response.choices[0].message.content.strip()
            return reply[:280]  # Ensure it's under Twitter limit
            
        except Exception as e:
            logger.error(f"Error generating AI reply: {e}")
            return "Interesting point! Thanks for sharing."
