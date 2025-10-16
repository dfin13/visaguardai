#!/usr/bin/env python
"""
Test AI analysis for ALL platforms to determine if issue is Twitter-specific or global
"""

import os
import sys
import django

# Django setup
sys.path.append('/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*80)
print("🧪 MULTI-PLATFORM AI ANALYSIS TEST")
print("="*80 + "\n")

print("🎯 Goal: Determine if OpenRouter 401 error affects:")
print("   • Twitter only (Twitter-specific issue)")
print("   • All platforms (global OpenRouter key issue)")
print()

# Mock post data for each platform (same content for consistency)
test_content = "Excited to announce our new project! Check it out. #innovation #tech"

mock_data = {
    "Instagram": {
        'caption': test_content,
        'post_url': 'https://instagram.com/p/test123',
        'timestamp': 'Mon Oct 13 12:00:00 +0000 2025',
        'likes_count': 100,
        'comments_count': 20,
    },
    "LinkedIn": {
        'text': test_content,
        'post_url': 'https://linkedin.com/post/test123',
        'timestamp': 'Mon Oct 13 12:00:00 +0000 2025',
        'likes_count': 100,
        'comments_count': 20,
    },
    "Facebook": {
        'text': test_content,
        'post_url': 'https://facebook.com/post/test123',
        'timestamp': 'Mon Oct 13 12:00:00 +0000 2025',
        'likes_count': 100,
        'comments_count': 20,
    },
    "Twitter": {
        'text': test_content,
        'post_url': 'https://twitter.com/user/status/test123',
        'timestamp': 'Mon Oct 13 12:00:00 +0000 2025',
        'likes_count': 100,
        'comments_count': 20,
        'shares_count': 10,
    }
}

from dashboard.intelligent_analyzer import analyze_post_intelligent

results = {}

for platform, post_data in mock_data.items():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"TESTING: {platform}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    try:
        print(f"⏳ Analyzing {platform} post...")
        result = analyze_post_intelligent(platform, post_data)
        
        print(f"✅ {platform} analysis SUCCEEDED")
        print(f"   Risk Score: {result.get('risk_score')}")
        print(f"   Reinforcement: {result.get('content_reinforcement', {}).get('status')}")
        print()
        
        results[platform] = {"status": "SUCCESS", "result": result}
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ {platform} analysis FAILED")
        print(f"   Error: {error_str[:100]}...")
        print()
        
        is_401 = "401" in error_str
        results[platform] = {
            "status": "FAILED",
            "error": error_str,
            "is_401": is_401
        }

# Summary
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("SUMMARY")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

success_count = sum(1 for r in results.values() if r["status"] == "SUCCESS")
fail_count = sum(1 for r in results.values() if r["status"] == "FAILED")
error_401_count = sum(1 for r in results.values() if r.get("is_401", False))

print(f"✅ Successful: {success_count}/4 platforms")
print(f"❌ Failed: {fail_count}/4 platforms")
print(f"🔐 401 Errors: {error_401_count}/4 platforms")
print()

print("Platform Status:")
for platform, result in results.items():
    status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
    print(f"  {status_icon} {platform}: {result['status']}")

print()

# Diagnosis
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("DIAGNOSIS")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if success_count == 4:
    print("✅ ALL PLATFORMS WORKING")
    print("   OpenRouter API is functional")
    print("   No Twitter-specific issue")
    
elif success_count == 0 and error_401_count == 4:
    print("❌ ALL PLATFORMS FAILING WITH 401")
    print()
    print("Root Cause:")
    print("  • OpenRouter API key is invalid, expired, or has no credits")
    print("  • This is NOT a Twitter-specific issue")
    print("  • All platforms (Instagram, LinkedIn, Facebook, Twitter) are affected")
    print()
    print("Solution:")
    print("  1. Go to https://openrouter.ai/keys")
    print("  2. Check if current key is active")
    print("  3. Verify account has credits/balance")
    print("  4. Generate a new API key if needed")
    print("  5. Update .env file with new key:")
    print("     OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx")
    print("  6. Restart Django server")
    
elif success_count > 0 and results["Twitter"]["status"] == "FAILED":
    print("⚠️  TWITTER FAILING, OTHER PLATFORMS WORKING")
    print()
    print("This is a Twitter-specific issue.")
    print("   Instagram: " + results["Instagram"]["status"])
    print("   LinkedIn: " + results["LinkedIn"]["status"])
    print("   Facebook: " + results["Facebook"]["status"])
    print("   Twitter: " + results["Twitter"]["status"])
    print()
    print("Possible causes:")
    print("  • Twitter data format differs from other platforms")
    print("  • Twitter-specific code path has an issue")
    print("  • Requires further investigation")
    
else:
    print("⚠️  MIXED RESULTS")
    print()
    print("Some platforms work, some don't:")
    for platform, result in results.items():
        print(f"  • {platform}: {result['status']}")
    print()
    print("This suggests intermittent API issues or rate limiting")

print()
print("="*80)
print("TEST COMPLETE")
print("="*80)




