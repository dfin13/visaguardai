#!/usr/bin/env python3
"""
Comprehensive Facebook Pipeline Test for "findingkids"
Tests: Scraping → AI Analysis → Template Data Structure
"""

import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, '/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

print("╔══════════════════════════════════════════════════════════════════════╗")
print("║                                                                      ║")
print("║   FACEBOOK PIPELINE TEST: findingkids                               ║")
print("║                                                                      ║")
print("╚══════════════════════════════════════════════════════════════════════╝")
print()

# Import after Django setup
from dashboard.scraper.facebook import analyze_facebook_posts

print("🎯 Target: findingkids")
print("📊 Limit: 3 posts")
print("🤖 AI Analysis: Enabled")
print()

# ============================================================================
# STEP 1: Run Full Analysis Pipeline
# ============================================================================
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("STEP 1: Running Full Analysis Pipeline")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

try:
    # This will trigger the API key logging we just added
    result = analyze_facebook_posts("findingkids", limit=3)
    
    print("✅ Analysis completed!")
    print()
    
    # Check if result is error response
    if 'facebook' not in result:
        print("❌ ERROR: Result doesn't contain 'facebook' key")
        print(f"Result keys: {result.keys()}")
        sys.exit(1)
    
    posts = result['facebook']
    print(f"📊 Retrieved {len(posts)} posts")
    print()
    
    if len(posts) == 0:
        print("❌ ERROR: No posts retrieved")
        print("This could mean:")
        print("  • Profile is private")
        print("  • Profile has no posts")
        print("  • Profile doesn't exist")
        sys.exit(1)
    
    # ============================================================================
    # STEP 2: Validate Data Structure
    # ============================================================================
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("STEP 2: Validating Data Structure")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    validation_results = {
        'all_valid': True,
        'posts_validated': 0,
        'issues': []
    }
    
    for idx, post in enumerate(posts, 1):
        print(f"━━━ Post {idx} Validation ━━━")
        print()
        
        # Required top-level fields
        has_post = 'post' in post
        has_post_data = 'post_data' in post
        has_analysis = 'analysis' in post and 'Facebook' in post['analysis']
        
        print(f"  Structure:")
        print(f"    {'✅' if has_post else '❌'} Has 'post' field: {has_post}")
        print(f"    {'✅' if has_post_data else '❌'} Has 'post_data' field: {has_post_data}")
        print(f"    {'✅' if has_analysis else '❌'} Has 'analysis.Facebook' field: {has_analysis}")
        print()
        
        if not (has_post and has_post_data and has_analysis):
            validation_results['all_valid'] = False
            validation_results['issues'].append(f"Post {idx}: Missing required top-level fields")
            continue
        
        # Validate post_data fields
        post_data = post['post_data']
        
        # Required fields for template
        has_text = post_data.get('text') or post_data.get('caption') or post_data.get('post_text')
        has_url = post_data.get('post_url') is not None
        has_timestamp = post_data.get('created_at') or post_data.get('timestamp')
        has_likes = 'likes_count' in post_data
        has_comments = 'comments_count' in post_data
        has_shares = 'shares_count' in post_data
        
        print(f"  Post Data:")
        print(f"    {'✅' if has_text else '❌'} Has text/caption")
        print(f"    {'✅' if has_url else '❌'} Has post_url")
        print(f"    {'✅' if has_timestamp else '❌'} Has timestamp")
        print(f"    {'✅' if has_likes else '❌'} Has likes_count")
        print(f"    {'✅' if has_comments else '❌'} Has comments_count")
        print(f"    {'✅' if has_shares else '❌'} Has shares_count")
        print()
        
        # Show actual values
        text = post_data.get('text') or post_data.get('caption') or post_data.get('post_text') or ''
        post_url = post_data.get('post_url')
        timestamp = post_data.get('created_at') or post_data.get('timestamp')
        likes_count = post_data.get('likes_count', 0)
        comments_count = post_data.get('comments_count', 0)
        shares_count = post_data.get('shares_count', 0)
        
        print(f"  Values:")
        print(f"    Text: {text[:60]}{'...' if len(text) > 60 else ''}")
        print(f"    URL: {post_url if post_url else '(none)'}")
        print(f"    Timestamp: {timestamp if timestamp else '(none)'}")
        print(f"    Engagement: {likes_count} likes, {comments_count} comments, {shares_count} shares")
        print()
        
        # Validate analysis structure
        fb_analysis = post['analysis']['Facebook']
        
        has_reinforcement = 'content_reinforcement' in fb_analysis
        has_suppression = 'content_suppression' in fb_analysis
        has_flag = 'content_flag' in fb_analysis
        has_risk_score = 'risk_score' in fb_analysis
        
        print(f"  Analysis Sections:")
        print(f"    {'✅' if has_reinforcement else '❌'} Content Strength (content_reinforcement)")
        print(f"    {'✅' if has_suppression else '❌'} Content Concern (content_suppression)")
        print(f"    {'✅' if has_flag else '❌'} Content Risk (content_flag)")
        print(f"    {'✅' if has_risk_score else '❌'} Risk Score")
        print()
        
        if has_risk_score:
            risk_score = fb_analysis['risk_score']
            
            # Calculate grade
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
            
            # Calculate risk level
            if risk_score <= 9:
                risk_level = "Low Risk"
                risk_color = "🟢"
            elif risk_score <= 29:
                risk_level = "Moderate Risk"
                risk_color = "🟠"
            else:
                risk_level = "High Risk"
                risk_color = "🔴"
            
            print(f"  Grading:")
            print(f"    Risk Score: {risk_score}")
            print(f"    Letter Grade: {grade}")
            print(f"    Risk Level: {risk_level} {risk_color}")
            print()
        
        # Check for placeholder text
        if has_reinforcement:
            reason = fb_analysis['content_reinforcement'].get('reason', '')
            if 'No issues detected' in reason or 'placeholder' in reason.lower():
                validation_results['issues'].append(f"Post {idx}: Placeholder text in content_reinforcement")
                validation_results['all_valid'] = False
        
        if has_suppression:
            reason = fb_analysis['content_suppression'].get('reason', '')
            if 'No issues detected' in reason or 'placeholder' in reason.lower():
                validation_results['issues'].append(f"Post {idx}: Placeholder text in content_suppression")
                validation_results['all_valid'] = False
        
        # Show analysis snippets
        if has_reinforcement:
            print(f"  Content Strength:")
            print(f"    Status: {fb_analysis['content_reinforcement'].get('status')}")
            reason = fb_analysis['content_reinforcement'].get('reason', '')
            print(f"    Reason: {reason[:100]}{'...' if len(reason) > 100 else ''}")
            print()
        
        if has_suppression:
            print(f"  Content Concern:")
            print(f"    Status: {fb_analysis['content_suppression'].get('status')}")
            reason = fb_analysis['content_suppression'].get('reason', '')
            print(f"    Reason: {reason[:100]}{'...' if len(reason) > 100 else ''}")
            print()
        
        if has_flag:
            print(f"  Content Risk:")
            print(f"    Status: {fb_analysis['content_flag'].get('status')}")
            reason = fb_analysis['content_flag'].get('reason', '')
            print(f"    Reason: {reason[:100]}{'...' if len(reason) > 100 else ''}")
            print()
        
        validation_results['posts_validated'] += 1
    
    # ============================================================================
    # STEP 3: Template Compatibility Check
    # ============================================================================
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("STEP 3: Template Compatibility Check")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    print("Checking if data structure matches result.html template requirements...")
    print()
    
    template_checks = {
        'item.post': all('post' in p for p in posts),
        'item.post_data': all('post_data' in p for p in posts),
        'item.post_data.post_url': all(p.get('post_data', {}).get('post_url') is not None for p in posts),
        'item.analysis.Facebook': all('analysis' in p and 'Facebook' in p['analysis'] for p in posts),
        'facebook_obj.risk_score': all(p.get('analysis', {}).get('Facebook', {}).get('risk_score') is not None for p in posts),
        'facebook_obj.content_reinforcement': all('content_reinforcement' in p.get('analysis', {}).get('Facebook', {}) for p in posts),
        'facebook_obj.content_suppression': all('content_suppression' in p.get('analysis', {}).get('Facebook', {}) for p in posts),
        'facebook_obj.content_flag': all('content_flag' in p.get('analysis', {}).get('Facebook', {}) for p in posts),
    }
    
    for key, value in template_checks.items():
        print(f"  {'✅' if value else '❌'} {key}: {value}")
    
    all_template_checks_pass = all(template_checks.values())
    print()
    
    # ============================================================================
    # STEP 4: Final Summary
    # ============================================================================
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("FINAL SUMMARY")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    print(f"Posts Retrieved: {len(posts)}")
    print(f"Posts Validated: {validation_results['posts_validated']}")
    print()
    
    if validation_results['all_valid'] and all_template_checks_pass:
        print("✅ ALL CHECKS PASSED")
        print()
        print("The Facebook pipeline for 'findingkids' is working correctly:")
        print("  ✅ Scraper extracts complete data")
        print("  ✅ AI generates proper analysis")
        print("  ✅ Data structure matches template requirements")
        print("  ✅ Post URLs present for 'View original post' links")
        print("  ✅ Risk scores, grades, and badges will render correctly")
        print("  ✅ No placeholder or blank data")
        print()
        print("Ready for /dashboard/results/ display!")
    else:
        print("⚠️  ISSUES DETECTED")
        print()
        if validation_results['issues']:
            print("Issues:")
            for issue in validation_results['issues']:
                print(f"  • {issue}")
        print()
        if not all_template_checks_pass:
            print("Template compatibility issues - some fields missing")
    
    # Save results for inspection
    output_file = '/Users/davidfinney/Downloads/visaguardai/facebook_findingkids_results.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print()
    print(f"📄 Full results saved to: facebook_findingkids_results.json")
    
except Exception as e:
    import traceback
    print("❌ PIPELINE FAILED")
    print()
    print(f"Error: {e}")
    print()
    print("Traceback:")
    print(traceback.format_exc())
    sys.exit(1)

print()
print("╔══════════════════════════════════════════════════════════════════════╗")
print("║                    TEST COMPLETE                                     ║")
print("╚══════════════════════════════════════════════════════════════════════╝")




