#!/usr/bin/env python
"""
Check for alternative Twitter scraping actors that might be available
"""

import os
import sys
import django

sys.path.append('/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from apify_client import ApifyClient
from apify_client._errors import ApifyApiError
from dotenv import load_dotenv

load_dotenv()

apify_key = os.getenv('APIFY_API_KEY')
client = ApifyClient(apify_key)

print("\n" + "="*80)
print("🔍 TWITTER ACTOR ALTERNATIVES CHECK")
print("="*80 + "\n")

# List of potential Twitter scraping actors
twitter_actors = [
    ("danek/twitter-timeline", "Current actor in t.py"),
    ("apify/twitter-scraper", "Official Apify Twitter scraper"),
    ("quacker/twitter-scraper", "Alternative Twitter scraper"),
    ("twitter-scraper", "Generic Twitter scraper"),
    ("apidojo/tweet-scraper", "Twitter tweet scraper"),
]

print("Testing availability of Twitter scraping actors...\n")

for actor_id, description in twitter_actors:
    print(f"🔍 Testing: {actor_id}")
    print(f"   Description: {description}")
    
    try:
        # Try to get actor info
        actor_info = client.actor(actor_id).get()
        
        if actor_info:
            print(f"   ✅ Actor exists")
            print(f"      Name: {actor_info.get('name', 'Unknown')}")
            print(f"      Title: {actor_info.get('title', 'Unknown')}")
            
            # Check if it requires payment
            pricing = actor_info.get('pricing', {})
            if pricing:
                print(f"      Pricing model: {pricing}")
            
            # Try a very small test run
            print(f"      Testing with 1 post limit...")
            try:
                test_run = client.actor(actor_id).call(
                    run_input={
                        "usernames": ["elonmusk"] if "danek" in actor_id or "apify" in actor_id else None,
                        "searchTerms": ["from:elonmusk"] if "apidojo" in actor_id else None,
                        "max_posts": 1,
                        "maxTweets": 1 if "apidojo" in actor_id else None,
                    },
                    wait_secs=10
                )
                print(f"      ✅ TEST RUN SUCCESSFUL!")
                print(f"         Run ID: {test_run.get('id')}")
                print(f"         Status: {test_run.get('status')}")
                print(f"         ⭐ THIS ACTOR WORKS!")
                print()
                
                # Get a sample item
                dataset_items = client.dataset(test_run["defaultDatasetId"]).list_items().items
                if dataset_items:
                    print(f"      📦 Sample data structure:")
                    sample = dataset_items[0]
                    print(f"         Available fields: {list(sample.keys())[:10]}...")
                    print()
                
            except ApifyApiError as e:
                error_str = str(e).lower()
                if "rent" in error_str or "trial" in error_str or "paid" in error_str:
                    print(f"      ❌ Requires payment/rental")
                elif "plan" in error_str:
                    print(f"      ❌ Plan limitation")
                else:
                    print(f"      ❌ Error: {str(e)[:100]}")
                print()
                
    except ApifyApiError as e:
        error_str = str(e).lower()
        if "not found" in error_str:
            print(f"   ❌ Actor not found")
        else:
            print(f"   ❌ Error: {str(e)[:100]}")
        print()
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)[:100]}")
        print()

print("="*80)
print("RECOMMENDATION:")
print("="*80)
print()
print("If any actor showed '⭐ THIS ACTOR WORKS!', update t.py to use that actor.")
print("If none work, the user may need to:")
print("  1. Rent the danek/twitter-timeline actor")
print("  2. Subscribe to a paid Apify plan with public actor access")
print("  3. Use a different Twitter data source (API, paid actor, etc.)")
print()




