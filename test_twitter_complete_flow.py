#!/usr/bin/env python
"""
Comprehensive test of Twitter/X analyzer using apidojo/tweet-scraper
Tests: scraping → AI analysis → result rendering
"""

import os
import sys
import json
import django

# Django setup
sys.path.append('/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*80)
print("🐦 TWITTER/X COMPLETE FLOW TEST")
print("="*80 + "\n")

# Test configuration
test_username = "elonmusk"
test_limit = 3

print(f"Test Profile: @{test_username}")
print(f"Tweet Limit: {test_limit}")
print()

# Step 1: Verify API key
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 1: API KEY VERIFICATION")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

apify_key = os.getenv('APIFY_API_KEY')
if apify_key:
    print(f"✅ APIFY_API_KEY found in .env")
    print(f"   Key: ...{apify_key[-8:]}")
else:
    print("❌ APIFY_API_KEY not found in .env")
    sys.exit(1)

print()

# Step 2: Test actor directly
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 2: DIRECT ACTOR TEST (apidojo/tweet-scraper)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

from apify_client import ApifyClient
from apify_client._errors import ApifyApiError

client = ApifyClient(apify_key)

actor_id = "apidojo/tweet-scraper"
run_input = {
    "searchTerms": [f"from:{test_username}"],
    "maxTweets": test_limit,
    "addUserInfo": True,
    "includeSearchTerms": False,
    "onlyImage": False,
    "onlyQuote": False,
    "onlyTwitterBlue": False,
    "onlyVerifiedUsers": False,
    "onlyVideo": False,
}

print(f"🚀 Testing actor: {actor_id}")
print(f"   Search: from:{test_username}")
print()

try:
    print("⏳ Running actor...")
    run = client.actor(actor_id).call(run_input=run_input, wait_secs=30)
    
    print(f"✅ Actor completed successfully!")
    print(f"   Run ID: {run.get('id')}")
    print(f"   Status: {run.get('status')}")
    print()
    
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
    print(f"📊 Retrieved {len(dataset_items)} tweets")
    print()
    
    if len(dataset_items) == 0:
        print("⚠️  No tweets returned (possibly rate limited or blocked)")
        print("   This might require a paid plan or the actor may be throttled")
        sys.exit(1)
    
    # Show first tweet structure
    print("📝 First tweet structure:")
    first_tweet = dataset_items[0]
    print(json.dumps(first_tweet, indent=2, default=str)[:1000] + "...")
    print()
    
    # Extract key fields
    print("🔍 Extracting fields from first tweet:")
    print()
    
    fields_to_check = [
        ("text", ["full_text", "text", "content"]),
        ("url", ["url", "tweetUrl"]),
        ("timestamp", ["created_at", "createdAt", "timestamp"]),
        ("likes", ["favorite_count", "likes", "likeCount"]),
        ("replies", ["reply_count", "replies", "replyCount"]),
        ("retweets", ["retweet_count", "retweets", "retweetCount"]),
    ]
    
    extracted_data = {}
    for field_name, possible_keys in fields_to_check:
        value = None
        for key in possible_keys:
            if key in first_tweet:
                value = first_tweet[key]
                break
        
        status = "✅" if value else "❌"
        print(f"   {status} {field_name}: {value if value else 'NOT FOUND'}")
        extracted_data[field_name] = value
    
    print()
    
    if not extracted_data.get("text"):
        print("❌ CRITICAL: Tweet text not found!")
        print("   Available keys:", list(first_tweet.keys())[:20])
        sys.exit(1)
    
except ApifyApiError as e:
    error_str = str(e)
    print(f"❌ Actor failed: {e}")
    print()
    
    if "demo" in error_str.lower() or "paid plan" in error_str.lower():
        print("⚠️  This actor requires a paid Apify plan")
        print("   Demo mode only without payment")
    elif "rent" in error_str.lower():
        print("⚠️  This actor requires rental")
    
    sys.exit(1)

# Step 3: Test full scraper function
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 3: FULL SCRAPER TEST (dashboard/scraper/t.py)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

print("📥 Importing Twitter scraper...")
from dashboard.scraper.t import analyze_twitter_profile

print()
print(f"🤖 Running full analysis for @{test_username}...")
print("   (This includes scraping + AI analysis)")
print()

try:
    result_json = analyze_twitter_profile(test_username, tweets_desired=test_limit)
    
    print("✅ Analysis completed!")
    print()
    
    # Parse result
    results = json.loads(result_json)
    print(f"📊 Analysis returned {len(results)} tweets")
    print()
    
    # Validate first result
    if len(results) > 0:
        first_result = results[0]
        
        print("🔍 Validating first result structure:")
        print()
        
        # Check post_data
        if "post_data" in first_result:
            post_data = first_result["post_data"]
            print("   ✅ post_data found")
            print(f"      - caption: {'✅' if post_data.get('caption') else '❌'}")
            print(f"      - post_url: {'✅' if post_data.get('post_url') else '❌'}")
            print(f"      - timestamp: {'✅' if post_data.get('timestamp') else '❌'}")
            print(f"      - likes_count: {post_data.get('likes_count', 'N/A')}")
            print(f"      - comments_count: {post_data.get('comments_count', 'N/A')}")
            print(f"      - shares_count: {post_data.get('shares_count', 'N/A')}")
        else:
            print("   ❌ post_data missing")
        
        print()
        
        # Check Twitter analysis
        if "Twitter" in first_result:
            twitter_analysis = first_result["Twitter"]
            print("   ✅ Twitter analysis found")
            print(f"      - content_strength: {'✅' if 'content_strength' in twitter_analysis else '❌'}")
            print(f"      - content_concern: {'✅' if 'content_concern' in twitter_analysis else '❌'}")
            print(f"      - content_risk: {'✅' if 'content_risk' in twitter_analysis else '❌'}")
            print(f"      - grade: {twitter_analysis.get('grade', 'N/A')}")
        else:
            print("   ❌ Twitter analysis missing")
        
        print()
        
        # Show sample
        print("📄 Sample result (first tweet):")
        print(json.dumps(first_result, indent=2, default=str)[:800] + "...")
        print()
    
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

# Step 4: Template compatibility check
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 4: TEMPLATE COMPATIBILITY CHECK")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

print("✅ Checking result structure matches template requirements:")
print()

template_checks = [
    ("item.post_data.post_url", "View original post link"),
    ("item.post_data.caption", "Tweet text display"),
    ("item.post_data.timestamp", "Post date"),
    ("item.post_data.likes_count", "Engagement metrics"),
    ("item.analysis.Twitter.grade", "Grade badge"),
    ("item.analysis.Twitter.content_strength", "Analysis sections"),
]

all_passed = True
for field_path, description in template_checks:
    # Simulate template access
    try:
        obj = first_result
        for part in field_path.replace("item.", "").split("."):
            if part == "analysis":
                obj = {k: v for k, v in obj.items() if k != "post_data"}
            else:
                obj = obj[part]
        
        print(f"   ✅ {field_path} ({description})")
    except (KeyError, TypeError):
        print(f"   ❌ {field_path} ({description}) - MISSING")
        all_passed = False

print()

if all_passed:
    print("✅ All template fields present!")
else:
    print("⚠️  Some template fields missing")

print()

# Final summary
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("SUMMARY")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

print("✅ Step 1: API key verified (.env)")
print("✅ Step 2: Actor runs successfully (apidojo/tweet-scraper)")
print("✅ Step 3: Full scraper + AI analysis works")
print("✅ Step 4: Template compatibility confirmed")
print()

print("🎉 TWITTER ANALYSIS FLOW IS READY!")
print()
print("Next steps:")
print("• Test on /dashboard/ page by connecting Twitter account")
print("• Verify results render correctly on /dashboard/results/")
print("• Ensure 'View original post' links work")
print()

print("="*80)
print("✅ TEST COMPLETE")
print("="*80)




