#!/usr/bin/env python3
"""
TikTok Integration Audit Script
Tests TikTok scraper functionality with username: u9td
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
sys.path.insert(0, '/Users/davidfinney/Downloads/visaguardai')
django.setup()

from dashboard.scraper.tiktok import analyze_tiktok_profile
from dashboard.models import UserProfile
import json

print("╔══════════════════════════════════════════════════════════════════════╗")
print("║                                                                      ║")
print("║   🔍 TIKTOK INTEGRATION AUDIT - PRODUCTION READINESS TEST          ║")
print("║                                                                      ║")
print("╚══════════════════════════════════════════════════════════════════════╝\n")

# Test 1: Database Schema Check
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 1: Database Schema Verification")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

fields = [f.name for f in UserProfile._meta.get_fields()]
tiktok_fields = [f for f in fields if 'tiktok' in f.lower()]
twitter_fields = [f for f in fields if 'twitter' in f.lower()]

print(f"✅ TikTok fields found: {tiktok_fields}")
if twitter_fields:
    print(f"❌ WARNING: Twitter fields still exist: {twitter_fields}")
else:
    print(f"✅ Twitter fields removed: None found")

# Test 2: TikTok Scraper Functionality
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 2: TikTok Scraper Test with @u9td")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

test_username = "u9td"
print(f"🎵 Testing TikTok scraper with username: @{test_username}")
print(f"📊 Requesting 5 most recent videos...\n")

try:
    result = analyze_tiktok_profile(test_username, num_videos=5)
    
    # Parse result
    if isinstance(result, str):
        data = json.loads(result)
    else:
        data = result
    
    print(f"✅ Scraper executed successfully!")
    print(f"📹 Videos retrieved: {len(data) if isinstance(data, list) else 'N/A'}")
    
    if isinstance(data, list) and len(data) > 0:
        print(f"\n📋 Sample Video Data:")
        first_video = data[0]
        print(f"  • Caption: {first_video.get('post', 'N/A')[:80]}...")
        print(f"  • Has Analysis: {'✅' if 'analysis' in first_video else '❌'}")
        
        if 'analysis' in first_video and 'TikTok' in first_video['analysis']:
            analysis = first_video['analysis']['TikTok']
            print(f"  • Risk Score: {analysis.get('risk_score', 'N/A')}/10")
            print(f"  • Content Reinforcement: {analysis.get('content_reinforcement', {}).get('status', 'N/A')}")
            print(f"  • Content Suppression: {analysis.get('content_suppression', {}).get('status', 'N/A')}")
            print(f"  • Content Flag: {analysis.get('content_flag', {}).get('status', 'N/A')}")
        
        if 'post_data' in first_video:
            post_data = first_video['post_data']
            print(f"  • Post URL: {post_data.get('post_url', 'N/A')}")
            print(f"  • Timestamp: {post_data.get('timestamp', 'N/A')}")
            print(f"  • Likes: {post_data.get('likes_count', 0):,}")
            print(f"  • Comments: {post_data.get('comments_count', 0):,}")
            print(f"  • Shares: {post_data.get('shares_count', 0):,}")
            print(f"  • Views: {post_data.get('views_count', 0):,}")
    else:
        print(f"⚠️  No video data returned (may indicate profile is private or actor issue)")
        
except Exception as e:
    print(f"❌ Scraper failed with error: {e}")
    import traceback
    print(traceback.format_exc())

# Test 3: Environment Variables
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 3: API Keys Configuration")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

apify_key = os.getenv('APIFY_API_KEY')
openrouter_key = os.getenv('OPENROUTER_API_KEY')

print(f"✅ APIFY_API_KEY: {'Set (' + apify_key[:20] + '...)' if apify_key else '❌ Not set'}")
print(f"✅ OPENROUTER_API_KEY: {'Set (' + openrouter_key[:20] + '...)' if openrouter_key else '❌ Not set'}")

# Test 4: Actor ID Verification
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 4: Apify Actor Configuration")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# Check the actual actor ID used in tiktok.py
with open('/Users/davidfinney/Downloads/visaguardai/dashboard/scraper/tiktok.py', 'r') as f:
    content = f.read()
    if 'clockworks/tiktok-profile-scraper' in content:
        print("✅ Actor ID: clockworks/tiktok-profile-scraper")
    else:
        print("❌ WARNING: Actor ID not found or incorrect!")

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("AUDIT SUMMARY")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("\n✅ AUDIT COMPLETE - Review results above")
print("\nNext Steps:")
print("  1. Clear browser cache and test on https://visaguardai.com/dashboard/")
print("  2. Connect TikTok account with username 'u9td'")
print("  3. Run analysis and verify results display correctly")
print("\n")

