#!/usr/bin/env python3
"""
Facebook Analysis Pipeline Diagnostic Script
Tests: isabelle.finney profile with 2 post limit
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django environment
sys.path.insert(0, '/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from apify_client import ApifyClient
from dashboard.models import Config

# Get API key
config = Config.objects.first()
if not config or not config.Apify_api_key:
    print("❌ ERROR: No Apify API key found in database")
    sys.exit(1)

APIFY_API_TOKEN = config.Apify_api_key
apify_client = ApifyClient(APIFY_API_TOKEN)

print("╔══════════════════════════════════════════════════════════════════════╗")
print("║                                                                      ║")
print("║       FACEBOOK ANALYSIS PIPELINE DIAGNOSTIC                         ║")
print("║                                                                      ║")
print("╚══════════════════════════════════════════════════════════════════════╝")
print()

# Test configuration
TEST_TARGET = "isabelle.finney"
LIMIT = 2

print(f"🎯 Target: {TEST_TARGET}")
print(f"📊 Limit: {LIMIT} posts")
print()

# ============================================================================
# STEP 1: Test Facebook Scraper
# ============================================================================
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 1: Testing Facebook Scraper")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

fb_url = f"https://www.facebook.com/{TEST_TARGET}"
print(f"📍 Scraping URL: {fb_url}")
print()

run_input = {
    "startUrls": [{"url": fb_url}],
    "resultsLimit": LIMIT,
    "scrapePostsUntilDate": None,
    "includeReactions": True,  # Changed from False
    "includeComments": True,   # Changed from False
    "includePostUrls": True    # Changed from False
}

print("⚙️  Scraper Configuration:")
print(json.dumps(run_input, indent=2))
print()

try:
    print("🚀 Starting Apify actor: apify/facebook-posts-scraper")
    print("⏳ Please wait...")
    
    run = apify_client.actor("apify/facebook-posts-scraper").call(run_input=run_input)
    
    print(f"✅ Scraper completed!")
    print(f"📦 Dataset ID: {run['defaultDatasetId']}")
    print()
    
    # Collect raw items
    print("📥 Fetching raw data from dataset...")
    raw_items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    
    print(f"✅ Retrieved {len(raw_items)} items")
    print()
    
    if len(raw_items) == 0:
        print("❌ ERROR: No posts retrieved from scraper!")
        print("   Possible reasons:")
        print("   - Profile is private")
        print("   - Profile doesn't exist")
        print("   - Facebook blocked the scraper")
        print("   - No posts on profile")
        sys.exit(1)
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("RAW SCRAPER DATA (First Item)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("Available fields:")
    for key in raw_items[0].keys():
        print(f"  • {key}")
    print()
    
    print("Full first item:")
    print(json.dumps(raw_items[0], indent=2, default=str))
    print()
    
    # ============================================================================
    # STEP 2: Extract Post Data
    # ============================================================================
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("STEP 2: Extracting Post Data")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    posts_data = []
    for idx, item in enumerate(raw_items, 1):
        print(f"📄 Post {idx}:")
        
        # Extract all possible fields
        post_text = item.get("text", "").strip()
        post_url = (
            item.get("url") or 
            item.get("post_url") or 
            item.get("postUrl") or 
            item.get("link") or 
            item.get("permalink") or 
            None
        )
        timestamp = (
            item.get("timestamp") or 
            item.get("created_at") or 
            item.get("date") or 
            item.get("time") or 
            None
        )
        likes_count = (
            item.get("likes") or 
            item.get("likesCount") or 
            item.get("reactions") or 
            item.get("reactionsCount") or 
            0
        )
        comments_count = (
            item.get("comments") or 
            item.get("commentsCount") or 
            item.get("comment_count") or 
            0
        )
        shares_count = (
            item.get("shares") or 
            item.get("sharesCount") or 
            item.get("share_count") or 
            0
        )
        
        print(f"  Text: {post_text[:80]}{'...' if len(post_text) > 80 else ''}")
        print(f"  URL: {post_url or 'NOT FOUND'}")
        print(f"  Timestamp: {timestamp or 'NOT FOUND'}")
        print(f"  Likes: {likes_count}")
        print(f"  Comments: {comments_count}")
        print(f"  Shares: {shares_count}")
        print()
        
        post_dict = {
            'caption': post_text,
            'text': post_text,
            'post_text': post_text,
            'post_url': post_url,
            'created_at': timestamp,
            'timestamp': timestamp,
            'likes_count': likes_count,
            'comments_count': comments_count,
            'shares_count': shares_count,
            'type': 'post',
            'hashtags': [],
            'mentions': [],
        }
        
        posts_data.append(post_dict)
    
    # ============================================================================
    # STEP 3: Test AI Analyzer
    # ============================================================================
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("STEP 3: Testing AI Analyzer")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    from dashboard.intelligent_analyzer import analyze_posts_batch
    
    print(f"🤖 Analyzing {len(posts_data)} posts with AI...")
    print()
    
    try:
        results = analyze_posts_batch("Facebook", posts_data)
        
        print(f"✅ AI Analysis completed!")
        print(f"📊 Results count: {len(results)}")
        print()
        
        for idx, result in enumerate(results, 1):
            print(f"━━━ Analysis Result {idx} ━━━")
            print()
            
            if 'analysis' in result and 'Facebook' in result['analysis']:
                fb_analysis = result['analysis']['Facebook']
                
                print(f"  Risk Score: {fb_analysis.get('risk_score', 'N/A')}")
                print()
                
                print("  Content Strength:")
                if 'content_reinforcement' in fb_analysis:
                    print(f"    Status: {fb_analysis['content_reinforcement'].get('status', 'N/A')}")
                    print(f"    Reason: {fb_analysis['content_reinforcement'].get('reason', 'N/A')[:80]}...")
                print()
                
                print("  Content Concern:")
                if 'content_suppression' in fb_analysis:
                    print(f"    Status: {fb_analysis['content_suppression'].get('status', 'N/A')}")
                    print(f"    Reason: {fb_analysis['content_suppression'].get('reason', 'N/A')[:80]}...")
                print()
                
                print("  Content Risk:")
                if 'content_flag' in fb_analysis:
                    print(f"    Status: {fb_analysis['content_flag'].get('status', 'N/A')}")
                    print(f"    Reason: {fb_analysis['content_flag'].get('reason', 'N/A')[:80]}...")
                print()
            else:
                print("  ❌ ERROR: Missing analysis structure")
                print(f"  Raw result: {json.dumps(result, indent=2)[:200]}...")
                print()
        
        # ============================================================================
        # STEP 4: Check Template Data Structure
        # ============================================================================
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("STEP 4: Verifying Template Data Structure")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        
        template_ready = True
        
        for idx, result in enumerate(results, 1):
            print(f"Checking Post {idx}:")
            
            # Check required fields for template
            has_post = 'post' in result
            has_post_data = 'post_data' in result
            has_analysis = 'analysis' in result and 'Facebook' in result['analysis']
            has_post_url = has_post_data and result.get('post_data', {}).get('post_url')
            
            print(f"  ✓ Has 'post' field: {has_post}")
            print(f"  ✓ Has 'post_data' field: {has_post_data}")
            print(f"  ✓ Has 'analysis.Facebook' field: {has_analysis}")
            print(f"  ✓ Has 'post_data.post_url' field: {has_post_url}")
            print()
            
            if not (has_post and has_post_data and has_analysis):
                template_ready = False
                print(f"  ❌ Post {idx} missing required fields!")
                print()
        
        if template_ready:
            print("✅ All posts have correct structure for template rendering")
        else:
            print("❌ Some posts missing required fields for template")
        print()
        
        # ============================================================================
        # SUMMARY
        # ============================================================================
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("DIAGNOSTIC SUMMARY")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        
        print(f"✅ Scraper: Retrieved {len(raw_items)} posts")
        print(f"✅ Analyzer: Analyzed {len(results)} posts")
        print(f"{'✅' if template_ready else '❌'} Template: Data structure {'correct' if template_ready else 'incomplete'}")
        print()
        
        # Check for missing data
        missing_issues = []
        for idx, result in enumerate(results, 1):
            if not result.get('post_data', {}).get('post_url'):
                missing_issues.append(f"Post {idx}: Missing post_url")
            if not result.get('post_data', {}).get('created_at'):
                missing_issues.append(f"Post {idx}: Missing timestamp")
        
        if missing_issues:
            print("⚠️  Issues found:")
            for issue in missing_issues:
                print(f"   • {issue}")
        else:
            print("✅ No issues found - pipeline is working correctly!")
        print()
        
    except Exception as e:
        import traceback
        print(f"❌ AI Analysis failed!")
        print(f"Error: {e}")
        print(f"Traceback:")
        print(traceback.format_exc())
        sys.exit(1)
        
except Exception as e:
    import traceback
    print(f"❌ Scraper failed!")
    print(f"Error: {e}")
    print(f"Traceback:")
    print(traceback.format_exc())
    sys.exit(1)

print()
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║                    DIAGNOSTIC COMPLETE                               ║")
print("╚══════════════════════════════════════════════════════════════════════╝")

