#!/usr/bin/env python3
"""
Clean Facebook Scraper Diagnostic
Tests apify/facebook-posts-scraper with current API key
No assumptions - shows exact API response
"""

import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, '/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from apify_client import ApifyClient
from dashboard.models import Config

print("╔══════════════════════════════════════════════════════════════════════╗")
print("║                                                                      ║")
print("║       FACEBOOK SCRAPER - CLEAN DIAGNOSTIC                           ║")
print("║                                                                      ║")
print("╚══════════════════════════════════════════════════════════════════════╝")
print()

# Get API key from database
config = Config.objects.first()
if not config or not config.Apify_api_key:
    print("❌ ERROR: No Apify API key found in Config model")
    sys.exit(1)

api_key = config.Apify_api_key
apify_client = ApifyClient(api_key)

print(f"🔑 Using API key: {api_key[:20]}...{api_key[-5:]}")
print()

# ============================================================================
# STEP 1: Check Account Permissions
# ============================================================================
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 1: Checking Account Permissions")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

try:
    user = apify_client.user().get()
    
    print(f"✅ Account authenticated")
    print(f"   Username: {user.get('username')}")
    print(f"   Email: {user.get('email')}")
    print()
    
    # Check plan features
    plan = user.get('plan', {})
    enabled_features = plan.get('enabledPlatformFeatures', [])
    
    print("Enabled Platform Features:")
    for feature in enabled_features:
        print(f"  • {feature}")
    print()
    
    # Check specific permissions
    has_actors_public_all = 'ACTORS_PUBLIC_ALL' in enabled_features
    has_actors_public_dev = 'ACTORS_PUBLIC_DEVELOPER' in enabled_features
    has_paid_actors = 'PAID_ACTORS_PER_EVENT' in enabled_features or 'PAID_ACTORS_FLAT_PRICE_PER_MONTH' in enabled_features or 'PAID_ACTORS_PER_DATASET_ITEM' in enabled_features
    
    print("Permission Analysis:")
    print(f"  {'✅' if has_actors_public_all else '❌'} ACTORS_PUBLIC_ALL: {has_actors_public_all}")
    print(f"  {'✅' if has_actors_public_dev else '❌'} ACTORS_PUBLIC_DEVELOPER: {has_actors_public_dev}")
    print(f"  {'✅' if has_paid_actors else '❌'} PAID_ACTORS (any): {has_paid_actors}")
    print()
    
    if has_actors_public_all:
        print("✅ Can run ALL public actors without subscription")
    elif has_actors_public_dev:
        print("⚠️  Can only run actors you've developed (DEVELOPER mode)")
        print("   Public store actors require subscription")
    else:
        print("❌ Cannot run public actors - subscription required")
    print()
    
    # Check usage limits
    monthly_usage = user.get('monthlyUsage', {})
    limits = plan.get('maxMonthlyUsageUsd', 0)
    
    if monthly_usage:
        print("Monthly Usage:")
        print(f"  Max allowed: ${limits}")
        print(f"  Compute units used: {monthly_usage.get('computeUnits', 0)}")
    print()
    
except Exception as e:
    print(f"❌ Failed to fetch account info: {e}")
    print()

# ============================================================================
# STEP 2: Test Facebook Posts Scraper (1 post only)
# ============================================================================
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 2: Testing Facebook Posts Scraper")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

actor_id = "apify/facebook-posts-scraper"
test_url = "https://www.facebook.com/natgeo"  # Public page with posts

print(f"🎯 Actor: {actor_id}")
print(f"📍 Test URL: {test_url}")
print(f"📊 Limit: 1 post (minimal test)")
print()

run_input = {
    "startUrls": [{"url": test_url}],
    "resultsLimit": 1,
    "scrapePostsUntilDate": None,
    "includeReactions": True,
    "includeComments": True,
    "includePostUrls": True
}

print("Run Input:")
print(json.dumps(run_input, indent=2))
print()

print("🚀 Attempting to run actor...")
print("⏳ This may take 30-60 seconds...")
print()

try:
    # Attempt to run the actor
    run = apify_client.actor(actor_id).call(
        run_input=run_input,
        timeout_secs=120  # 2 minute timeout
    )
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ SUCCESS - SCRAPER RAN SUCCESSFULLY!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    print(f"Run ID: {run.get('id')}")
    print(f"Status: {run.get('status')}")
    print(f"Dataset ID: {run.get('defaultDatasetId')}")
    print()
    
    # Fetch results
    print("📥 Fetching scraped data...")
    items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    
    print(f"✅ Retrieved {len(items)} item(s)")
    print()
    
    if len(items) > 0:
        print("━━━ Sample Data ━━━")
        first_item = items[0]
        
        # Show available fields
        print("Available fields:")
        for key in first_item.keys():
            value = first_item[key]
            if isinstance(value, str) and len(value) > 50:
                print(f"  • {key}: {value[:50]}...")
            else:
                print(f"  • {key}: {value}")
        print()
        
        # Check key fields
        has_text = 'text' in first_item and first_item['text']
        has_url = any(k in first_item for k in ['url', 'post_url', 'postUrl', 'link'])
        has_timestamp = any(k in first_item for k in ['timestamp', 'created_at', 'date'])
        has_engagement = any(k in first_item for k in ['likes', 'reactions', 'comments'])
        
        print("Data Quality Check:")
        print(f"  {'✅' if has_text else '❌'} Has text content")
        print(f"  {'✅' if has_url else '❌'} Has post URL")
        print(f"  {'✅' if has_timestamp else '❌'} Has timestamp")
        print(f"  {'✅' if has_engagement else '❌'} Has engagement data")
        print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("CONCLUSION:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("✅ Scraper is USABLE — no subscription needed!")
    print()
    print("The Facebook Posts Scraper works with your current API key.")
    print("You can proceed with using it in the application.")
    print()
    print("Run Statistics:")
    print(f"  • Compute units used: {run.get('stats', {}).get('computeUnitsUsed', 'N/A')}")
    print(f"  • Run time: {run.get('stats', {}).get('runTimeSecs', 'N/A')}s")
    print()
    
except Exception as e:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("❌ SCRAPER FAILED")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    error_str = str(e)
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {error_str}")
    print()
    
    # Try to parse error details
    if hasattr(e, 'response'):
        print("API Response Details:")
        try:
            response = e.response
            if hasattr(response, 'json'):
                error_json = response.json()
                print(json.dumps(error_json, indent=2))
            elif hasattr(response, 'text'):
                print(response.text)
        except:
            print("(Could not parse response)")
        print()
    
    # Analyze error type
    error_lower = error_str.lower()
    
    if "cannot run this public actor" in error_lower or "current plan does not support" in error_lower:
        print("📋 Diagnosis: SUBSCRIPTION REQUIRED")
        print()
        print("Your Apify plan does not include access to public actors.")
        print()
        print("Solutions:")
        print("1. Subscribe to this specific actor:")
        print("   → https://apify.com/apify/facebook-posts-scraper")
        print("   → Choose 'Pay per result' (~$0.01/post)")
        print()
        print("2. Upgrade your Apify plan to include public actors")
        print("   → https://console.apify.com/billing")
        print()
        
    elif "quota" in error_lower or "limit" in error_lower:
        print("📋 Diagnosis: QUOTA/LIMIT EXCEEDED")
        print()
        print("You may have hit a usage limit or quota.")
        print("Check your Apify console: https://console.apify.com")
        print()
        
    elif "authentication" in error_lower or "unauthorized" in error_lower or "invalid" in error_lower:
        print("📋 Diagnosis: AUTHENTICATION ISSUE")
        print()
        print("The API key may be invalid or expired.")
        print("Verify your key in: https://console.apify.com/account/integrations")
        print()
        
    elif "not found" in error_lower or "404" in error_lower:
        print("📋 Diagnosis: ACTOR NOT FOUND")
        print()
        print("The actor may not exist or is inaccessible.")
        print()
        
    else:
        print("📋 Diagnosis: UNKNOWN ERROR")
        print()
        print("The error doesn't match known patterns.")
        print("Please check the error message above for details.")
        print()
    
    print("Full Traceback:")
    import traceback
    print(traceback.format_exc())

print()
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║                    DIAGNOSTIC COMPLETE                               ║")
print("╚══════════════════════════════════════════════════════════════════════╝")




