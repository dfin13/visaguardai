#!/bin/bash
# Quick verification script to check if signup fix is working
# Run this on production server AFTER deploying the fix

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║     Signup Fix Verification Script                              ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

PROJECT_DIR="/var/www/visaguardai"
cd $PROJECT_DIR

# Activate venv
source venv/bin/activate

echo "1️⃣  Checking Migration Status..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py showmigrations dashboard | tail -5
echo ""

echo "2️⃣  Checking if migration 0024 is applied..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python manage.py showmigrations dashboard | grep -q "\[X\] 0024_alter_userprofile_username"; then
    echo "✅ Migration 0024 is applied"
else
    echo "❌ Migration 0024 is NOT applied!"
    echo "   Run: python manage.py migrate"
fi
echo ""

echo "3️⃣  Checking UserProfile Model Schema..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py dbshell << 'EOF'
\d dashboard_userprofile
\q
EOF
echo ""

echo "4️⃣  Checking Service Status..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if systemctl is-active --quiet visaguardai.service; then
    echo "✅ visaguardai.service is running"
else
    echo "❌ visaguardai.service is NOT running"
fi

if systemctl is-active --quiet nginx; then
    echo "✅ nginx is running"
else
    echo "❌ nginx is NOT running"
fi
echo ""

echo "5️⃣  Recent Error Log (last 10 lines)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo tail -10 $PROJECT_DIR/logs/gunicorn_error.log
echo ""

echo "6️⃣  Checking for Recent Errors..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ERROR_COUNT=$(sudo tail -100 $PROJECT_DIR/logs/gunicorn_error.log | grep -i "IntegrityError\|NOT NULL constraint failed" | wc -l)
if [ $ERROR_COUNT -eq 0 ]; then
    echo "✅ No IntegrityError in recent logs (last 100 lines)"
else
    echo "⚠️  Found $ERROR_COUNT IntegrityError(s) in recent logs"
    echo "   These may be old errors from before the fix"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ VERIFICATION COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Next Steps:"
echo "   1. Test signup at: https://visaguardai.com/auth/signup/"
echo "   2. Monitor logs: sudo tail -f $PROJECT_DIR/logs/gunicorn_error.log"
echo "   3. Look for: '✅ UserProfile created for user:' in logs"
echo ""

