#!/bin/bash
# OAuth Health Check Script for VisaGuardAI

LOG_FILE="/Users/davidfinney/Downloads/visaguardai/logs/oauth_health.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "=== OAuth Health Check - $(date) ===" >> "$LOG_FILE"

cd /Users/davidfinney/Downloads/visaguardai

# Check if Google OAuth app exists in database
python3 manage.py shell << 'EOF' >> "$LOG_FILE" 2>&1
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

try:
    app = SocialApp.objects.get(provider='google')
    site = Site.objects.get_current()
    
    print("✅ OAuth Status: HEALTHY")
    print(f"   Provider: {app.provider}")
    print(f"   Client ID: {app.client_id[:20]}...")
    print(f"   Sites: {[s.domain for s in app.sites.all()]}")
    print(f"   Current Site: {site.domain}")
    
    # Verify credentials are not empty
    if not app.client_id or not app.secret:
        print("⚠️  WARNING: OAuth credentials are empty!")
        exit(1)
    
except SocialApp.DoesNotExist:
    print("❌ OAuth Status: MISSING - Google OAuth app not found!")
    exit(1)
except Exception as e:
    print(f"❌ OAuth Status: ERROR - {str(e)}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo "✅ Health check passed" >> "$LOG_FILE"
else
    echo "❌ Health check failed" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

