#!/usr/bin/env python3
"""
X Automation Bot - Main Entry Point
"""
import os
import sys
import subprocess
import time
import signal
from dotenv import load_dotenv

load_dotenv()

def run_bot():
    """Run Telegram bot"""
    print("🤖 Starting Telegram Bot...")
    return subprocess.Popen([sys.executable, "telegram_bot.py"])

def run_api():
    """Run API server"""
    print("⚡ Starting API Server...")
    return subprocess.Popen([sys.executable, "api.py"])

def main():
    print("=" * 50)
    print("🚀 X Automation Bot")
    print("=" * 50)
    print()
    
    # Check env
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("❌ Error: TELEGRAM_BOT_TOKEN not set")
        print("Create .env file with your bot token")
        sys.exit(1)
    
    print("📋 Starting components...")
    print("   • Telegram Bot")
    print("   • API Server (http://127.0.0.1:8000)")
    print()
    
    # Start both processes
    bot_process = run_bot()
    time.sleep(2)  # Give bot time to start
    api_process = run_api()
    
    print()
    print("✅ All components started!")
    print("   Dashboard: http://127.0.0.1:8000")
    print("   API Docs:  http://127.0.0.1:8000/docs")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            # Check if processes are alive
            bot_status = bot_process.poll()
            api_status = api_process.poll()
            
            if bot_status is not None:
                print(f"⚠️  Bot exited with code {bot_status}, restarting...")
                bot_process = run_bot()
            
            if api_status is not None:
                print(f"⚠️  API exited with code {api_status}, restarting...")
                api_process = run_api()
            
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        bot_process.terminate()
        api_process.terminate()
        print("✅ Stopped")

if __name__ == "__main__":
    main()
oardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
