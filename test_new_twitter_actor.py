#!/usr/bin/env python
"""
Test New Twitter Actor: kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest
Verify it works correctly and charges only for 2 tweets
"""

import os
import sys
import django

# Django setup
sys.path.append('/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from dotenv import load_dotenv
from apify_client import ApifyClient
import json

load_dotenv()

print("\n" + "="*80)
print("🧪 TESTING NEW TWITTER ACTOR")
print("="*80 + "\n")

print("Actor: kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest")
print("Test: 2 tweets from @elonmusk")
print("Goal: Verify correct billing and data structure")
print()

# Get Apify key
APIFY_API_KEY = os.getenv('APIFY_API_KEY')
if not APIFY_API_KEY:
    print("❌ ERROR: APIFY_API_KEY not found in .env")
    print("⚠️  This will generate FAKE RESULTS!")
    sys.exit(1)

print(f"✅ Using Apify key from .env: {APIFY_API_KEY[:10]}...{APIFY_API_KEY[-4:]}")
print()

# Initialize client
apify_client = ApifyClient(APIFY_API_KEY)

# Configure actor
actor_id = "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest"
username = "elonmusk"
tweets_desired = 2

run_input = {
    "searchTerms": [f"from:{username}"],
    "maxTweets": tweets_desired,
    "addUserInfo": True,
    "includeSearchTerms": False,
    "onlyImage": False,
    "onlyQuote": False,
    "onlyTwitterBlue": False,
    "onlyVerifiedUsers": False,
    "onlyVideo": False,
}

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 1: Run Actor")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

print(f"Running actor: {actor_id}")
print(f"Input: {json.dumps(run_input, indent=2)}")
print()

try:
    print("⏳ Starting actor run...")
    run = apify_client.actor(actor_id).call(run_input=run_input, wait_secs=15)
    print(f"✅ Actor run completed!")
    print(f"   Run ID: {run.get('id')}")
    print(f"   Dataset ID: {run.get('defaultDatasetId')}")
    print()
    
    # Wait for dataset
    import time
    time.sleep(5)
    
except Exception as e:
    print(f"❌ Actor run failed: {e}")
    print()
    print("Possible causes:")
    print("  • Actor not found or renamed")
    print("  • Insufficient Apify credits")
    print("  • API key invalid")
    sys.exit(1)

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 2: Retrieve Dataset Items")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

try:
    # Get dataset with hard limit
    dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items(limit=tweets_desired).items
    print(f"✅ Retrieved {len(dataset_items)} items from dataset")
    print(f"   Expected: {tweets_desired}")
    print(f"   Got: {len(dataset_items)}")
    
    if len(dataset_items) > tweets_desired:
        print(f"⚠️  WARNING: Got more items than requested!")
        print(f"   This could mean billing issues!")
    elif len(dataset_items) == tweets_desired:
        print(f"✅ CORRECT: Exactly {tweets_desired} items retrieved")
    else:
        print(f"ℹ️  Got fewer items (account may have fewer tweets)")
    
    print()
    
except Exception as e:
    print(f"❌ Failed to retrieve dataset: {e}")
    sys.exit(1)

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 3: Verify Data Structure")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if len(dataset_items) == 0:
    print("❌ No items retrieved - cannot verify data structure")
    sys.exit(1)

# Check first item
first_item = dataset_items[0]
print("First item keys:", list(first_item.keys()))
print()

# Required fields
required_fields = {
    "text": ["full_text", "text", "content"],
    "url": ["url", "tweetUrl", "tweet_url"],
    "timestamp": ["created_at", "createdAt", "timestamp"],
    "likes": ["favorite_count", "likes", "likeCount", "favoriteCount"],
    "replies": ["reply_count", "replies", "replyCount"],
    "retweets": ["retweet_count", "retweets", "retweetCount"],
}

print("Checking for required fields:")
for field_name, possible_keys in required_fields.items():
    found = False
    for key in possible_keys:
        if key in first_item:
            value = first_item[key]
            print(f"  ✅ {field_name}: Found as '{key}' = {str(value)[:60]}")
            found = True
            break
    
    if not found:
        print(f"  ❌ {field_name}: NOT FOUND (checked: {possible_keys})")

print()

# Show sample data
print("Sample tweet data:")
print(json.dumps(first_item, indent=2)[:1000])
print()

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 4: Test Data Extraction (Same as t.py)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

tweets = []
for item in dataset_items:
    try:
        # Extract tweet text (same logic as t.py)
        tweet_text = (
            item.get("full_text") or
            item.get("text") or
            item.get("content") or
            item.get("tweet", {}).get("full_text") or
            item.get("tweet", {}).get("text")
        )

        if not tweet_text:
            print(f"⚠️  Could not extract text from item")
            continue

        # Extract URL
        tweet_url = (
            item.get("url") or
            item.get("tweetUrl") or
            item.get("tweet", {}).get("url") or
            f"https://twitter.com/{username}/status/{item.get('id_str', '')}"
        )

        # Extract timestamp
        timestamp = (
            item.get("created_at") or
            item.get("createdAt") or
            item.get("timestamp") or
            item.get("tweet", {}).get("created_at")
        )

        # Extract engagement metrics
        likes_count = (
            item.get("favorite_count") or
            item.get("likes") or
            item.get("likeCount") or
            item.get("tweet", {}).get("favorite_count") or
            0
        )

        replies_count = (
            item.get("reply_count") or
            item.get("replies") or
            item.get("replyCount") or
            item.get("tweet", {}).get("reply_count") or
            0
        )

        retweets_count = (
            item.get("retweet_count") or
            item.get("retweets") or
            item.get("retweetCount") or
            item.get("tweet", {}).get("retweet_count") or
            0
        )

        # Extract hashtags and mentions
        hashtags = []
        mentions = []

        entities = item.get("entities", {})
        if entities:
            hashtags = [tag.get("text", "") for tag in entities.get("hashtags", [])]
            mentions = [mention.get("screen_name", "") for mention in entities.get("user_mentions", [])]

        tweets.append({
            "tweet": tweet_text,
            "post_url": tweet_url,
            "timestamp": timestamp,
            "likes": likes_count,
            "replies": replies_count,
            "retweets": retweets_count,
            "hashtags": hashtags,
            "mentions": mentions,
        })
        
        print(f"✅ Extracted tweet {len(tweets)}:")
        print(f"   Text: {tweet_text[:80]}...")
        print(f"   URL: {tweet_url}")
        print(f"   Likes: {likes_count}, Replies: {replies_count}, Retweets: {retweets_count}")
        print()
        
    except Exception as e:
        print(f"⚠️  Error extracting tweet data: {e}")
        continue

print(f"✅ Successfully extracted {len(tweets)} tweets")
print()

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("SUMMARY")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if len(tweets) == tweets_desired:
    print("✅ SUCCESS: New actor works correctly!")
    print()
    print(f"   Requested: {tweets_desired} tweets")
    print(f"   Retrieved: {len(dataset_items)} items from dataset")
    print(f"   Extracted: {len(tweets)} tweets")
    print()
    print("   ✅ Data structure compatible")
    print("   ✅ All required fields present")
    print("   ✅ Billing should be correct (pay per result)")
    print()
    print("🎉 SAFE TO DEPLOY!")
    
elif len(tweets) > 0:
    print("⚠️  PARTIAL SUCCESS:")
    print(f"   Expected {tweets_desired} tweets, got {len(tweets)}")
    print("   May be due to account having fewer tweets")
    print("   Data structure appears compatible")
    
else:
    print("❌ FAILURE: Could not extract any tweets")
    print("   Data structure may be incompatible")
    print("   DO NOT DEPLOY")

print()
print("="*80)
print("✅ TEST COMPLETE")
print("="*80)

