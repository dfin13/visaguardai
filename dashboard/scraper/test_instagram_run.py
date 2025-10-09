#!/usr/bin/env python
"""
Test script for Instagram scraper - verifies real data extraction.
Usage: python test_instagram_run.py [username]
"""
import sys
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from dashboard.scraper.instagram import analyze_instagram_posts
import json


def test_instagram_scraper(username="natgeo", limit=3):
    """Test Instagram scraper with a real username"""
    print(f"\n{'='*80}")
    print(f"TESTING INSTAGRAM SCRAPER")
    print(f"{'='*80}")
    print(f"Username: {username}")
    print(f"Limit: {limit} posts")
    print()
    
    # Run the scraper
    results = analyze_instagram_posts(username, limit=limit)
    
    print(f"\n{'='*80}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*80}")
    print(f"Total posts scraped: {len(results)}")
    
    if results:
        print(f"\n{'='*80}")
        print(f"FIRST POST DETAILS")
        print(f"{'='*80}")
        first_post = results[0]
        
        # Check for structured post_data
        if 'post_data' in first_post:
            post_data = first_post['post_data']
            print(f"\nPost Data Fields:")
            print(f"  post_id: {post_data.get('post_id')}")
            print(f"  type: {post_data.get('type')}")
            print(f"  caption_present: {bool(post_data.get('caption'))}")
            print(f"  created_at: {post_data.get('created_at')}")
            print(f"  likes_count: {post_data.get('likes_count')}")
            print(f"  comments_count: {post_data.get('comments_count')}")
            print(f"  post_url: {post_data.get('post_url')}")
            print(f"  display_url_present: {bool(post_data.get('display_url'))}")
            print(f"  hashtags: {post_data.get('hashtags', [])[:3]}")
            print(f"  mentions: {post_data.get('mentions', [])[:3]}")
            print(f"  location: {post_data.get('location_name')}")
            print(f"  data_unavailable: {post_data.get('data_unavailable', False)}")
            
            print(f"\n✅ DATA QUALITY CHECK:")
            print(f"  Caption present: {'✅' if post_data.get('caption') else '❌'}")
            print(f"  Media present: {'✅' if post_data.get('display_url') or post_data.get('images') else '❌'}")
            print(f"  Timestamp present: {'✅' if post_data.get('created_at') else '❌'}")
            print(f"  Engagement data: {'✅' if post_data.get('likes_count') is not None else '❌'}")
            print(f"  Post URL: {'✅' if post_data.get('post_url') else '❌'}")
            
            if post_data.get('caption'):
                print(f"\nCaption preview (first 150 chars):")
                print(f"  {post_data['caption'][:150]}...")
        
        # Check analysis
        if 'analysis' in first_post:
            analysis = first_post['analysis']
            print(f"\nAnalysis Present: ✅")
            if 'Instagram' in analysis:
                risk_score = analysis['Instagram'].get('risk_score', -1)
                print(f"  Risk Score: {risk_score}")
    
    print(f"\n{'='*80}")
    print(f"FULL RESULT (First Post):")
    print(f"{'='*80}")
    print(json.dumps(results[0] if results else {}, indent=2, default=str))
    
    return results


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "natgeo"
    test_instagram_scraper(username, limit=3)

