#!/usr/bin/env python
"""
Production Testing Suite - Verify All 4 Social Media Platforms
Tests actual analysis flow for Instagram, LinkedIn, Facebook, Twitter
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

from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

print("\n" + "="*80)
print("🧪 PRODUCTION TESTING SUITE - ALL 4 PLATFORMS")
print("="*80 + "\n")

print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Test accounts (use small, public accounts)
TEST_ACCOUNTS = {
    "Instagram": "visaguardai",  # Use your own account or a small public one
    "LinkedIn": "syedawaisalishah",  # Use a small public profile
    "Facebook": "findingkids",  # Public page
    "Twitter": "elonmusk"  # Public account
}

print("📋 Test Configuration:")
for platform, account in TEST_ACCOUNTS.items():
    print(f"  • {platform}: @{account}")
print()

# Results storage
results = {}

# Test each platform
platforms = [
    ("Instagram", "dashboard.scraper.instagram", "analyze_instagram_posts"),
    ("LinkedIn", "dashboard.scraper.linkedin", "analyze_linkedin_posts"),
    ("Facebook", "dashboard.scraper.facebook", "analyze_facebook_posts"),
    ("Twitter", "dashboard.scraper.t", "analyze_twitter_profile"),
]

for platform_name, module_path, function_name in platforms:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"TESTING: {platform_name}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    username = TEST_ACCOUNTS[platform_name]
    start_time = time.time()
    
    try:
        # Import the scraper function
        module_parts = module_path.split('.')
        module = __import__(module_path, fromlist=[function_name])
        scraper_function = getattr(module, function_name)
        
        print(f"⏳ Analyzing {platform_name} account: @{username}")
        print(f"   Limit: 10 posts (new cap)")
        print()
        
        # Run analysis
        if platform_name == "LinkedIn":
            # LinkedIn has special return format (posts, error)
            posts, error = scraper_function(username, limit=10)
            if error:
                raise Exception(f"LinkedIn returned error: {error}")
            result = posts
        elif platform_name == "Twitter":
            # Twitter uses tweets_desired parameter
            result = scraper_function(username, tweets_desired=10)
        else:
            # Instagram and Facebook
            result = scraper_function(username, limit=10)
        
        elapsed_time = time.time() - start_time
        
        # Parse result
        if isinstance(result, str):
            # JSON string response
            try:
                result = json.loads(result)
            except:
                pass
        
        # Validate result
        if isinstance(result, list):
            post_count = len(result)
        elif isinstance(result, dict):
            # Facebook returns {"facebook": [...]}
            if "facebook" in result:
                post_count = len(result["facebook"])
            else:
                post_count = 1
        else:
            post_count = 0
        
        # Check if posts were analyzed
        if post_count > 0:
            print(f"✅ {platform_name} Analysis SUCCESSFUL")
            print(f"   Posts analyzed: {post_count}")
            print(f"   Time elapsed: {elapsed_time:.2f} seconds")
            print()
            
            # Validate structure
            sample_post = result[0] if isinstance(result, list) else result.get("facebook", [{}])[0] if "facebook" in result else {}
            
            has_post_data = "post_data" in sample_post
            has_analysis = "analysis" in sample_post or platform_name in sample_post
            
            print(f"   Structure validation:")
            print(f"     • post_data: {'✅' if has_post_data else '❌'}")
            print(f"     • analysis: {'✅' if has_analysis else '❌'}")
            
            # Check for 10-post cap
            if post_count <= 10:
                print(f"     • 10-post cap: ✅ ({post_count} posts)")
            else:
                print(f"     • 10-post cap: ❌ ({post_count} posts - EXCEEDS LIMIT)")
            
            print()
            
            results[platform_name] = {
                "status": "SUCCESS",
                "post_count": post_count,
                "time": elapsed_time,
                "capped_correctly": post_count <= 10
            }
        else:
            print(f"⚠️  {platform_name} returned NO posts")
            print(f"   This could mean:")
            print(f"     • Account is private")
            print(f"     • Account has no posts")
            print(f"     • Scraper is blocked")
            print()
            
            results[platform_name] = {
                "status": "NO_POSTS",
                "post_count": 0,
                "time": elapsed_time,
                "capped_correctly": True
            }
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_str = str(e)
        
        print(f"❌ {platform_name} Analysis FAILED")
        print(f"   Error: {error_str[:100]}...")
        print(f"   Time elapsed: {elapsed_time:.2f} seconds")
        print()
        
        results[platform_name] = {
            "status": "FAILED",
            "error": error_str,
            "time": elapsed_time,
            "capped_correctly": None
        }
    
    print()

# Summary
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("SUMMARY")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

success_count = sum(1 for r in results.values() if r["status"] == "SUCCESS")
total_platforms = len(results)

print(f"Test Results: {success_count}/{total_platforms} platforms working")
print()

for platform, result in results.items():
    status_icon = "✅" if result["status"] == "SUCCESS" else "⚠️" if result["status"] == "NO_POSTS" else "❌"
    print(f"{status_icon} {platform}:")
    print(f"   Status: {result['status']}")
    if result["status"] == "SUCCESS":
        print(f"   Posts: {result['post_count']}")
        print(f"   10-post cap: {'✅ Working' if result['capped_correctly'] else '❌ NOT working'}")
    print(f"   Time: {result['time']:.2f}s")
    if "error" in result:
        print(f"   Error: {result['error'][:60]}...")
    print()

# Performance metrics
if success_count > 0:
    avg_time = sum(r["time"] for r in results.values() if r["status"] == "SUCCESS") / success_count
    print(f"📊 Performance:")
    print(f"   Average time per platform: {avg_time:.2f} seconds")
    print(f"   Expected with 10-post cap: 1-2 minutes per platform")
    print()

# 10-post cap verification
cap_working = all(r.get("capped_correctly", False) for r in results.values() if r["status"] == "SUCCESS")
if cap_working:
    print("✅ 10-POST CAP: All platforms respect the 10-post limit")
else:
    print("⚠️  10-POST CAP: Some platforms may exceed the limit")
print()

# Final verdict
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("FINAL VERDICT")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if success_count == total_platforms:
    print("🎉 ALL PLATFORMS WORKING PERFECTLY!")
    print()
    print("✅ Instagram: Operational")
    print("✅ LinkedIn: Operational")
    print("✅ Facebook: Operational")
    print("✅ Twitter: Operational")
    print()
    print("Production deployment is SUCCESSFUL!")
    print()
elif success_count >= 3:
    print("✅ MOSTLY WORKING (3+/4 platforms)")
    print()
    print(f"Working: {success_count}/{total_platforms} platforms")
    print("Production is functional but needs attention on failed platform(s)")
    print()
elif success_count >= 1:
    print("⚠️  PARTIALLY WORKING (1-2/4 platforms)")
    print()
    print(f"Working: {success_count}/{total_platforms} platforms")
    print("Multiple platforms need attention")
    print()
else:
    print("❌ DEPLOYMENT ISSUE")
    print()
    print("No platforms are working. Check:")
    print("  • Server status")
    print("  • API keys")
    print("  • Network connectivity")
    print()

print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("="*80)
print("✅ PRODUCTION TEST COMPLETE")
print("="*80)




