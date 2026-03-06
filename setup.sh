#!/bin/bash

# Setup script for X Automation Bot
# Works on macOS and Linux

set -e

echo "=========================================="
echo "  X Automation Bot - Setup Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo -e "${RED}Error: Python 3.9+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python version OK: $PYTHON_VERSION${NC}"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠ venv already exists. Skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt -q
echo -e "${GREEN}✓ Python packages installed${NC}"
echo ""

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium
echo -e "${GREEN}✓ Playwright browsers installed${NC}"
echo ""

# Create .env if not exists
echo "Checking configuration..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env already exists. Skipping...${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✓ .env created from template${NC}"
    echo ""
    echo -e "${YELLOW}⚠ IMPORTANT: Edit .env file with your settings!${NC}"
    echo "   Required: TELEGRAM_BOT_TOKEN, ALLOWED_USERS"
fi
echo ""

# Initialize database
echo "Initializing database..."
python3 -c "from database import init_db; init_db()"
echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

# Success message
echo "=========================================="
echo -e "${GREEN}  Setup completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your settings:"
echo "   nano .env"
echo ""
echo "2. Get Telegram Bot Token from @BotFather"
echo "   https://t.me/botfather"
echo ""
echo "3. Get your Telegram ID from @userinfobot"
echo "   https://t.me/userinfobot"
echo ""
echo "4. Run the bot:"
echo "   python main.py"
echo ""
echo "5. Open API docs in browser:"
echo "   http://localhost:8000/docs"
echo ""
echo "For help, see README.md"
echo ""
