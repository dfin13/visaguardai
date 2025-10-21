#!/bin/bash
# Quick deployment script for dark mode template fixes
# Run this on the production server: bash DEPLOY_DARK_MODE_FIX.sh

set -e  # Exit on any error

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║        VisaGuardAI - Dark Mode Fix Deployment                   ║"
echo "║        Results Page Styling Update                              ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
PROJECT_DIR="/var/www/visaguardai"
VENV_DIR="$PROJECT_DIR/venv"

# Step 1: Pull latest changes
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Pulling latest changes from GitHub..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd $PROJECT_DIR
git pull origin main
git submodule update --init --recursive

# Step 2: Activate virtual environment
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Activating virtual environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
source $VENV_DIR/bin/activate

# Step 3: Collect static files (templates are served directly, but just in case)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Collecting static files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py collectstatic --noinput

# Step 4: Clear any template caches
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Clearing template caches..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Step 5: Restart services
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Restarting services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo systemctl restart visaguardai.service
sudo systemctl reload nginx

# Verify services are running
sleep 2
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  Verifying services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet visaguardai.service; then
    echo "✅ Gunicorn service is running"
else
    echo "❌ Gunicorn service failed to start!"
    sudo systemctl status visaguardai.service --no-pager
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx service is running"
else
    echo "❌ Nginx service failed to start!"
    sudo systemctl status nginx --no-pager
    exit 1
fi

# Final confirmation
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DARK MODE FIX DEPLOYED SUCCESSFULLY!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Changes deployed:"
echo "   • Results page now consistently displays in dark mode"
echo "   • All light mode styling variants removed"
echo "   • Risk badges, profile cards, and legends updated"
echo ""
echo "🔍 Test the changes:"
echo "   • Visit: https://visaguardai.com/dashboard/results/"
echo "   • Verify all UI elements are in dark mode"
echo "   • Check tweet content boxes, profile summaries, and grade legend"
echo ""
echo "📝 If you see any cached light mode styling:"
echo "   • Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)"
echo "   • Clear browser cache if needed"
echo ""

