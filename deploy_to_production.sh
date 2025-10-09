#!/bin/bash
# Production Deployment Script for VisaGuardAI
# PostgreSQL + Google OAuth Migration

set -e  # Exit on any error

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║        VisaGuardAI Production Deployment                        ║"
echo "║        PostgreSQL + Google OAuth Migration                      ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
PROJECT_DIR="/var/www/visaguardai"
VENV_DIR="$PROJECT_DIR/venv"
BACKUP_DIR="$PROJECT_DIR/backups"

echo "📂 Project Directory: $PROJECT_DIR"
echo ""

# Step 1: Pull latest changes
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Pulling latest changes from GitHub..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd $PROJECT_DIR
git pull origin main

# Step 2: Activate virtual environment
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Activating virtual environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
source $VENV_DIR/bin/activate

# Step 3: Install/update dependencies
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Installing dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pip install -r requirements.txt --quiet

# Step 4: Check if PostgreSQL is installed
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Checking PostgreSQL..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL is installed"
    psql --version
else
    echo "❌ PostgreSQL not found! Please install it first:"
    echo "   sudo apt update"
    echo "   sudo apt install -y postgresql postgresql-contrib"
    exit 1
fi

# Step 5: Check database connection
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Checking database connection..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(cat $PROJECT_DIR/.env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "❌ .env file not found! Please create it with production credentials."
    exit 1
fi

python manage.py check --database default
if [ $? -eq 0 ]; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed! Check your .env file."
    exit 1
fi

# Step 6: Backup existing database (if SQLite exists)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  Creating backup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
mkdir -p $BACKUP_DIR

if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
    echo "📦 Backing up existing SQLite database..."
    python manage.py dumpdata --natural-foreign --natural-primary \
        -e contenttypes -e auth.Permission \
        > $BACKUP_DIR/sqlite_data_backup_$(date +%Y%m%d_%H%M%S).json
    echo "✅ SQLite data exported to JSON"
fi

# Backup current PostgreSQL database
echo "📦 Backing up PostgreSQL database..."
pg_dump $DB_NAME -h $DB_HOST -U $DB_USER > $BACKUP_DIR/postgres_backup_$(date +%Y%m%d_%H%M%S).sql
gzip $BACKUP_DIR/postgres_backup_$(date +%Y%m%d_%H%M%S).sql
echo "✅ PostgreSQL backup created"

# Step 7: Run migrations
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  Running migrations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py migrate

# Step 8: Configure Google OAuth for production
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  Configuring Google OAuth for production..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python manage.py shell << 'EOFPYTHON'
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import os

# Update Site for production
site = Site.objects.get_current()
site.domain = 'visaguardai.com'
site.name = 'VisaGuardAI'
site.save()
print(f"✅ Site updated: {site.domain}")

# Configure Google OAuth
app, created = SocialApp.objects.get_or_create(
    provider='google',
    defaults={'name': 'Google OAuth'}
)
app.client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
app.secret = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')
app.save()
app.sites.set([site])

status = "Created" if created else "Updated"
print(f"✅ Google OAuth {status.lower()}: {app.client_id[:20]}...")
EOFPYTHON

# Step 9: Collect static files
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9️⃣  Collecting static files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py collectstatic --noinput

# Step 10: Run health checks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔟  Running health checks..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py check

# Make backup and health check scripts executable
chmod +x backup_database.sh check_oauth_health.sh
echo "✅ Scripts made executable"

# Step 11: Restart services
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣1️⃣  Restarting services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo systemctl restart visaguardai.service
sudo systemctl restart nginx

# Verify services are running
sleep 2
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

# Final verification
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Application URLs:"
echo "   • Main site: https://visaguardai.com"
echo "   • Login: https://visaguardai.com/auth/login/"
echo "   • Admin: https://visaguardai.com/admin/"
echo "   • Google OAuth: https://visaguardai.com/accounts/google/login/"
echo ""
echo "🔧 Useful commands:"
echo "   • Check OAuth health: ./check_oauth_health.sh"
echo "   • Create backup: ./backup_database.sh"
echo "   • View logs: sudo journalctl -u visaguardai.service -f"
echo "   • Restart services: sudo systemctl restart visaguardai.service nginx"
echo ""
echo "📝 Important reminders:"
echo "   1. Verify Google Cloud Console has production redirect URI:"
echo "      https://visaguardai.com/accounts/google/login/callback/"
echo "   2. Ensure SSL certificate is valid"
echo "   3. Test both authentication methods"
echo ""

