# VisaGuardAI - User Data Storage Map

**Analysis Date:** 2025-10-16  
**Purpose:** Complete map of where and how user data is stored in the VisaGuardAI system

---

## 📊 Executive Summary

**Primary Storage:** PostgreSQL Database  
**Session Backend:** Database (`django_session` table)  
**Cache Backend:** Database (`django_cache_table`)  
**Media Storage:** Filesystem (`/media/profile_pictures/`)  

**Key Finding:** All user data is stored in PostgreSQL, including sessions and cache. No Redis, no file-based storage for analysis data.

---

## 1️⃣ Database Models (PostgreSQL)

### **1.1 UserProfile Model**
**Location:** `dashboard/models.py` (lines 4-25)

**Purpose:** Stores user profile information and social media connections

**Fields:**
```python
- user (OneToOneField → auth.User) [CASCADE DELETE]
- username (CharField, max=150)
- tiktok (CharField, max=150, nullable)
- instagram (CharField, max=150, nullable)
- linkedin (CharField, max=150, nullable)
- facebook (CharField, max=150, nullable)
- instagram_connected (Boolean, default=False)
- tiktok_connected (Boolean, default=False)
- linkedin_connected (Boolean, default=False)
- facebook_connected (Boolean, default=False)
- first_login (Boolean, default=True)
- profile_picture (ImageField, upload_to='profile_pictures/', nullable)
- country (CharField, max=100, nullable)
- university (CharField, max=100, nullable)
- payment_completed (Boolean, default=False)
- updated_at (DateTime, auto_now=True)
```

**Notable:**
- Twitter/X username is **NOT stored in database** (removed in migration)
- Twitter username is stored in **session** instead: `request.session['twitter_username']`
- Profile pictures stored as files in `/media/profile_pictures/`

**Creation:**
- Automatically created by signals on user signup (see signals.py)
- Manual creation in views if missing

**Updates:**
- `views.py` lines: 439, 765, 826, 886, 1238, 1261, 1360, 1380

---

### **1.2 AnalysisSession Model**
**Location:** `dashboard/models.py` (lines 31-39)

**Purpose:** Records when a user runs an analysis

**Fields:**
```python
- user (ForeignKey → User) [CASCADE DELETE]
- profile_username (CharField, max=255)
- analyzed_at (DateTime, auto_now_add=True)
- payment_completed (Boolean, default=False)
```

**Creation:**
- `views.py` line 409: `AnalysisSession.objects.create()`

**Usage:**
- Tracks analysis history
- Links users to their analysis runs
- **Note:** Actual analysis results are NOT stored here (stored in cache/session)

---

### **1.3 Config Model**
**Location:** `dashboard/models.py` (lines 40-57)

**Purpose:** Global configuration (NOT per-user)

**Fields:**
```python
- Apify_api_key (CharField, max=255)
- Gemini_api_key (CharField, max=255)
- openrouter_api_key (CharField, max=255)
- Price (Integer, nullable, default=0) # in cents
- STRIPE_SECRET_KEY_TEST (CharField, max=255)
- STRIPE_PUBLISHABLE_KEY_TEST (CharField, max=255)
- STRIPE_SECRET_KEY_LIVE (CharField, max=255)
- STRIPE_PUBLISHABLE_KEY_LIVE (CharField, max=255)
- live (Boolean, default=False) # test vs live mode
- created_at (DateTime, auto_now_add=True)
- updated_at (DateTime, auto_now=True)
```

**Access Pattern:**
- Always retrieved with `Config.objects.first()` (singleton pattern)
- Used in 8 files: views.py, intelligent_analyzer.py, all scrapers

**Security:**
- Contains sensitive API keys
- Should be encrypted at rest (currently plaintext in DB)
- Single record for entire application

---

## 2️⃣ Session Storage (Database)

**Backend:** `django.contrib.sessions.backends.db`  
**Table:** `django_session`  
**Location:** `settings.py` line 115

### **2.1 Session Data Keys**

**Analysis Results (Temporary):**
```python
'instagram_analysis'   # List of analyzed Instagram posts
'linkedin_analysis'    # List of analyzed LinkedIn posts
'twitter_analysis'     # List of analyzed Twitter posts
'facebook_analysis'    # List of analyzed Facebook posts
```

**Analysis State:**
```python
'analysis_started'     # Boolean - analysis in progress
'analysis_complete'    # Boolean - analysis finished
'current_analysis_paid' # Boolean - user paid for current analysis
'analysis_run_id'      # String - Unique ID for this analysis run
'analysis_timestamp'   # Float - Unix timestamp when started
```

**Twitter/X Username (Persistent):**
```python
'twitter_username'     # String - Twitter handle (not stored in DB)
```

**Lifecycle:**
1. Analysis starts → `analysis_started = True`, `analysis_complete = False`
2. Results appear in cache → copied to session when complete
3. Payment → `current_analysis_paid = True`
4. Session persists until user logs out or session expires

**Set Locations:**
- `views.py` lines: 194-197, 317, 322-323, 333-334, 481, 566, 880, 1361

---

## 3️⃣ Cache Storage (Database)

**Backend:** `django.core.cache.backends.db.DatabaseCache`  
**Table:** `django_cache_table`  
**Timeout:** 3600 seconds (1 hour)  
**Location:** `settings.py` lines 132-137

### **3.1 Cache Keys by User**

**Analysis Results:**
```python
f'instagram_analysis_{user_id}'   # List of analyzed posts
f'linkedin_analysis_{user_id}'    # List of analyzed posts
f'twitter_analysis_{user_id}'     # List of analyzed posts
f'facebook_analysis_{user_id}'    # List of analyzed posts
```

**Profile Data:**
```python
f'instagram_profile_{user_id}'    # Dict: username, full_name, assessment
f'twitter_profile_{user_id}'      # Dict: username, full_name, assessment
f'facebook_profile_{user_id}'     # Dict: username, full_name, assessment
# Note: No linkedin_profile cache key found
```

**Progress Tracking:**
```python
f'analysis_stage_{user_id}'       # String: 'starting', 'analyzing_instagram', etc.
f'stage_progress_{user_id}'       # Int: 0-100 percentage
```

**Set Locations:**
- `utils.py` lines: 129-130, 136-137, 143-144, 150-151, 201, 253, 276, 280-290
- `views.py` lines: 345-346

**Flow:**
1. Analysis starts → cache keys created with progress
2. Each platform completes → results written to cache
3. All platforms done → results copied from cache to session
4. Cache keys deleted after copy to session

---

## 4️⃣ Data Write Operations

### **4.1 UserProfile Writes**

**Create Operations:**
```python
# Automatic (signals.py):
- post_save signal (line 14): UserProfile.objects.create() on User creation
- user_signed_up handler (line 37): get_or_create() safety net
- social_account_added handler (line 50): get_or_create() for OAuth

# Manual (views.py):
- Line 443: UserProfile.objects.create() if DoesNotExist
- Line 1243: UserProfile.objects.create() in profile update
```

**Update Operations:**
```python
# views.py .save() calls:
- Line 439: After setting payment_completed
- Line 765: Profile settings update
- Line 826: Connect social account
- Line 886: Disconnect social account  
- Line 1238: Profile form submission
- Line 1261: User details update
- Line 1360: Payment success
- Line 1380: Update after verification
```

### **4.2 AnalysisSession Writes**

**Create Only:**
```python
# views.py line 409:
AnalysisSession.objects.create(
    user=request.user,
    profile_username=instagram_username or linkedin_username or twitter_username or facebook_username,
    payment_completed=False
)
```

**No Updates:** Records are immutable after creation

### **4.3 Cache Writes**

**Platform Analysis Results:**
```python
# utils.py (analyze_all_platforms):
- Lines 280-286: Set analysis results for all platforms
- Line 289-290: Set completion stage and progress

# utils.py (parallel execution):
- Lines 129-151: Set progress stages during analysis
```

**Profile Data:**
```python
# utils.py:
- Line 201: cache.set(f'instagram_profile_{user_id}', ...)
- Line 253: cache.set(f'twitter_profile_{user_id}', ...)
- Line 276: cache.set(f'facebook_profile_{user_id}', ...)
```

### **4.4 Session Writes**

**Analysis Data:**
```python
# views.py (check_analysis_progress):
- Lines 194-197: Copy results from cache to session when complete

# views.py (start_analysis):
- Lines 317, 322-323, 333-334: Set analysis state
- Line 880: Set twitter_username
```

**Payment State:**
```python
# views.py:
- Line 481: Set current_analysis_paid = True (checkout)
- Line 566: Set current_analysis_paid = True (success)
- Line 1361: Set current_analysis_paid = True (webhook)
```

---

## 5️⃣ Data Read Operations

### **5.1 UserProfile Reads**

**Get Operations:**
```python
# views.py:
- Line 306: UserProfile.objects.get(user=request.user)
- Line 395: UserProfile.objects.get(user=request.user)
- Line 434: UserProfile.objects.get(user=request.user)
- Line 459: UserProfile.objects.get(user=request.user)
- Line 537: UserProfile.objects.get(user=request.user)
- Line 750: UserProfile.objects.get(user=request.user)
- Line 824: UserProfile.objects.get(user=request.user)
- Line 837: UserProfile.objects.get(user=request.user)
- Line 884: UserProfile.objects.get(user=request.user)
- Line 1162: UserProfile.objects.get(user=user)
- Line 1222: UserProfile.objects.get(user=request.user)
- Line 1270: UserProfile.objects.get(user=request.user)
- Line 1378: UserProfile.objects.get(user=request.user)
```

**Common Pattern:**
```python
try:
    user_profile = UserProfile.objects.get(user=request.user)
    # Use profile data
except UserProfile.DoesNotExist:
    # Handle missing profile
```

### **5.2 Config Reads**

**Singleton Pattern:**
```python
# Always: Config.objects.first()
# Used in:
- views.py (lines 711, 1313)
- intelligent_analyzer.py (line 24)
- scraper/t.py (line 24)
- scraper/facebook.py (line 21)
- scraper/linkedin.py (line 21)
- scraper/instagram.py (line 21)
```

### **5.3 Cache Reads**

**Analysis Results:**
```python
# views.py (check_analysis_progress):
- Lines 178-181: Get analysis results for all platforms
- Lines 184-185: Get current stage and progress

# views.py (other locations):
- Line 907: cache.get(cache_key) generic
- Line 915: cache.get(cache_key) generic
- Line 927: Debug cache read
- Line 1086: cache.get(cache_key) generic
```

### **5.4 Session Reads**

**Twitter Username:**
```python
# views.py - multiple locations:
- Lines 175, 309, 393, 471, 503, 525, 532, 553, 794, 841, 1172, 1178
# Pattern: twitter_username = request.session.get('twitter_username')
```

**Analysis Results:**
```python
# Accessed throughout views.py after analysis completes
# Keys: 'instagram_analysis', 'linkedin_analysis', 'twitter_analysis', 'facebook_analysis'
```

---

## 6️⃣ Sensitive Data Summary

### **6.1 API Keys (Global - Config Model)**
```python
✅ Stored: PostgreSQL (Config table)
⚠️  Security: Plaintext (should be encrypted)
📍 Access: Config.objects.first()
🔑 Keys:
  - Apify API key
  - Gemini API key  
  - OpenRouter API key
  - Stripe Secret Keys (test & live)
  - Stripe Publishable Keys (test & live)
```

### **6.2 User Credentials**
```python
✅ Stored: PostgreSQL (auth_user table - Django default)
🔒 Security: Passwords hashed with Django's password hashers
📍 Access: django.contrib.auth.models.User
```

### **6.3 Social Media Usernames**
```python
✅ Stored: PostgreSQL (UserProfile table)
📍 Fields: instagram, linkedin, facebook, tiktok
⚠️  Exception: Twitter username stored in SESSION only
🔒 Security: No encryption (usernames are semi-public)
```

### **6.4 Analysis Results**
```python
✅ Temporary Storage: Cache (1 hour) → Session (until logout)
❌ Persistent Storage: NOT stored in database after session ends
📊 Contents: Platform posts, AI analysis, risk scores, letter grades
🔒 Security: Session data secured by SESSION_COOKIE_SECURE
```

### **6.5 Payment Status**
```python
✅ Stored: PostgreSQL (UserProfile.payment_completed)
✅ Session: request.session['current_analysis_paid']
📍 Updated: On Stripe checkout success
```

---

## 7️⃣ Data Lifecycle

### **7.1 User Registration Flow**
```
1. User signs up (manual or OAuth)
   ↓
2. Django creates User record (auth_user table)
   ↓
3. post_save signal fires → UserProfile created automatically
   ↓
4. first_login = True, all social accounts disconnected
```

### **7.2 Social Account Connection Flow**
```
1. User connects Instagram/LinkedIn/Facebook
   ↓
2. Username stored in UserProfile.{platform} field
   ↓
3. UserProfile.{platform}_connected = True
   ↓
4. UserProfile.save()

Exception - Twitter/X:
1. User connects Twitter
   ↓
2. Username stored in request.session['twitter_username']
   ↓
3. UserProfile.tiktok_connected = True (legacy field name)
   ↓
4. UserProfile.save()
```

### **7.3 Analysis Flow**
```
1. User starts analysis
   ↓
2. AnalysisSession record created (timestamp, user_id)
   ↓
3. Cache keys created:
   - analysis_stage_{user_id} = 'starting'
   - stage_progress_{user_id} = 0
   ↓
4. Parallel scraping starts (all platforms simultaneously)
   ↓
5. Each platform completes:
   - Results written to cache: {platform}_analysis_{user_id}
   - Progress updated: stage_progress_{user_id}
   ↓
6. All platforms complete:
   - Results copied from cache → session
   - Cache keys deleted
   - analysis_complete = True in session
   ↓
7. User pays:
   - UserProfile.payment_completed = True
   - request.session['current_analysis_paid'] = True
   ↓
8. User logs out:
   - Session data cleared
   - Analysis results LOST (not persisted to DB)
```

### **7.4 Data Persistence**

**Permanent Storage:**
- User credentials (auth_user)
- User profiles (UserProfile)
- Social media usernames (UserProfile)
- Payment status (UserProfile.payment_completed)
- Analysis history timestamps (AnalysisSession)

**Temporary Storage (1 hour):**
- Analysis results (cache)
- Progress tracking (cache)

**Session Storage (until logout):**
- Twitter username
- Analysis results (after completion)
- Payment status for current analysis

**NOT Stored Permanently:**
- ❌ Actual analysis results (posts, AI analysis, risk scores)
- ❌ Individual post content
- ❌ AI-generated recommendations
- ❌ Letter grades and risk assessments

---

## 8️⃣ Database Schema

### **PostgreSQL Tables**

**Django Default Tables:**
- `auth_user` - User accounts
- `auth_group` - User groups
- `auth_permission` - Permissions
- `django_session` - Session data
- `django_content_type` - Content types
- `django_migrations` - Migration history
- `django_admin_log` - Admin actions

**Custom Tables:**
- `dashboard_userprofile` - User profiles (main user data)
- `dashboard_analysissession` - Analysis history
- `dashboard_config` - Global configuration

**Cache Table:**
- `django_cache_table` - Cache backend storage

**Media Files:**
- `/media/profile_pictures/` - User profile pictures (ImageField)

---

## 9️⃣ Security Considerations

### **✅ Good Practices**
1. Passwords hashed with Django's secure hashers
2. Sessions secured with HTTPS-only cookies
3. CSRF protection enabled
4. HSTS headers configured
5. Session data isolated by user

### **⚠️ Areas for Improvement**

**1. API Keys in Plaintext**
```
Issue: Config model stores API keys as plain CharField
Risk: Database breach exposes all API keys
Fix: Encrypt at rest (django-encrypted-fields, AWS Secrets Manager, etc.)
```

**2. Analysis Results Not Persisted**
```
Issue: Users lose analysis results on logout
Risk: Poor UX, users must re-run/re-pay
Fix: Create AnalysisResult model to persist data
```

**3. No Data Retention Policy**
```
Issue: Sessions/cache have timeouts but no cleanup
Risk: Stale data accumulation
Fix: Implement cleanup jobs for old AnalysisSession records
```

**4. Twitter Username in Session**
```
Issue: Inconsistent with other platforms (DB storage)
Risk: Lost on logout, inconsistent data model
Fix: Add twitter field back to UserProfile or use consistent session storage
```

---

## 🔟 Storage Capacity Planning

### **Per User Storage (Estimated)**

**Database:**
- UserProfile: ~500 bytes (text fields, booleans)
- AnalysisSession: ~200 bytes per analysis
- Session data: ~2KB (serialized analysis results)
- Cache data: ~5KB during analysis (4 platforms)

**Media:**
- Profile picture: ~100KB (if uploaded)

**Total per user:** ~108KB permanent + 7KB temporary

**For 10,000 users:**
- Database: ~1GB
- Media: ~1GB (if all upload pictures)
- Cache: ~50MB (active analyses)

---

## 📋 Summary Checklist

### **User Data Storage Locations:**
- [x] PostgreSQL Database (primary)
- [x] Django Sessions (database-backed)
- [x] Django Cache (database-backed)  
- [x] Filesystem (/media/profile_pictures/)
- [ ] Redis (not used)
- [ ] JSON files (not used)
- [ ] Pickle files (not used)
- [ ] External storage (S3, etc.) (not used)

### **Models Storing User Data:**
- [x] UserProfile (profiles, social accounts, payment)
- [x] AnalysisSession (analysis history)
- [ ] AnalysisResult (not implemented - should be)
- [x] Config (global API keys - not per-user)

### **Temporary Storage:**
- [x] Cache: Analysis results (1 hour)
- [x] Session: Analysis results, Twitter username (until logout)

### **Sensitive Data:**
- [x] API keys: Config model (plaintext - needs encryption)
- [x] User passwords: auth_user (properly hashed)
- [x] Social usernames: UserProfile (plaintext - semi-public data)
- [x] Stripe keys: Config model (plaintext - needs encryption)

---

## 📌 Conclusion

**All user data flows through PostgreSQL**, with temporary storage in database-backed sessions and cache. The system does **NOT** persist analysis results beyond the session, which may be a design choice for privacy but could be a UX limitation.

**Key architectural decision:** Analysis results are treated as ephemeral, not permanent records. Users must pay and download their report before logging out, or re-run the analysis.

**Security priority:** Encrypt API keys in the Config model and implement secrets management.

---

**Document End**

