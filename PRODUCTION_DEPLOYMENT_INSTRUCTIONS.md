# Production Deployment Instructions

## 📋 Prerequisites

Before deploying, ensure you have:

1. ✅ SSH access to your Hostinger VPS (root@148.230.110.112)
2. ✅ PostgreSQL installed on production server
3. ✅ Production database credentials ready
4. ✅ Google Cloud Console configured with production redirect URI
5. ✅ SSL certificate active for visaguardai.com

---

## 🚀 Deployment Steps

### Option 1: Automated Deployment (Recommended)

SSH into your production server and run the deployment script:

```bash
# SSH into your server
ssh root@148.230.110.112

# Navigate to project directory
cd /var/www/visaguardai

# Pull latest changes
git pull origin main

# Run deployment script
./deploy_to_production.sh
```

The script will automatically:
- Pull latest code
- Install dependencies
- Check PostgreSQL
- Create backups
- Run migrations
- Configure OAuth
- Collect static files
- Restart services

---

### Option 2: Manual Step-by-Step Deployment

If you prefer manual control:

#### Step 1: SSH into Server
```bash
ssh root@148.230.110.112
cd /var/www/visaguardai
```

#### Step 2: Install PostgreSQL (if not installed)
```bash
# Check if PostgreSQL is installed
psql --version

# If not installed:
sudo apt update
sudo apt install -y postgresql postgresql-contrib libpq-dev

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Step 3: Create Production Database
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE visaguard_db;
CREATE USER visaguard_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE visaguard_user SET client_encoding TO 'utf8';
ALTER ROLE visaguard_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE visaguard_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE visaguard_db TO visaguard_user;
\q
```

#### Step 4: Create Production .env File
```bash
# Copy the template
cp .env.production.template .env

# Edit with your production credentials
nano .env
```

**Required values to update:**
- `SECRET_KEY` - Generate a new one: `python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- `DB_PASSWORD` - Your PostgreSQL password
- `STRIPE_PUBLISHABLE_KEY_LIVE` - From Stripe dashboard
- `STRIPE_SECRET_KEY_LIVE` - From Stripe dashboard

#### Step 5: Pull Latest Code
```bash
git pull origin main
```

#### Step 6: Install Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 7: Migrate Data from SQLite (if needed)
```bash
# Export data from SQLite (if you have existing data)
python manage.py dumpdata --natural-foreign --natural-primary \
    -e contenttypes -e auth.Permission \
    > sqlite_backup.json

# Update settings to use PostgreSQL (already done in settings.py)

# Run migrations to create tables in PostgreSQL
python manage.py migrate

# Load data into PostgreSQL
python manage.py loaddata sqlite_backup.json
```

#### Step 8: Configure Site and OAuth for Production
```bash
python manage.py shell << 'EOF'
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import os

# Update Site for production
site = Site.objects.get_current()
site.domain = 'visaguardai.com'
site.name = 'VisaGuardAI'
site.save()
print(f"✅ Site: {site.domain}")

# Configure Google OAuth
app, created = SocialApp.objects.get_or_create(
    provider='google',
    defaults={'name': 'Google OAuth'}
)
app.client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
app.secret = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')
app.save()
app.sites.set([site])
print(f"✅ OAuth configured: {app.client_id[:20]}...")
EOF
```

#### Step 9: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

#### Step 10: Restart Services
```bash
sudo systemctl restart visaguardai.service
sudo systemctl restart nginx
```

#### Step 11: Verify Services
```bash
# Check service status
sudo systemctl status visaguardai.service
sudo systemctl status nginx

# Check logs
sudo journalctl -u visaguardai.service -n 50 --no-pager

# Test OAuth health
./check_oauth_health.sh
```

---

## 🔧 Google Cloud Console Configuration

**CRITICAL:** Update your Google Cloud Console settings:

1. Go to: https://console.cloud.google.com/
2. Select your project
3. Navigate to: APIs & Services → Credentials
4. Edit your OAuth 2.0 Client ID
5. Add to **Authorized redirect URIs**:
   ```
   https://visaguardai.com/accounts/google/login/callback/
   ```
6. Add to **Authorized domains**:
   ```
   visaguardai.com
   ```
7. Save changes

---

## ✅ Post-Deployment Verification

### Test All Authentication Methods

1. **Traditional Login**
   ```bash
   curl -I https://visaguardai.com/auth/login/
   # Should return: HTTP/2 200
   ```

2. **Google OAuth**
   ```bash
   curl -I https://visaguardai.com/accounts/google/login/
   # Should return: HTTP/2 302 (redirect to Google)
   ```

3. **Admin Panel**
   ```bash
   curl -I https://visaguardai.com/admin/
   # Should return: HTTP/2 302 (redirect to login)
   ```

### Verify Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql -d visaguard_db

# Check tables
\dt

# Check OAuth configuration
SELECT provider, name FROM socialaccount_socialapp;

# Check site configuration
SELECT domain, name FROM django_site;

# Exit
\q
```

### Check OAuth Health

```bash
./check_oauth_health.sh
cat logs/oauth_health.log
```

---

## 🔄 Rollback Plan (If Something Goes Wrong)

If deployment fails, you can rollback:

```bash
# Restore previous code version
git reset --hard HEAD~1

# Restore database from backup
pg_restore -d visaguard_db backups/latest_backup.sql.gz

# Restart services
sudo systemctl restart visaguardai.service nginx
```

---

## 📊 Monitoring & Maintenance

### Regular Backups

Schedule automated backups:

```bash
# Add to crontab
crontab -e

# Add this line for daily backups at 3 AM:
0 3 * * * cd /var/www/visaguardai && ./backup_database.sh >> logs/backup.log 2>&1
```

### OAuth Health Checks

```bash
# Weekly health check
crontab -e

# Add this line for weekly checks on Sundays:
0 3 * * 0 cd /var/www/visaguardai && ./check_oauth_health.sh
```

### View Logs

```bash
# Application logs
sudo journalctl -u visaguardai.service -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# OAuth health logs
tail -f logs/oauth_health.log
```

---

## 🆘 Troubleshooting

### Issue: "OperationalError: could not connect to server"

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql

# Check connection
psql -d visaguard_db -U visaguard_user -h localhost
```

### Issue: "Google OAuth redirect mismatch"

**Solution:**
1. Check Site domain: `python manage.py shell -c "from django.contrib.sites.models import Site; print(Site.objects.get_current().domain)"`
2. Verify it matches Google Cloud Console redirect URI
3. Ensure redirect URI is: `https://visaguardai.com/accounts/google/login/callback/`

### Issue: "502 Bad Gateway"

**Solution:**
```bash
# Check Gunicorn status
sudo systemctl status visaguardai.service

# Restart services
sudo systemctl restart visaguardai.service nginx

# Check for errors
sudo journalctl -u visaguardai.service -n 50
```

### Issue: "Static files not loading"

**Solution:**
```bash
# Recollect static files
python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## 📞 Support

If you encounter issues:

1. Check logs: `sudo journalctl -u visaguardai.service -n 100`
2. Run health check: `./check_oauth_health.sh`
3. Verify database connection: `python manage.py check --database default`
4. Review documentation: `POSTGRES_OAUTH_MIGRATION_REPORT.md`

---

## ✨ Success Checklist

After deployment, verify:

- [ ] Website loads: https://visaguardai.com
- [ ] Traditional login works
- [ ] Google OAuth login works
- [ ] Admin panel accessible
- [ ] User profiles auto-created
- [ ] Database queries working
- [ ] Static files loading
- [ ] SSL certificate valid
- [ ] Services running (Gunicorn + Nginx)
- [ ] Backups automated
- [ ] OAuth health monitoring active

---

**Deployment Date:** $(date)
**Status:** Ready for Production
**Documentation:** Complete

