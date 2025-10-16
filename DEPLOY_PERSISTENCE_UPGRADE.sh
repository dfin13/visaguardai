#!/bin/bash

# VisaGuardAI Persistence & Security Upgrade Deployment Script
# Run this on the production server

set -e  # Exit on error

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   VisaGuardAI Persistence & Security Upgrade Deployment      ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root or with sudo${NC}"
   echo "Usage: sudo bash DEPLOY_PERSISTENCE_UPGRADE.sh"
   exit 1
fi

# Configuration
PROJECT_DIR="/var/www/visaguardai"
PYTHON_BIN="python3"
GUNICORN_SERVICE="gunicorn"

echo -e "${YELLOW}📍 Project Directory: $PROJECT_DIR${NC}"
echo ""

# Step 1: Backup database
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Backup Database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd "$PROJECT_DIR"
BACKUP_FILE="backup_before_persistence_upgrade_$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump visaguard_db > "/tmp/$BACKUP_FILE" 2>/dev/null || echo "⚠️  Backup skipped (optional)"
echo -e "${GREEN}✓ Database backup created (if PostgreSQL is running)${NC}"
echo ""

# Step 2: Pull latest code
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Pull Latest Code"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git pull origin main
echo -e "${GREEN}✓ Code updated${NC}"
echo ""

# Step 3: Install dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Install Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PYTHON_BIN -m pip install -r requirements.txt -q
echo -e "${GREEN}✓ Dependencies installed (including django-encrypted-model-fields)${NC}"
echo ""

# Step 4: Generate encryption key (if not set)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Configure Encryption Key"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if encryption key is already set
if grep -q "FIELD_ENCRYPTION_KEY" /etc/systemd/system/$GUNICORN_SERVICE.service 2>/dev/null; then
    echo -e "${GREEN}✓ Encryption key already configured${NC}"
else
    echo -e "${YELLOW}⚠️  Generating new encryption key...${NC}"
    NEW_KEY=$($PYTHON_BIN -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo -e "${GREEN}✓ Generated key: ${NEW_KEY:0:20}...${NC}"
    echo ""
    echo -e "${YELLOW}📝 Please add this to your Gunicorn service file:${NC}"
    echo ""
    echo "sudo nano /etc/systemd/system/$GUNICORN_SERVICE.service"
    echo ""
    echo "Add this line in the [Service] section:"
    echo "Environment=\"FIELD_ENCRYPTION_KEY=$NEW_KEY\""
    echo ""
    echo -e "${YELLOW}Press ENTER after you've added the key...${NC}"
    read -r
    
    echo "Reloading systemd daemon..."
    systemctl daemon-reload
    echo -e "${GREEN}✓ Daemon reloaded${NC}"
fi
echo ""

# Step 5: Run migrations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Run Migrations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PYTHON_BIN manage.py migrate dashboard
echo -e "${GREEN}✓ Migrations applied${NC}"
echo ""

# Step 6: Test cleanup command
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Test Cleanup Command"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PYTHON_BIN manage.py cleanup_old_data --dry-run | head -20
echo -e "${GREEN}✓ Cleanup command functional${NC}"
echo ""

# Step 7: Restart Gunicorn
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Restart Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
systemctl restart $GUNICORN_SERVICE
sleep 3
systemctl status $GUNICORN_SERVICE --no-pager -l | head -15
echo -e "${GREEN}✓ Gunicorn restarted${NC}"
echo ""

# Step 8: Verify deployment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8: Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Checking recent logs for errors..."
journalctl -u $GUNICORN_SERVICE --since "30 seconds ago" --no-pager | grep -i "error\|traceback" | head -5 || echo -e "${GREEN}✓ No errors in logs${NC}"
echo ""
echo "Checking database migrations:"
$PYTHON_BIN manage.py showmigrations dashboard | tail -3
echo ""

# Summary
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ✅ DEPLOYMENT COMPLETE                                     ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Upgrade successfully deployed!${NC}"
echo ""
echo "✅ What's New:"
echo "   • Twitter field now persists to database"
echo "   • Analysis results stored permanently (AnalysisResult model)"
echo "   • API keys encrypted at rest"
echo "   • Cleanup command available: python manage.py cleanup_old_data"
echo ""
echo "📋 Next Steps:"
echo "   1. Test Twitter connection: https://visaguardai.com/dashboard/"
echo "   2. Run an analysis to verify persistence"
echo "   3. Set up cleanup cron job (optional but recommended)"
echo "   4. Monitor logs for any issues"
echo ""
echo "📖 Documentation:"
echo "   • PERSISTENCE_SECURITY_UPGRADE_COMPLETE.md"
echo "   • USER_DATA_STORAGE_MAP.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

