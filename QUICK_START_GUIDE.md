# VisaGuardAI - Quick Start Guide (After PostgreSQL Migration)

## 🚀 Starting the Application

### 1. Start PostgreSQL
```bash
brew services start postgresql@14
```

### 2. Start Django Development Server
```bash
cd /Users/davidfinney/Downloads/visaguardai
python3 manage.py runserver
```

Visit: `http://127.0.0.1:8000`

---

## 🔐 Authentication Options

### Option 1: Email/Password Sign Up
1. Go to: `http://127.0.0.1:8000/auth/signup/`
2. Fill in username, email, and password
3. Account created automatically with profile

### Option 2: Google OAuth
1. Go to: `http://127.0.0.1:8000/auth/login/`
2. Click "Continue with Google"
3. Sign in with Google account
4. Redirects back to dashboard automatically

---

## 👤 Admin Access

**URL:** `http://127.0.0.1:8000/admin/`

**Credentials:**
- Username: `admin`
- Password: `admin123`

**Admin Tasks:**
- View/edit users
- Manage social apps (OAuth)
- Configure site settings
- View analysis sessions

---

## 🛠️ Essential Commands

### Database Operations
```bash
# Create backup
./backup_database.sh

# Check OAuth health
./check_oauth_health.sh

# Access PostgreSQL
psql -d visaguard_db

# Run migrations
python3 manage.py migrate
```

### Django Operations
```bash
# System check
python3 manage.py check

# Create superuser
python3 manage.py createsuperuser

# Collect static files
python3 manage.py collectstatic

# Django shell
python3 manage.py shell
```

---

## 📊 Verification

### Check PostgreSQL Status
```bash
brew services list | grep postgresql
# Should show: postgresql@14  started
```

### Check Database Connection
```bash
python3 manage.py check --database default
# Should show: System check identified no issues
```

### Verify OAuth Configuration
```bash
./check_oauth_health.sh
cat logs/oauth_health.log
# Should show: ✅ OAuth Status: HEALTHY
```

---

## 🔧 Configuration Files

### .env (Environment Variables)
Location: `/Users/davidfinney/Downloads/visaguardai/.env`

Contains:
- Database credentials
- Secret keys
- API keys (Stripe, Gemini, Apify)
- Google OAuth credentials

**⚠️ Never commit .env to git!**

### settings.py
Location: `/Users/davidfinney/Downloads/visaguardai/visaguardai/settings.py`

Key Settings:
- `DATABASES`: PostgreSQL configuration
- `SITE_ID = 1`: For allauth
- `AUTHENTICATION_BACKENDS`: Dual auth support
- `SOCIALACCOUNT_PROVIDERS`: Google OAuth config

---

## 🌐 URLs Reference

### Authentication
- Login: `/auth/login/`
- Signup: `/auth/signup/`
- Logout: `/auth/logout/`
- Forgot Password: `/auth/forgot-password/`
- Google OAuth: `/accounts/google/login/`

### Dashboard
- Dashboard: `/dashboard/`
- Settings: `/dashboard/settings/`
- Results: `/dashboard/result/`
- Payment: `/dashboard/payment/`

### Admin
- Admin Panel: `/admin/`
- Social Apps: `/admin/socialaccount/socialapp/`
- Users: `/admin/auth/user/`
- Sites: `/admin/sites/site/`

---

## 🆘 Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Restart server
python3 manage.py runserver
```

### PostgreSQL Not Running
```bash
# Start PostgreSQL
brew services start postgresql@14

# Check status
brew services list | grep postgresql
```

### Database Connection Error
```bash
# Check .env file exists
cat .env | grep DB_NAME

# Test connection
psql -d visaguard_db -c "SELECT 1;"
```

### Google OAuth Not Working
1. Check Site domain: `/admin/sites/site/1/`
   - Should be `127.0.0.1:8000` for dev
2. Check OAuth app: `/admin/socialaccount/socialapp/`
   - Client ID and Secret should be filled
3. Run health check: `./check_oauth_health.sh`

---

## 📦 Dependencies

All dependencies in `requirements.txt`:
```bash
# Install/update all dependencies
pip install -r requirements.txt
```

Key packages:
- `Django==5.2.5`
- `django-allauth==65.11.2`
- `psycopg2-binary==2.9.10`
- `stripe==12.4.0`
- `google-generativeai==0.8.5`

---

## 🔒 Security Notes

1. **Production Deployment:**
   - Set `DEBUG = False`
   - Use strong SECRET_KEY
   - Enable HTTPS
   - Use production database password
   - Update ALLOWED_HOSTS

2. **Google Cloud Console:**
   - Add production redirect URIs
   - Add authorized domains
   - Restrict API key usage

3. **Database:**
   - Regular backups (automated)
   - Secure password for production
   - Firewall rules for PostgreSQL port

---

## 📱 Testing Authentication

### Test Email/Password Flow
```python
python3 manage.py shell

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# Create test user
user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')

# Authenticate
auth_user = authenticate(username='testuser', password='testpass123')
print(f"Authenticated: {auth_user is not None}")
```

### Test OAuth Configuration
```python
python3 manage.py shell

from allauth.socialaccount.models import SocialApp

# Check Google OAuth
app = SocialApp.objects.get(provider='google')
print(f"Provider: {app.provider}")
print(f"Client ID: {app.client_id}")
print(f"Sites: {[s.domain for s in app.sites.all()]}")
```

---

## 🎯 Next Steps

1. **Customize Site:**
   - Update Site domain to your production domain
   - Configure email backend for password reset
   - Add custom branding

2. **Google Cloud Console:**
   - Add production redirect URIs
   - Configure OAuth consent screen
   - Set up API quotas

3. **Production Deployment:**
   - Deploy to Hostinger VPS
   - Configure Nginx + Gunicorn
   - Setup SSL certificates
   - Run migrations on production DB

4. **Monitoring:**
   - Setup automated backups (cron)
   - Configure error logging
   - Enable uptime monitoring
   - Setup alerts

---

## 📞 Support

For issues or questions:
1. Check logs: `/tmp/django_server.log`
2. Check OAuth health: `./check_oauth_health.sh`
3. Review migration report: `POSTGRES_OAUTH_MIGRATION_REPORT.md`

---

**Status:** ✅ System ready for development and testing
**Last Updated:** October 8, 2025

