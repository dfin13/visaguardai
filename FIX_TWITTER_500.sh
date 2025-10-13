#!/bin/bash

# Fix Twitter 500 Error - Production
# This script ensures Twitter uses the correct API key and restarts services

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║   🔧 FIX TWITTER 500 ERROR - API KEY CHECK                          ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project directory
PROJECT_DIR="/var/www/visaguardai"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: Check .env file${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd $PROJECT_DIR

if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Check for APIFY_API_KEY
    if grep -q "^APIFY_API_KEY=" .env; then
        KEY=$(grep "^APIFY_API_KEY=" .env | cut -d '=' -f 2 | tr -d '"' | tr -d "'")
        if [ -n "$KEY" ]; then
            echo -e "${GREEN}✅ APIFY_API_KEY is set in .env${NC}"
            echo "   Key preview: ${KEY:0:10}...${KEY: -4}"
        else
            echo -e "${RED}❌ APIFY_API_KEY is empty in .env${NC}"
            echo "   Action: Set the correct API key in .env"
            exit 1
        fi
    else
        echo -e "${RED}❌ APIFY_API_KEY not found in .env${NC}"
        echo "   Action: Add APIFY_API_KEY=your_key_here to .env"
        exit 1
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
    echo "   Location: $PROJECT_DIR/.env"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: Verify code is up to date${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check latest commit
CURRENT_COMMIT=$(git log --oneline -n 1)
echo "Current commit: $CURRENT_COMMIT"

# Check if Twitter scraper has the correct key loading
if grep -q "APIFY_API_TOKEN = os.getenv('APIFY_API_KEY')" dashboard/scraper/t.py; then
    echo -e "${GREEN}✅ Twitter scraper uses correct API key loading${NC}"
else
    echo -e "${RED}❌ Twitter scraper has incorrect API key loading${NC}"
    echo "   Action: Pull latest code from GitHub"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3: Check Twitter scraper structure${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if Twitter returns list (not JSON string)
if grep -q "return results  # Return Python list" dashboard/scraper/t.py; then
    echo -e "${GREEN}✅ Twitter returns Python list (correct)${NC}"
else
    echo -e "${YELLOW}⚠️  Twitter may still return JSON string${NC}"
    echo "   Checking for json.dumps..."
    if grep -q "return json.dumps(results" dashboard/scraper/t.py; then
        echo -e "${RED}❌ Twitter returns JSON string (WRONG - causes 500)${NC}"
        echo "   Action: Update dashboard/scraper/t.py"
        echo "   Change: return json.dumps(results) → return results"
        exit 1
    else
        echo -e "${GREEN}✅ No json.dumps found${NC}"
    fi
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 4: Restart services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Restarting Gunicorn..."
sudo systemctl restart gunicorn
sleep 2

if sudo systemctl is-active --quiet gunicorn; then
    echo -e "${GREEN}✅ Gunicorn restarted successfully${NC}"
else
    echo -e "${RED}❌ Gunicorn failed to restart${NC}"
    sudo systemctl status gunicorn --no-pager
    exit 1
fi

echo ""
echo "Restarting Nginx..."
sudo systemctl restart nginx
sleep 2

if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx restarted successfully${NC}"
else
    echo -e "${RED}❌ Nginx failed to restart${NC}"
    sudo systemctl status nginx --no-pager
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 5: Run diagnostic${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Running API key diagnostic..."
source venv/bin/activate
python3 check_twitter_api_keys.py

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                      ║${NC}"
echo -e "${GREEN}║   ✅ TWITTER FIX APPLIED - SERVICES RESTARTED                       ║${NC}"
echo -e "${GREEN}║                                                                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next: Test Twitter analysis at https://visaguardai.com/dashboard/"
echo ""

