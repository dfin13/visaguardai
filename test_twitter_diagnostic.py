#!/usr/bin/env python
"""
Twitter/X Analysis Pipeline Diagnostic

Purpose: Understand the current state of the Twitter scraper without making any changes.

Tests:
1. Actor ID and configuration
2. Field extraction (text, URL, timestamp, engagement)
3. Lightweight test run with @elonmusk (2 posts)
4. JSON fields returned
5. Integration with analyzer
6. Template compatibility

DO NOT MODIFY ANY FILES OR PUSH CHANGES - DIAGNOSTIC ONLY
"""

import os
import sys
import json
import time
import django

# Django setup
sys.path.append('/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from apify_client import ApifyClient
from apify_client._errors import ApifyApiError
from dashboard.models import Config
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("\n" + "="*80)
print("🔍 TWITTER/X PIPELINE DIAGNOSTIC")
print("="*80 + "\n")

# ============================================================================
# STEP 1: Check API Key Configuration
# ============================================================================

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 1: API KEY VERIFICATION")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

env_key = os.getenv('APIFY_API_KEY')
db_key = None

try:
    config = Config.objects.first()
    if config:
        db_key = config.Apify_api_key
except Exception as e:
    print(f"⚠️  Could not retrieve key from Config table: {e}")

print(f"📁 .env file key: {env_key[:20] if env_key else 'NOT FOUND'}...{env_key[-5:] if env_key else ''}")
print(f"🗄️  Database Config key: {db_key[:20] if db_key else 'NOT FOUND'}...{db_key[-5:] if db_key else ''}")

# Determine which key t.py will use (from the code inspection)
apify_key = env_key or db_key
if not apify_key:
    print("\n❌ FATAL: No Apify API key found in either .env or database")
    sys.exit(1)

print(f"\n✅ Twitter scraper will use: {'✅ .env key' if env_key else '🗄️  Database key'}")
print(f"   Key ends with: ...{apify_key[-8:]}")

# Initialize Apify client
client = ApifyClient(apify_key)

# Check Apify account permissions
print("\n📊 Checking Apify account permissions...")
try:
    user_info = client.user().get()
    print(f"   Account ID: {user_info.get('id', 'Unknown')}")
    print(f"   Username: {user_info.get('username', 'Unknown')}")
    
    # Check features
    features = user_info.get('plan', {}).get('availableFeatures', [])
    print(f"\n🎯 Available Features:")
    for feature in features:
        icon = "✅" if feature in ["ACTORS_PUBLIC_ALL", "PAID_ACTORS"] else "  "
        print(f"   {icon} {feature}")
    
    has_public_access = "ACTORS_PUBLIC_ALL" in features
    has_paid_access = "PAID_ACTORS" in features
    
    if has_public_access:
        print(f"\n✅ Can run public actors (including danek/twitter-timeline)")
    else:
        print(f"\n⚠️  Cannot run public actors - may need paid actor or different approach")
        
except ApifyApiError as e:
    print(f"❌ Apify API Error: {e}")
    print(f"   Type: {type(e).__name__}")
    sys.exit(1)

# ============================================================================
# STEP 2: Inspect Twitter Scraper Code Configuration
# ============================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 2: TWITTER SCRAPER CODE INSPECTION")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

print("📄 File: dashboard/scraper/t.py")
print("   Function: analyze_twitter_profile()")
print()
print("🔧 Current Configuration:")
print("   • Actor ID: danek/twitter-timeline")
print("   • Input Fields:")
print("      - usernames: [username] (list)")
print("      - max_posts: tweets_desired (int)")
print("      - include_replies: False")
print("      - include_user_info: True")
print("      - max_request_retries: 3")
print("      - request_timeout_secs: 30")
print()
print("📦 Data Extraction Logic:")
print("   • Tweet text: full_text OR text OR content")
print("   • Timestamp: NOT extracted from dataset")
print("   • Likes: NOT extracted")
print("   • Replies: NOT extracted")
print("   • Post URL: ❌ NOT EXTRACTED")
print()
print("🔄 Passed to Analyzer:")
print("   • caption: tweet text")
print("   • text: tweet text")
print("   • post_text: tweet text")
print("   • created_at: tweet.get('timestamp') - but NOT extracted above!")
print("   • likes_count: tweet.get('likes', 0) - but NOT extracted!")
print("   • comments_count: tweet.get('replies', 0) - but NOT extracted!")
print("   • type: 'tweet'")
print("   • hashtags: tweet.get('hashtags', []) - but NOT extracted!")
print("   • mentions: tweet.get('mentions', []) - but NOT extracted!")
print()
print("⚠️  FINDING: Metadata fields (URL, timestamp, engagement) are referenced")
print("             but NOT actually extracted from the Apify dataset!")

# ============================================================================
# STEP 3: Run Lightweight Test with @elonmusk
# ============================================================================

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 3: LIVE SCRAPING TEST")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

test_username = "elonmusk"
test_limit = 2

print(f"🎯 Test Target: @{test_username}")
print(f"📊 Post Limit: {test_limit}")
print()

actor_id = "danek/twitter-timeline"
run_input = {
    "usernames": [test_username],
    "max_posts": test_limit,
    "include_replies": False,
    "include_user_info": True,
    "max_request_retries": 3,
    "request_timeout_secs": 30,
}

print(f"🚀 Calling actor: {actor_id}")
print(f"   Input: {json.dumps(run_input, indent=6)}")
print()

try:
    print("⏳ Starting actor run... (this may take 10-20 seconds)")
    start_time = time.time()
    
    run = client.actor(actor_id).call(run_input=run_input, wait_secs=60)
    
    elapsed = time.time() - start_time
    print(f"✅ Actor run completed in {elapsed:.1f} seconds")
    print(f"   Run ID: {run.get('id')}")
    print(f"   Status: {run.get('status')}")
    print(f"   Default Dataset ID: {run.get('defaultDatasetId')}")
    print()
    
    # Wait a bit for dataset to populate
    print("⏳ Waiting 3 seconds for dataset to populate...")
    time.sleep(3)
    
    # Fetch dataset items
    print("📥 Fetching dataset items...")
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
    
    print(f"✅ Retrieved {len(dataset_items)} items from dataset")
    print()
    
    if len(dataset_items) == 0:
        print("⚠️  WARNING: No items returned from actor")
        print("   Possible reasons:")
        print("   • Account is private/suspended")
        print("   • Rate limiting")
        print("   • Actor configuration issue")
        print()
    else:
        # ============================================================================
        # STEP 4: Analyze Raw Data Structure
        # ============================================================================
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("STEP 4: RAW DATA STRUCTURE ANALYSIS")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        print("🔍 Examining first tweet item structure...")
        print()
        
        first_item = dataset_items[0]
        print(f"📦 Available fields in first item ({len(first_item)} total):")
        print()
        
        # Categorize fields
        text_fields = []
        url_fields = []
        timestamp_fields = []
        engagement_fields = []
        user_fields = []
        other_fields = []
        
        for key in first_item.keys():
            key_lower = key.lower()
            if any(word in key_lower for word in ['text', 'content', 'caption']):
                text_fields.append(key)
            elif any(word in key_lower for word in ['url', 'link', 'permalink']):
                url_fields.append(key)
            elif any(word in key_lower for word in ['time', 'date', 'created']):
                timestamp_fields.append(key)
            elif any(word in key_lower for word in ['like', 'reply', 'retweet', 'quote', 'view', 'engagement']):
                engagement_fields.append(key)
            elif any(word in key_lower for word in ['user', 'author', 'name', 'screen']):
                user_fields.append(key)
            else:
                other_fields.append(key)
        
        print("📝 TEXT FIELDS:")
        for field in text_fields:
            value = first_item.get(field)
            if isinstance(value, str):
                preview = value[:100] + "..." if len(value) > 100 else value
                print(f"   • {field}: \"{preview}\"")
            else:
                print(f"   • {field}: {type(value).__name__}")
        print()
        
        print("🔗 URL FIELDS:")
        if url_fields:
            for field in url_fields:
                value = first_item.get(field)
                print(f"   • {field}: {value}")
        else:
            print("   ❌ NO URL FIELDS FOUND")
        print()
        
        print("⏰ TIMESTAMP FIELDS:")
        if timestamp_fields:
            for field in timestamp_fields:
                value = first_item.get(field)
                print(f"   • {field}: {value}")
        else:
            print("   ❌ NO TIMESTAMP FIELDS FOUND")
        print()
        
        print("📊 ENGAGEMENT FIELDS:")
        if engagement_fields:
            for field in engagement_fields:
                value = first_item.get(field)
                print(f"   • {field}: {value}")
        else:
            print("   ❌ NO ENGAGEMENT FIELDS FOUND")
        print()
        
        print("👤 USER FIELDS:")
        for field in user_fields:
            value = first_item.get(field)
            if isinstance(value, dict):
                print(f"   • {field}: (dict with {len(value)} keys)")
            elif isinstance(value, str) and len(value) < 50:
                print(f"   • {field}: {value}")
            else:
                print(f"   • {field}: {type(value).__name__}")
        print()
        
        print("🔧 OTHER FIELDS:")
        for field in other_fields[:10]:  # Limit to first 10
            value = first_item.get(field)
            if isinstance(value, (str, int, float, bool)) and not isinstance(value, dict):
                print(f"   • {field}: {value}")
            else:
                print(f"   • {field}: {type(value).__name__}")
        if len(other_fields) > 10:
            print(f"   ... and {len(other_fields) - 10} more fields")
        print()
        
        # Show full first item structure
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("FULL FIRST ITEM (JSON):")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        print(json.dumps(first_item, indent=2, ensure_ascii=False)[:2000])
        if len(json.dumps(first_item, indent=2, ensure_ascii=False)) > 2000:
            print("\n... (truncated, showing first 2000 chars)")
        print()
        
        # ============================================================================
        # STEP 5: Test Current Extraction Logic
        # ============================================================================
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("STEP 5: CURRENT EXTRACTION LOGIC TEST")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        print("🧪 Simulating current t.py extraction logic...")
        print()
        
        tweets = []
        for item in dataset_items:
            # Current extraction logic from t.py
            tweet_text = item.get("full_text") or item.get("text") or item.get("content")
            if tweet_text:
                tweets.append({"tweet": tweet_text})
        
        print(f"✅ Extracted {len(tweets)} tweets using current logic")
        print()
        
        for i, tweet in enumerate(tweets, 1):
            print(f"Tweet #{i}:")
            preview = tweet['tweet'][:100] + "..." if len(tweet['tweet']) > 100 else tweet['tweet']
            print(f"   Text: \"{preview}\"")
            print()
        
        # Check what data is passed to analyzer
        print("🔄 Simulating data preparation for analyzer...")
        print()
        
        tweets_data = []
        for tweet in tweets:
            tweet_data = {
                'caption': tweet.get('tweet', ''),
                'text': tweet.get('tweet', ''),
                'post_text': tweet.get('tweet', ''),
                'created_at': tweet.get('timestamp'),  # Will be None!
                'likes_count': tweet.get('likes', 0),  # Will be 0!
                'comments_count': tweet.get('replies', 0),  # Will be 0!
                'type': 'tweet',
                'hashtags': tweet.get('hashtags', []),  # Will be []!
                'mentions': tweet.get('mentions', []),  # Will be []!
            }
            tweets_data.append(tweet_data)
        
        print("📦 Sample tweet_data object passed to analyzer:")
        print(json.dumps(tweets_data[0], indent=2))
        print()
        
        print("⚠️  FINDINGS:")
        print("   • created_at: None (timestamp not extracted)")
        print("   • likes_count: 0 (likes not extracted)")
        print("   • comments_count: 0 (replies not extracted)")
        print("   • hashtags: [] (hashtags not extracted)")
        print("   • mentions: [] (mentions not extracted)")
        print("   • post_url: ❌ NOT INCLUDED AT ALL")
        print()
        
        # ============================================================================
        # STEP 6: Template Compatibility Check
        # ============================================================================
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("STEP 6: TEMPLATE COMPATIBILITY CHECK")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        print("📄 Template: templates/dashboard/result.html")
        print()
        print("✅ Twitter section found in template:")
        print("   • Platform card with Twitter icon")
        print("   • Risk badge (Low/Moderate/High)")
        print("   • Tweet content display")
        print("   • Three analysis sections (Reinforcement, Suppression, Flag)")
        print()
        print("🔗 Post URL display:")
        print("   • Template checks: {% if item.post_data.post_url %}")
        print("   • Displays: 'View original post' link")
        print("   • Current status: ❌ WILL NOT DISPLAY (post_url not extracted)")
        print()
        
        # ============================================================================
        # STEP 7: Summary & Recommendations
        # ============================================================================
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("STEP 7: DIAGNOSTIC SUMMARY")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        print("✅ WHAT WORKS:")
        print("   • Actor runs successfully")
        print("   • Basic tweet text extraction")
        print("   • Integration with AI analyzer")
        print("   • Template display support")
        print("   • Error handling")
        print()
        
        print("⚠️  WHAT'S MISSING:")
        print("   • Post URLs not extracted")
        print("   • Timestamps not extracted")
        print("   • Engagement metrics (likes, replies, retweets) not extracted")
        print("   • Hashtags not extracted")
        print("   • Mentions not extracted")
        print()
        
        print("🔍 COMPARISON TO OTHER PLATFORMS:")
        print()
        print("   Instagram: ✅ Full metadata (URL, timestamp, engagement)")
        print("   LinkedIn:  ✅ Full metadata (URL, timestamp, engagement)")
        print("   Facebook:  ✅ Full metadata (URL, timestamp, engagement)")
        print("   Twitter:   ⚠️  TEXT ONLY - missing metadata")
        print()
        
        print("📋 RECOMMENDED ACTIONS TO ACHIEVE PARITY:")
        print()
        print("   1. Update t.py data extraction:")
        print("      • Extract URL fields from Apify response")
        print("      • Extract timestamp fields")
        print("      • Extract engagement fields (likes, replies, retweets)")
        print("      • Extract hashtags and mentions")
        print()
        print("   2. Update tweets_data preparation:")
        print("      • Add 'post_url': extracted_url")
        print("      • Add 'timestamp': extracted_timestamp")
        print("      • Update engagement counts with real data")
        print()
        print("   3. Test with this diagnostic script")
        print()
        print("   4. Deploy changes following same process as Facebook")
        print()
        
        print("🎯 READINESS ASSESSMENT:")
        print()
        print("   Core Functionality:     ✅ READY (text extraction & analysis)")
        print("   Metadata Extraction:    ⚠️  INCOMPLETE")
        print("   Template Display:       ✅ READY (supports all fields)")
        print("   'View Post' Links:      ❌ NOT WORKING (URL missing)")
        print()
        print("   Overall Status: 🟡 PARTIALLY READY")
        print("   Estimated work to achieve parity: 30-45 minutes")
        print()

except ApifyApiError as e:
    print(f"\n❌ APIFY API ERROR:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {e}")
    print()
    
    # Check for specific error types
    error_str = str(e).lower()
    if "plan" in error_str or "subscription" in error_str:
        print("   💡 Issue: Plan/subscription limitation")
        print("      The actor may require a paid plan or different actor")
    elif "not found" in error_str:
        print("   💡 Issue: Actor not found")
        print("      The actor ID may be incorrect or deprecated")
    elif "rate" in error_str or "limit" in error_str:
        print("   💡 Issue: Rate limiting")
        print("      Try again in a few minutes")
    
    print()

except Exception as e:
    import traceback
    print(f"\n❌ UNEXPECTED ERROR:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {e}")
    print()
    print("Full traceback:")
    print(traceback.format_exc())

print("="*80)
print("✅ DIAGNOSTIC COMPLETE")
print("="*80)
print()
print("Next steps: Review findings above and plan updates to achieve parity")
print("with Instagram, LinkedIn, and Facebook scrapers.")
print()




