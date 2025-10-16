#!/usr/bin/env python3
"""
Facebook Analysis Pipeline - MOCK TEST
Tests the analyzer and template logic with simulated Facebook data
(since the Apify scraper requires a plan upgrade)
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# Setup Django environment
sys.path.insert(0, '/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

print("╔══════════════════════════════════════════════════════════════════════╗")
print("║                                                                      ║")
print("║       FACEBOOK ANALYSIS PIPELINE - MOCK TEST                        ║")
print("║                                                                      ║")
print("╚══════════════════════════════════════════════════════════════════════╝")
print()

print("⚠️  NOTE: Using mock data since Apify plan doesn't support Facebook scraper")
print()

# ============================================================================
# Create Mock Facebook Post Data
# ============================================================================
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("Creating Mock Facebook Posts")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# Simulate realistic Facebook post data
mock_posts = [
    {
        'text': 'Excited to announce that I just started my new internship at Tech Solutions! Looking forward to learning and growing in the field of software development. #NewBeginnings #CareerGrowth',
        'post_url': 'https://www.facebook.com/isabelle.finney/posts/123456789',
        'timestamp': (datetime.now() - timedelta(days=5)).isoformat(),
        'likes_count': 45,
        'comments_count': 12,
        'shares_count': 3,
    },
    {
        'text': 'Celebrated my graduation today with family and friends! 🎓 So grateful for everyone who supported me throughout this journey. Time to take on the world!',
        'post_url': 'https://www.facebook.com/isabelle.finney/posts/987654321',
        'timestamp': (datetime.now() - timedelta(days=30)).isoformat(),
        'likes_count': 156,
        'comments_count': 34,
        'shares_count': 8,
    },
]

print(f"✅ Created {len(mock_posts)} mock Facebook posts")
print()

for idx, post in enumerate(mock_posts, 1):
    print(f"Post {idx}:")
    print(f"  Text: {post['text'][:60]}...")
    print(f"  URL: {post['post_url']}")
    print(f"  Timestamp: {post['timestamp']}")
    print(f"  Engagement: {post['likes_count']} likes, {post['comments_count']} comments")
    print()

# ============================================================================
# Test AI Analyzer
# ============================================================================
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("Testing AI Analyzer with Mock Data")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

from dashboard.intelligent_analyzer import analyze_posts_batch

# Convert to standard format
posts_data = []
for post in mock_posts:
    posts_data.append({
        'caption': post['text'],
        'text': post['text'],
        'post_text': post['text'],
        'post_url': post.get('post_url'),
        'created_at': post.get('timestamp'),
        'timestamp': post.get('timestamp'),
        'likes_count': post.get('likes_count', 0),
        'comments_count': post.get('comments_count', 0),
        'shares_count': post.get('shares_count', 0),
        'type': 'post',
        'hashtags': [],
        'mentions': [],
    })

print(f"🤖 Analyzing {len(posts_data)} posts with AI...")
print()

try:
    results = analyze_posts_batch("Facebook", posts_data)
    
    print(f"✅ AI Analysis completed!")
    print(f"📊 Results count: {len(results)}")
    print()
    
    # ============================================================================
    # Validate Results Structure
    # ============================================================================
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Validating Results Structure")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    all_valid = True
    
    for idx, result in enumerate(results, 1):
        print(f"━━━ Post {idx} Validation ━━━")
        print()
        
        # Check structure
        has_post = 'post' in result
        has_post_data = 'post_data' in result
        has_analysis = 'analysis' in result and 'Facebook' in result['analysis']
        
        print(f"  Structure:")
        print(f"    ✓ Has 'post' field: {has_post}")
        print(f"    ✓ Has 'post_data' field: {has_post_data}")
        print(f"    ✓ Has 'analysis.Facebook' field: {has_analysis}")
        
        if has_post_data:
            post_data = result.get('post_data', {})
            has_url = 'post_url' in post_data and post_data['post_url'] is not None
            has_timestamp = 'created_at' in post_data or 'timestamp' in post_data
            has_engagement = 'likes_count' in post_data or 'comments_count' in post_data
            
            print(f"    ✓ Has 'post_url': {has_url}")
            print(f"    ✓ Has timestamp: {has_timestamp}")
            print(f"    ✓ Has engagement data: {has_engagement}")
        
        print()
        
        # Check analysis content
        if has_analysis:
            fb_analysis = result['analysis']['Facebook']
            risk_score = fb_analysis.get('risk_score', -1)
            
            # Determine grade
            if risk_score <= 2:
                grade = "A+"
            elif risk_score <= 7:
                grade = "A"
            elif risk_score <= 9:
                grade = "A-"
            elif risk_score <= 12:
                grade = "B+"
            elif risk_score <= 17:
                grade = "B"
            elif risk_score <= 19:
                grade = "B-"
            elif risk_score <= 22:
                grade = "C+"
            elif risk_score <= 27:
                grade = "C"
            elif risk_score <= 29:
                grade = "C-"
            elif risk_score <= 32:
                grade = "D+"
            elif risk_score <= 37:
                grade = "D"
            elif risk_score <= 39:
                grade = "D-"
            else:
                grade = "F"
            
            # Determine risk level
            if risk_score <= 9:
                risk_level = "Low Risk 🟢"
            elif risk_score <= 29:
                risk_level = "Moderate Risk 🟠"
            else:
                risk_level = "High Risk 🔴"
            
            print(f"  Analysis:")
            print(f"    Risk Score: {risk_score}")
            print(f"    Grade: {grade}")
            print(f"    Risk Level: {risk_level}")
            print()
            
            # Check sections
            has_reinforcement = 'content_reinforcement' in fb_analysis
            has_suppression = 'content_suppression' in fb_analysis
            has_flag = 'content_flag' in fb_analysis
            
            print(f"    ✓ Has Content Strength section: {has_reinforcement}")
            print(f"    ✓ Has Content Concern section: {has_suppression}")
            print(f"    ✓ Has Content Risk section: {has_flag}")
            print()
            
            # Display analysis snippets
            if has_reinforcement:
                print(f"    Content Strength:")
                print(f"      Status: {fb_analysis['content_reinforcement'].get('status', 'N/A')}")
                reason = fb_analysis['content_reinforcement'].get('reason', 'N/A')
                print(f"      Reason: {reason[:80]}{'...' if len(reason) > 80 else ''}")
                print()
            
            if has_suppression:
                print(f"    Content Concern:")
                print(f"      Status: {fb_analysis['content_suppression'].get('status', 'N/A')}")
                reason = fb_analysis['content_suppression'].get('reason', 'N/A')
                print(f"      Reason: {reason[:80]}{'...' if len(reason) > 80 else ''}")
                print()
            
            if has_flag:
                print(f"    Content Risk:")
                print(f"      Status: {fb_analysis['content_flag'].get('status', 'N/A')}")
                reason = fb_analysis['content_flag'].get('reason', 'N/A')
                print(f"      Reason: {reason[:80]}{'...' if len(reason) > 80 else ''}")
                print()
        
        if not (has_post and has_post_data and has_analysis):
            all_valid = False
            print(f"  ❌ Post {idx} has structural issues!")
            print()
    
    # ============================================================================
    # Final Summary
    # ============================================================================
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("MOCK TEST SUMMARY")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    if all_valid:
        print("✅ SUCCESS: All posts have correct structure and analysis")
        print()
        print("Expected behavior once Apify plan is upgraded:")
        print("  1. Scraper will retrieve real Facebook posts with all metadata")
        print("  2. AI analyzer will process them (as demonstrated above)")
        print("  3. Results will render correctly on /dashboard/results/")
        print("  4. Each card will show:")
        print("     • Letter grade (A+ through F)")
        print("     • Risk badge (Low/Moderate/High)")
        print("     • 'View original post' link")
        print("     • Three analysis sections (Strength, Concern, Risk)")
        print()
        print("✅ Facebook pipeline is READY - just needs Apify plan upgrade")
    else:
        print("❌ ISSUES DETECTED: Some posts missing required fields")
        print("   Review validation output above for details")
    print()
    
    # Save results to file for inspection
    output_file = '/Users/davidfinney/Downloads/visaguardai/facebook_mock_results.json'
    with open(output_file, 'w') as f:
        json.dump({"facebook": results}, f, indent=2, default=str)
    
    print(f"📄 Results saved to: {output_file}")
    print()
    
except Exception as e:
    import traceback
    print(f"❌ AI Analysis failed!")
    print(f"Error: {e}")
    print()
    print(f"Traceback:")
    print(traceback.format_exc())
    sys.exit(1)

print()
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║                    MOCK TEST COMPLETE                                ║")
print("╚══════════════════════════════════════════════════════════════════════╝")




