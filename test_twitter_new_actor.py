#!/usr/bin/env python
"""
Test the new apidojo/twitter-scraper-lite actor to verify it works
and understand its data structure before updating t.py
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
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*80)
print("🧪 TESTING NEW TWITTER ACTOR: apidojo/twitter-scraper-lite")
print("="*80 + "\n")

# Get API key
apify_key = os.getenv('APIFY_API_KEY')
print(f"✅ Using API key: ...{apify_key[-8:]}")

# Initialize client
client = ApifyClient(apify_key)

# Test configuration
test_username = "elonmusk"
test_limit = 2

print(f"\n🎯 Test Target: @{test_username}")
print(f"📊 Tweet Limit: {test_limit}")
print()

# New actor configuration
actor_id = "apidojo/twitter-scraper-lite"
run_input = {
    "searchTerms": [f"from:{test_username}"],
    "maxTweets": test_limit,
    "addUserInfo": True,
    "includeSearchTerms": False,
}

print(f"🚀 Actor: {actor_id}")
print(f"📦 Input Configuration:")
print(json.dumps(run_input, indent=2))
print()

try:
    print("⏳ Starting actor run...")
    start_time = time.time()
    
    run = client.actor(actor_id).call(run_input=run_input, wait_secs=60)
    
    elapsed = time.time() - start_time
    print(f"✅ Actor run completed in {elapsed:.1f} seconds")
    print(f"   Run ID: {run.get('id')}")
    print(f"   Status: {run.get('status')}")
    print()
    
    # Wait for dataset
    print("⏳ Waiting 3 seconds for dataset to populate...")
    time.sleep(3)
    
    # Fetch dataset
    print("📥 Fetching dataset items...")
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
    
    print(f"✅ Retrieved {len(dataset_items)} items")
    print()
    
    if len(dataset_items) == 0:
        print("⚠️  WARNING: No items returned")
    else:
        # Analyze first item structure
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("DATA STRUCTURE ANALYSIS")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        first_item = dataset_items[0]
        
        print(f"📦 Available fields ({len(first_item)} total):")
        for key in sorted(first_item.keys()):
            value = first_item.get(key)
            if isinstance(value, str) and len(value) < 100:
                print(f"   • {key}: {value}")
            elif isinstance(value, (int, float, bool)):
                print(f"   • {key}: {value}")
            elif value is None:
                print(f"   • {key}: None")
            else:
                print(f"   • {key}: {type(value).__name__}")
        print()
        
        # Check for key fields
        print("🔍 KEY FIELD EXTRACTION TEST:")
        print()
        
        # Text
        text = first_item.get("full_text") or first_item.get("text") or first_item.get("content")
        print(f"   ✅ TEXT: {text[:100] if text else 'NOT FOUND'}...")
        print()
        
        # URL
        url = first_item.get("url") or first_item.get("link") or first_item.get("permalink")
        print(f"   {'✅' if url else '❌'} URL: {url or 'NOT FOUND'}")
        print()
        
        # Timestamp
        timestamp = first_item.get("created_at") or first_item.get("createdAt") or first_item.get("date")
        print(f"   {'✅' if timestamp else '❌'} TIMESTAMP: {timestamp or 'NOT FOUND'}")
        print()
        
        # Engagement
        likes = first_item.get("favorite_count") or first_item.get("likes") or first_item.get("favoriteCount")
        replies = first_item.get("reply_count") or first_item.get("replies") or first_item.get("replyCount")
        retweets = first_item.get("retweet_count") or first_item.get("retweets") or first_item.get("retweetCount")
        
        print(f"   {'✅' if likes is not None else '❌'} LIKES: {likes if likes is not None else 'NOT FOUND'}")
        print(f"   {'✅' if replies is not None else '❌'} REPLIES: {replies if replies is not None else 'NOT FOUND'}")
        print(f"   {'✅' if retweets is not None else '❌'} RETWEETS: {retweets if retweets is not None else 'NOT FOUND'}")
        print()
        
        # Show full first item
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("FULL FIRST ITEM (JSON):")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        print(json.dumps(first_item, indent=2, ensure_ascii=False))
        print()
        
        # Test extraction logic
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("RECOMMENDED EXTRACTION CODE:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        print("""
tweets = []
for item in dataset_items:
    tweet_text = item.get("full_text") or item.get("text") or item.get("content")
    if tweet_text:
        tweets.append({
            "tweet": tweet_text,
            "post_url": item.get("url") or item.get("link"),
            "timestamp": item.get("created_at") or item.get("createdAt"),
            "likes": item.get("favorite_count", 0) or item.get("favoriteCount", 0),
            "replies": item.get("reply_count", 0) or item.get("replyCount", 0),
            "retweets": item.get("retweet_count", 0) or item.get("retweetCount", 0),
            "hashtags": item.get("hashtags", []),
            "mentions": item.get("user_mentions", []) or item.get("mentions", []),
        })
        """)
        
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ TEST SUCCESSFUL!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        print("The apidojo/twitter-scraper-lite actor works correctly.")
        print("You can now update t.py with:")
        print(f'  • Actor ID: "{actor_id}"')
        print('  • Input: searchTerms=[f"from:{username}"], maxTweets=tweets_desired')
        print("  • Data extraction: Use recommended code above")
        print()

except ApifyApiError as e:
    print(f"\n❌ APIFY API ERROR:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {e}")
    print()
    
    error_str = str(e).lower()
    if "plan" in error_str or "subscription" in error_str or "rent" in error_str:
        print("   💡 This actor also requires a paid plan or rental")
    elif "not found" in error_str:
        print("   💡 Actor not found")
    
except Exception as e:
    import traceback
    print(f"\n❌ UNEXPECTED ERROR:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {e}")
    print()
    print("Full traceback:")
    print(traceback.format_exc())

print("="*80)
print("✅ TEST COMPLETE")
print("="*80)




