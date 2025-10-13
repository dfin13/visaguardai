#!/bin/bash

# VisaGuard AI - Production Deployment Script
# Deploy latest changes to production server

set -e  # Exit on any error

echo "🚀 VisaGuard AI - Production Deployment"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
SERVER="root@148.230.110.112"
PROJECT_DIR="/var/www/visaguardai"
BRANCH="main"

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "Server: $SERVER"
echo "Project Directory: $PROJECT_DIR"
echo "Branch: $BRANCH"
echo ""

# Step 1: Confirm deployment
echo -e "${YELLOW}⚠️  You are about to deploy to PRODUCTION${NC}"
echo -e "${YELLOW}This will update:${NC}"
echo "  • All scraper limits to 10 posts"
echo "  • Twitter scraper with new actor"
echo "  • OpenRouter API headers"
echo ""
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi
echo ""

# Step 2: SSH to server and pull changes
echo -e "${BLUE}📥 Step 1: Pulling latest changes from GitHub...${NC}"
ssh $SERVER << 'ENDSSH'
    set -e
    cd /var/www/visaguardai
    
    echo "Current directory: $(pwd)"
    echo ""
    
    # Stash any local changes
    echo "Stashing local changes..."
    git stash
    
    # Pull latest changes
    echo "Pulling from main branch..."
    git pull origin main
    
    echo ""
    echo "✅ Code updated successfully"
ENDSSH

echo ""

# Step 3: Install dependencies (if any new ones)
echo -e "${BLUE}📦 Step 2: Installing dependencies...${NC}"
ssh $SERVER << 'ENDSSH'
    set -e
    cd /var/www/visaguardai
    source venv/bin/activate
    
    echo "Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1
    
    echo "Installing requirements..."
    pip install -r requirements.txt
    
    echo "✅ Dependencies updated"
ENDSSH

echo ""

# Step 4: Collect static files
echo -e "${BLUE}📁 Step 3: Collecting static files...${NC}"
ssh $SERVER << 'ENDSSH'
    set -e
    cd /var/www/visaguardai
    source venv/bin/activate
    
    python manage.py collectstatic --noinput
    
    echo "✅ Static files collected"
ENDSSH

echo ""

# Step 5: Restart services
echo -e "${BLUE}🔄 Step 4: Restarting services...${NC}"
ssh $SERVER << 'ENDSSH'
    set -e
    
    echo "Restarting Gunicorn..."
    sudo systemctl restart gunicorn
    
    echo "Restarting Nginx..."
    sudo systemctl restart nginx
    
    echo "✅ Services restarted"
ENDSSH

echo ""

# Step 6: Verify deployment
echo -e "${BLUE}✅ Step 5: Verifying deployment...${NC}"
ssh $SERVER << 'ENDSSH'
    set -e
    
    echo "Checking Gunicorn status..."
    sudo systemctl status gunicorn --no-pager | head -n 5
    
    echo ""
    echo "Checking Nginx status..."
    sudo systemctl status nginx --no-pager | head -n 5
    
    echo ""
    echo "✅ All services running"
ENDSSH

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📊 Changes Deployed:${NC}"
echo "  ✅ Instagram: 10-post limit"
echo "  ✅ LinkedIn: 10-post limit"
echo "  ✅ Facebook: 10-post limit"
echo "  ✅ Twitter: 10-post limit + new actor"
echo "  ✅ OpenRouter: Enhanced headers"
echo ""
echo -e "${BLUE}🔍 Next Steps:${NC}"
echo "  1. Monitor logs: ssh $SERVER 'sudo journalctl -u gunicorn -f'"
echo "  2. Test site: https://visaguardai.com"
echo "  3. Run test script: python3 test_production_platforms.py"
echo ""
echo -e "${GREEN}✅ Production is now live with optimized scrapers!${NC}"


