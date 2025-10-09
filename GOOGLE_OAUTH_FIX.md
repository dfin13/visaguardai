# Google OAuth Signup Flow - Complete Fix

## 🎯 Problem Solved

**Before:** Google OAuth users were not getting UserProfile created automatically, causing errors and broken flows.

**After:** New Google OAuth users get a complete account setup (User + UserProfile) and are automatically logged in and redirected to dashboard, identical to manual signup.

---

## ✅ What Was Fixed

### 1. Enhanced Signal Handlers (`dashboard/signals.py`)

**Fixed `save_user_profile` Signal:**
```python
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Check if profile exists before trying to save
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        # Create profile if it doesn't exist (safety net)
        UserProfile.objects.get_or_create(user=instance, defaults={'first_login': True})
```

**Added `user_signed_up` Handler:**
```python
@receiver(user_signed_up)
def user_signed_up_handler(request, user, **kwargs):
    # Ensures UserProfile exists for both manual and OAuth signups
    profile, created = UserProfile.objects.get_or_create(user=user, defaults={'first_login': True})
```

**Added `social_account_added` Handler:**
```python
@receiver(social_account_added)
def social_account_added_handler(request, sociallogin, **kwargs):
    # Ensures UserProfile exists when social account is linked
    user = sociallogin.user
    profile, created = UserProfile.objects.get_or_create(user=user, defaults={'first_login': True})
```

### 2. Custom Adapters (`dashboard/adapters.py` - NEW FILE)

**CustomSocialAccountAdapter:**
- Handles OAuth signup flow
- Connects existing users by email (prevents duplicates)
- Creates UserProfile automatically
- Populates user data from Google (first_name, last_name)
- Ensures proper redirect to dashboard

**CustomAccountAdapter:**
- Handles manual signup
- Ensures UserProfile creation as safety net
- Redirects to dashboard after signup/login

### 3. Settings Updates (`visaguardai/settings.py`)

**New Settings:**
```python
# Allauth settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_REDIRECT_URL = '/dashboard/'  # After signup
LOGIN_REDIRECT_URL = '/dashboard/'  # After login
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # Login with email
ACCOUNT_UNIQUE_EMAIL = True  # Ensure unique emails

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True  # Auto create account for new OAuth users
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'  # Skip email verification for OAuth
SOCIALACCOUNT_STORE_TOKENS = True  # Store OAuth tokens

# Custom adapters
ACCOUNT_ADAPTER = 'dashboard.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'dashboard.adapters.CustomSocialAccountAdapter'
```

---

## 🔄 OAuth Flow

### New User (First Time Google Sign-In):

1. User clicks "Sign in with Google"
2. Redirected to Google OAuth consent screen
3. User grants permissions
4. Google redirects back with OAuth token
5. **CustomSocialAccountAdapter.save_user()** called:
   - Creates new User object
   - Extracts email, first_name, last_name from Google
6. **Signal `post_save`** triggered → Creates UserProfile
7. **Signal `user_signed_up`** triggered → Ensures UserProfile exists
8. **Signal `social_account_added`** triggered → Safety net check
9. User automatically logged in
10. Redirected to `/dashboard/`

### Existing User (Return Visit):

1. User clicks "Sign in with Google"
2. Google authentication
3. **CustomSocialAccountAdapter.pre_social_login()** called:
   - Checks if email already exists
   - Connects OAuth to existing account (no duplicate)
4. User logged in
5. Redirected to `/dashboard/`

---

## 🛡️ Safety Nets (Multiple Layers)

The system has **4 layers** of UserProfile creation to ensure it never fails:

1. **Signal: post_save** - Creates profile when User is created
2. **Signal: user_signed_up** - Ensures profile exists after signup
3. **Signal: social_account_added** - Ensures profile for OAuth users
4. **Adapter: save_user()** - Final safety net in adapter

Even if one fails, the others will catch it!

---

## 📊 Database Models

### User (Django Built-in)
```python
username: str
email: str (unique)
first_name: str
last_name: str
password: str (hashed)
```

### SocialAccount (django-allauth)
```python
user: ForeignKey(User)
provider: str  # "google"
uid: str  # Google user ID
extra_data: JSONField  # OAuth data
```

### UserProfile (Custom)
```python
user: OneToOneField(User)
first_login: bool
instagram: str (optional)
linkedin: str (optional)
twitter: str (optional)
facebook: str (optional)
payment_completed: bool
```

---

## 🧪 Testing Instructions

### Test 1: New OAuth User

1. Clear browser cookies/use incognito
2. Go to https://visaguardai.com/auth/login/
3. Click "Sign in with Google"
4. Select a Google account NOT previously used
5. Grant permissions
6. **Expected Result:**
   - ✅ User created in database
   - ✅ UserProfile created
   - ✅ Logged in automatically
   - ✅ Redirected to /dashboard/
   - ✅ No errors

### Test 2: Existing OAuth User

1. Use same Google account from Test 1
2. Click "Sign in with Google"
3. **Expected Result:**
   - ✅ Logged in immediately
   - ✅ Redirected to /dashboard/
   - ✅ No duplicate account created
   - ✅ No errors

### Test 3: Email Collision (OAuth + Manual)

1. Create manual account with email: test@example.com
2. Logout
3. Try to sign in with Google using test@example.com
4. **Expected Result:**
   - ✅ Google OAuth links to existing account
   - ✅ No duplicate created
   - ✅ User can login with both methods

### Test 4: Manual Signup (Still Works)

1. Go to /auth/signup/
2. Fill out manual signup form
3. Submit
4. **Expected Result:**
   - ✅ User created
   - ✅ UserProfile created
   - ✅ Logged in automatically
   - ✅ Redirected to /dashboard/

---

## 🔍 Debugging

### Check Logs (Production)
```bash
ssh root@148.230.110.112
journalctl -u visaguardai -f | grep -E "UserProfile|OAuth|Google"
```

### Expected Log Messages:
```
✅ UserProfile created for user: john@example.com (ID: 123)
✅ Populated user data from Google: john@example.com
✅ UserProfile created for OAuth user: john@example.com via google
```

### Check Database (Production)
```bash
ssh root@148.230.110.112
cd /var/www/visaguardai
source venv/bin/activate
python3 manage.py shell
```

```python
from django.contrib.auth.models import User
from dashboard.models import UserProfile
from allauth.socialaccount.models import SocialAccount

# Check OAuth user
user = User.objects.get(email='test@example.com')
print(f"User: {user.username}, Email: {user.email}")

# Check profile
profile = user.userprofile
print(f"Profile exists: {profile is not None}")
print(f"First login: {profile.first_login}")

# Check social account
social = SocialAccount.objects.filter(user=user).first()
if social:
    print(f"OAuth Provider: {social.provider}")
    print(f"OAuth Email: {social.extra_data.get('email')}")
```

---

## 🚨 Troubleshooting

### Issue: "UserProfile matching query does not exist"

**Cause:** Signal not firing or adapter not creating profile

**Fix:** Already fixed with multiple safety nets. If still occurs:
```python
# Manual fix in Django shell
from django.contrib.auth.models import User
from dashboard.models import UserProfile

user = User.objects.get(email='problem@example.com')
UserProfile.objects.create(user=user, first_login=True)
```

### Issue: "User with this Email already exists"

**Cause:** Trying to create duplicate user

**Fix:** Already handled by `pre_social_login` which connects OAuth to existing account

### Issue: Not redirected to dashboard

**Cause:** LOGIN_REDIRECT_URL not set or adapter override missing

**Fix:** Already set in settings.py and adapters.py

---

## 📋 Configuration Checklist

✅ django-allauth installed in INSTALLED_APPS
✅ Google OAuth app configured in Django admin
✅ SITE_ID = 1 in settings.py
✅ Custom adapters configured
✅ Signals connected in apps.py
✅ LOGIN_REDIRECT_URL = '/dashboard/'
✅ SOCIALACCOUNT_AUTO_SIGNUP = True
✅ Multiple UserProfile creation safety nets

---

## 🔐 Security Notes

- OAuth tokens are stored securely in database
- CSRF protection enabled
- Session cookies are secure (HTTPS only)
- No sensitive data logged
- Email uniqueness enforced
- Password not stored for OAuth users (handled by Google)

---

## 📚 References

- Django Allauth: https://django-allauth.readthedocs.io/
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Django Signals: https://docs.djangoproject.com/en/stable/topics/signals/

---

**Status:** ✅ DEPLOYED & WORKING
**Date:** 2025-10-09
**Version:** 1.0

