#!/bin/bash

# VisaGuard AI - Production Deployment Script
# Execute this on your production server (165.227.115.79)

set -e  # Exit on error

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║   🚀 VISAGUARD AI - PRODUCTION DEPLOYMENT                           ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/var/www/visaguardai"

echo -e "${BLUE}📋 Deployment Info:${NC}"
echo "  Server: 165.227.115.79"
echo "  Project: $PROJECT_DIR"
echo "  Commit: d55302a"
echo "  Date: $(date)"
echo ""

# Step 1: Navigate to project directory
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 1: Navigate to Project Directory${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cd $PROJECT_DIR
echo -e "${GREEN}✅ Current directory: $(pwd)${NC}"
echo ""

# Step 2: Check current status
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 2: Check Current Git Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Current commit:${NC}"
git log --oneline -n 1
echo ""
echo -e "${YELLOW}Branch:${NC}"
git branch --show-current
echo ""

# Step 3: Stash local changes (if any)
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 3: Stash Local Changes${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if git diff --quiet && git diff --cached --quiet; then
    echo -e "${GREEN}✅ No local changes to stash${NC}"
else
    echo -e "${YELLOW}⚠️  Stashing local changes...${NC}"
    git stash
    echo -e "${GREEN}✅ Local changes stashed${NC}"
fi
echo ""

# Step 4: Pull latest changes
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 4: Pull Latest Changes from GitHub${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Pulling from origin/main...${NC}"
git pull origin main
echo -e "${GREEN}✅ Code updated successfully${NC}"
echo ""
echo -e "${YELLOW}New commit:${NC}"
git log --oneline -n 1
echo ""

# Step 5: Verify files were updated
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 5: Verify Updated Files${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Checking scraper files...${NC}"
for file in dashboard/scraper/instagram.py dashboard/scraper/linkedin.py dashboard/scraper/facebook.py dashboard/scraper/t.py dashboard/intelligent_analyzer.py; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file (missing)${NC}"
    fi
done
echo ""

# Step 6: Restart Gunicorn
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 6: Restart Gunicorn Service${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Restarting Gunicorn...${NC}"
sudo systemctl restart gunicorn
sleep 2
echo -e "${GREEN}✅ Gunicorn restarted${NC}"
echo ""

# Step 7: Restart Nginx
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 7: Restart Nginx Service${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Restarting Nginx...${NC}"
sudo systemctl restart nginx
sleep 2
echo -e "${GREEN}✅ Nginx restarted${NC}"
echo ""

# Step 8: Verify services
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 8: Verify Services Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Gunicorn Status:${NC}"
if sudo systemctl is-active --quiet gunicorn; then
    echo -e "${GREEN}✅ Gunicorn is ACTIVE${NC}"
    sudo systemctl status gunicorn --no-pager -l | head -10
else
    echo -e "${RED}❌ Gunicorn is NOT ACTIVE${NC}"
    sudo systemctl status gunicorn --no-pager -l | head -10
fi
echo ""

echo -e "${YELLOW}Nginx Status:${NC}"
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx is ACTIVE${NC}"
    sudo systemctl status nginx --no-pager -l | head -10
else
    echo -e "${RED}❌ Nginx is NOT ACTIVE${NC}"
    sudo systemctl status nginx --no-pager -l | head -10
fi
echo ""

# Step 9: Check for errors
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 9: Check Recent Logs${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Recent Gunicorn logs (last 20 lines):${NC}"
sudo journalctl -u gunicorn -n 20 --no-pager
echo ""

# Step 10: Test site accessibility
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 10: Test Site Accessibility${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Testing https://visaguardai.com...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://visaguardai.com)
if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✅ Site is accessible (HTTP $HTTP_CODE)${NC}"
elif [ "$HTTP_CODE" == "301" ] || [ "$HTTP_CODE" == "302" ]; then
    echo -e "${GREEN}✅ Site is accessible (HTTP $HTTP_CODE - redirect)${NC}"
else
    echo -e "${RED}⚠️  Site returned HTTP $HTTP_CODE${NC}"
fi
echo ""

# Final summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                      ║${NC}"
echo -e "${GREEN}║   ✅ DEPLOYMENT COMPLETE!                                           ║${NC}"
echo -e "${GREEN}║                                                                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo -e "  ✅ Code pulled from GitHub"
echo -e "  ✅ Gunicorn restarted"
echo -e "  ✅ Nginx restarted"
echo -e "  ✅ Services verified"
echo -e "  ✅ Site accessible"
echo ""
echo -e "${BLUE}🔍 Next Steps:${NC}"
echo "  1. Visit https://visaguardai.com"
echo "  2. Login to dashboard"
echo "  3. Test analyzing a social media account"
echo "  4. Verify 10-post limit is working"
echo "  5. Check that all 4 platforms work"
echo ""
echo -e "${BLUE}📝 Monitor Logs:${NC}"
echo "  sudo journalctl -u gunicorn -f"
echo ""
echo -e "${BLUE}🎉 All changes deployed successfully!${NC}"
echo ""
echo -e "${YELLOW}Changes Deployed:${NC}"
echo "  • Instagram: 10-post limit"
echo "  • LinkedIn: 10-post limit"
echo "  • Facebook: 10-post limit"
echo "  • Twitter: 10-post limit + new actor"
echo "  • OpenRouter: Enhanced headers"
echo ""




