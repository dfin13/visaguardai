# Email/Password Signup 500 Error - Fix Report

## Issue Identified

**Problem:** Email/password signups are failing with HTTP 500 errors, while Google OAuth signups work perfectly.

## Root Cause

After analyzing the code, I identified **two critical issues**:

### 1. **UserProfile.username Field Constraint**
- Location: `dashboard/models.py` line 8
- The `username` field in the UserProfile model was defined as:
  ```python
  username = models.CharField(max_length=150, )  # NOT NULL, no default
  ```
- When a user signs up via email/password, Django's `User.objects.create_user()` creates a User object
- The signal handler (`dashboard/signals.py`) then tries to create a UserProfile
- **BUT** the UserProfile creation fails because the `username` field is NOT NULL with no default value
- This causes an `IntegrityError` and results in a 500 error

### 2. **Duplicate Signal Handlers**
- Location: `dashboard/signals.py`
- The signals file had duplicate handler functions (lines 8-54 were duplicated in lines 57-95)
- Line 55 had a critical bug referencing undefined variable `instance`
- This could cause signal failures or unpredictable behavior

## Fixes Applied

### Fix #1: UserProfile.username Field
**File:** `dashboard/models.py`

Changed:
```python
username = models.CharField(max_length=150, )
```

To:
```python
username = models.CharField(max_length=150, blank=True, default='')
```

**Migration Created:** `dashboard/migrations/0024_alter_userprofile_username.py`

### Fix #2: Signal Handlers
**File:** `dashboard/signals.py`

- Removed all duplicate signal handlers
- Fixed the undefined `instance` variable bug
- Added proper error handling with try-except blocks
- Ensured graceful fallbacks for UserProfile creation

### Fix #3: Better Error Handling
Added comprehensive error logging in all signal handlers to help debug future issues:
- `create_user_profile` - logs errors during profile creation
- `save_user_profile` - logs errors during profile saving
- `user_signed_up_handler` - logs errors during signup
- `social_account_added_handler` - logs errors during OAuth

## Deployment Instructions

### Step 1: Deploy to Production Server

SSH into your production server and run:

```bash
ssh your-server

cd /var/www/visaguardai
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Run the new migration
python manage.py migrate

# Restart services
sudo systemctl restart visaguardai.service
sudo systemctl restart nginx
```

### Step 2: Verify the Fix

1. **Check logs in real-time:**
   ```bash
   sudo tail -f /var/www/visaguardai/logs/gunicorn_error.log
   ```

2. **Test email/password signup:**
   - Go to https://visaguardai.com/auth/signup/
   - Fill in the signup form with test credentials
   - Submit and verify successful signup

3. **Check for any errors:**
   ```bash
   # View recent errors
   sudo tail -100 /var/www/visaguardai/logs/gunicorn_error.log
   
   # Check service status
   sudo systemctl status visaguardai.service
   ```

### Step 3: Monitor Production Logs

After deployment, monitor for these success indicators:
- ✅ "UserProfile created for user: USERNAME (ID: X)"
- ✅ Successful redirects to dashboard after signup
- ❌ No more IntegrityError messages

## Why Google OAuth Was Working

Google OAuth signups were working because:
1. Allauth creates the User object differently
2. The `social_account_added` signal handler has additional fallback logic
3. The signal may have been creating profiles with different timing

But email/password signups went through a different code path that exposed the schema constraint issue.

## Testing Checklist

- [ ] Deploy fixes to production
- [ ] Run migration `0024_alter_userprofile_username.py`
- [ ] Test email/password signup with new account
- [ ] Test email/password login with newly created account
- [ ] Verify Google OAuth still works
- [ ] Check error logs for any new issues
- [ ] Test password reset flow
- [ ] Verify user can access dashboard after signup

## Files Modified

1. `dashboard/models.py` - Fixed username field constraint
2. `dashboard/signals.py` - Removed duplicates, added error handling
3. `dashboard/migrations/0024_alter_userprofile_username.py` - New migration
4. `check_production_logs.sh` - Helper script for log checking
5. `deploy_signup_fix.sh` - Automated deployment script
6. `test_signup_fix_local.py` - Local testing script

## Additional Notes

### Log Checking Script
Created `check_production_logs.sh` with commands to check production logs. Make it executable:
```bash
chmod +x check_production_logs.sh
./check_production_logs.sh
```

### Future Considerations

1. **Consider removing the username field entirely** from UserProfile if it's redundant with User.username
2. **Add database constraints validation** in CI/CD pipeline
3. **Implement better error pages** that don't expose sensitive error details
4. **Set up error monitoring** (like Sentry) to catch these issues proactively

## Contact

If issues persist after deployment, check:
1. Migration was applied: `python manage.py showmigrations dashboard`
2. Services restarted successfully
3. No other pending migrations
4. Database constraints are correct

Created: October 28, 2025

