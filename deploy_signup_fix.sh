#!/bin/bash
# Emergency Deployment Script - Fix Email/Password Signup 500 Error
# This script fixes the IntegrityError caused by the UserProfile.username field

set -e  # Exit on any error

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║     Email/Password Signup Fix - Emergency Deployment            ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
PROJECT_DIR="/var/www/visaguardai"
VENV_DIR="$PROJECT_DIR/venv"

echo "📂 Project Directory: $PROJECT_DIR"
echo ""

# Step 1: Navigate to project
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Navigating to project directory..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd $PROJECT_DIR

# Step 2: Pull latest changes
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Pulling latest changes from GitHub..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git pull origin main

# Step 3: Activate virtual environment
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Activating virtual environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
source $VENV_DIR/bin/activate

# Step 4: Show pending migrations
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Checking pending migrations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py showmigrations dashboard

# Step 5: Run the critical migration
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Running migration 0024_alter_userprofile_username..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py migrate dashboard 0024

# Step 6: Run all remaining migrations
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  Running all migrations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py migrate

# Step 7: Restart Gunicorn service
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  Restarting Gunicorn service..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo systemctl restart visaguardai.service

# Step 8: Check service status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  Checking service status..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sleep 2
if systemctl is-active --quiet visaguardai.service; then
    echo "✅ Gunicorn service is running"
else
    echo "❌ Gunicorn service failed to start!"
    sudo systemctl status visaguardai.service --no-pager
    exit 1
fi

# Step 9: Show recent logs
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9️⃣  Recent logs (last 20 lines)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo tail -20 $PROJECT_DIR/logs/gunicorn_error.log

# Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔍 What was fixed:"
echo "   • UserProfile.username field now allows blank values"
echo "   • Signal handlers deduplicated and error handling improved"
echo "   • Email/password signup should now work without 500 errors"
echo ""
echo "🧪 Testing Instructions:"
echo "   1. Go to: https://visaguardai.com/auth/signup/"
echo "   2. Fill in signup form with:"
echo "      - Username: testuser$(date +%s)"
echo "      - Email: test$(date +%s)@example.com"
echo "      - Password: (at least 12 characters)"
echo "   3. Complete reCAPTCHA and submit"
echo "   4. Should redirect to dashboard successfully"
echo ""
echo "📊 Monitor logs in real-time:"
echo "   sudo tail -f $PROJECT_DIR/logs/gunicorn_error.log"
echo ""
echo "🔍 Check for these success messages:"
echo "   ✅ UserProfile created for user: USERNAME (ID: X)"
echo ""
echo "⚠️  If issues persist:"
echo "   1. Check: python manage.py showmigrations dashboard"
echo "   2. Check logs: sudo tail -100 $PROJECT_DIR/logs/gunicorn_error.log"
echo "   3. Verify database: python manage.py dbshell"
echo "   4. Check signal loading: python manage.py shell"
echo ""

