# 🚨 URGENT: Google OAuth Secret Rotation Guide

**Priority:** 🔴 **CRITICAL**  
**Deadline:** Within 24 hours  
**Reason:** OAuth Client Secret was exposed in Git history for ~8 hours

---

## Quick Action Steps

### Step 1: Access Google Cloud Console
1. Go to: https://console.cloud.google.com/
2. Sign in with your Google account
3. Select your project (or the one with OAuth credentials)

### Step 2: Navigate to Credentials
1. Click **"APIs & Services"** in left menu
2. Click **"Credentials"**
3. Find your OAuth 2.0 Client ID:
   - Should show: `1095815216076-2dorkvubbmhanjpi5cad3ndas6m0bo98.apps.googleusercontent.com`

### Step 3: Create New Client Secret
1. Click on the OAuth 2.0 Client ID
2. In the **"Client secrets"** section:
   - Click **"Add Secret"** (if available)
   - OR click the **menu (⋮)** next to existing secret → **"Reset"**
3. Copy the new secret (it will look like: `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
4. **Save it immediately** - you can't see it again!

### Step 4: Update Production Server
```bash
# SSH into production
ssh root@148.230.110.112

# Navigate to project
cd /var/www/visaguardai

# Edit .env file
nano .env

# Find this line:
# GOOGLE_OAUTH2_CLIENT_SECRET=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

# Replace with your new secret:
# GOOGLE_OAUTH2_CLIENT_SECRET=GOCSPX-YOUR-NEW-SECRET-HERE

# Save (Ctrl+O, Enter, Ctrl+X)
```

### Step 5: Update Database
```bash
# Still on production server
source venv/bin/activate

python manage.py shell << 'EOFPYTHON'
from allauth.socialaccount.models import SocialApp

# Update the Google OAuth app
app = SocialApp.objects.get(provider='google')
app.secret = 'GOCSPX-YOUR-NEW-SECRET-HERE'  # Use your new secret
app.save()

print(f"✅ OAuth secret updated: {app.secret[:10]}...")
EOFPYTHON
```

### Step 6: Restart Services
```bash
# Restart Gunicorn to load new .env
sudo systemctl restart visaguardai.service

# Check status
sudo systemctl status visaguardai.service

# Verify no errors
sudo journalctl -u visaguardai.service -n 20 --no-pager
```

### Step 7: Test Google OAuth Login
1. Visit: https://visaguardai.com/auth/login/
2. Click **"Continue with Google"**
3. Complete OAuth flow
4. Verify you're redirected to dashboard

If successful: ✅ OAuth rotation complete!

### Step 8: Delete Old Secret
1. Go back to Google Cloud Console
2. Find the **old secret** (compromised one)
3. Click menu (⋮) → **"Delete"**
4. Confirm deletion

✅ **Old secret permanently revoked**

---

## Verification Checklist

After rotation, verify:

- [ ] New secret saved in production .env
- [ ] Database updated with new secret
- [ ] Services restarted successfully
- [ ] Google OAuth login works
- [ ] Users can sign in with Google
- [ ] Old secret deleted from Google Cloud Console

---

## If OAuth Login Fails After Rotation

### Check 1: Verify Secret in .env
```bash
cat /var/www/visaguardai/.env | grep GOOGLE_OAUTH2_CLIENT_SECRET
# Should show new secret (GOCSPX-...)
```

### Check 2: Verify Database
```bash
python manage.py shell -c "from allauth.socialaccount.models import SocialApp; app = SocialApp.objects.get(provider='google'); print(app.secret[:10])"
# Should show new secret prefix
```

### Check 3: Check Logs
```bash
sudo journalctl -u visaguardai.service -f
# Watch for OAuth errors
```

### Check 4: Verify Redirect URI
In Google Cloud Console, ensure authorized redirect URIs include:
- `https://visaguardai.com/accounts/google/login/callback/`
- `http://127.0.0.1:8000/accounts/google/login/callback/` (for local testing)

---

## Timeline

- **Oct 8, 17:43** - Secret exposed in commit 4a900d7
- **Oct 9, 01:40** - Secret removed from git history
- **Oct 9, 01:41** - Force pushed to GitHub
- **Within 24 hrs** - Secret must be rotated ⚠️

---

## Why This Is Critical

The exposed OAuth Client Secret could allow:
- Impersonation of your application
- Unauthorized OAuth authentication
- Access to user Google accounts via your OAuth app
- Reputation damage

**Even though we removed it from git, it was public for ~8 hours, so rotation is mandatory.**

---

## After Rotation

Update your local .env file too:
```bash
# On your local machine
cd /Users/davidfinney/Downloads/visaguardai
nano .env
# Update GOOGLE_OAUTH2_CLIENT_SECRET with new value
```

---

## Support

If you need help:
1. Check: `SECURITY_INCIDENT_REPORT.md` (full details)
2. Run: `./check_oauth_health.sh` (after rotation)
3. Test: Local dev server first before production

---

**🔴 DO NOT DELAY - Rotate the Google OAuth secret today!**

