import json
import os
from apify_client import ApifyClient
from openai import OpenAI

from django.conf import settings
from dashboard.models import Config

# Get API keys from environment variables or Django settings
APIFY_API_TOKEN = os.getenv('APIFY_API_KEY') or getattr(settings, 'APIFY_API_KEY', None)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY') or getattr(settings, 'OPENROUTER_API_KEY', None)

# Fallback to database config if environment variables not set
if not APIFY_API_TOKEN or not OPENROUTER_API_KEY:
    config = Config.objects.first()
    if config:
        APIFY_API_TOKEN = config.Apify_api_key
        OPENROUTER_API_KEY = config.openrouter_api_key

# Ensure we have API keys
if not APIFY_API_TOKEN:
    raise ValueError("APIFY_API_KEY not found in environment variables or database config")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables or database config")

# ==== Initialize Clients ====
client_ai = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
apify_client = ApifyClient(APIFY_API_TOKEN)

# REMOVED: generate_fallback_instagram_posts function
# This function was creating fake Instagram posts when scraping failed.
# Instead, we now return proper "inaccessible account" responses.

def analyze_instagram_posts(username, limit=5):
    """
    Scrape & analyze Instagram posts.
    Returns proper response for inaccessible accounts instead of fabricating content.
    """
    from .account_checker import check_scraping_result, create_inaccessible_account_response, is_account_private_error

    print(f"\n🔍 INSTAGRAM ANALYSIS STARTING")
    print(f"   Username: {username}")
    print(f"   Limit: {limit} posts")

    # ==== SCRAPE INSTAGRAM POSTS ====
    run_input = {
        "username": [username],
        "resultsLimit": limit,
        "scrapePostsUntilDate": None,
        "shouldDownloadMedia": False,
    }

    print(f"📡 Triggering Apify Instagram scraper for {username}...")
    try:
        run = apify_client.actor("apify/instagram-post-scraper").call(run_input=run_input)
        print(f"✅ Apify run completed! Run ID: {run.get('id', 'unknown')}")
        print(f"   Dataset ID: {run.get('defaultDatasetId', 'unknown')}")
        
        # Extract full post data with all available fields
        posts_data = []
        posts_text_only = []
        
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            # Extract all available fields from Apify response
            post_obj = {
                # Core identifiers
                "post_id": item.get("id"),
                "short_code": item.get("shortCode"),
                "type": item.get("type"),  # Image, Video, Sidecar
                
                # Content
                "caption": item.get("caption", "").strip(),
                "hashtags": item.get("hashtags", []),
                "mentions": item.get("mentions", []),
                
                # Timestamps and location
                "created_at": item.get("timestamp"),  # ISO8601
                "location_name": item.get("locationName"),
                
                # Engagement metrics
                "likes_count": item.get("likesCount", 0),
                "comments_count": item.get("commentsCount", 0),
                "video_view_count": item.get("videoViewCount", 0) if item.get("type") == "Video" else None,
                
                # Media URLs
                "post_url": item.get("url"),
                "display_url": item.get("displayUrl"),
                "video_url": item.get("videoUrl") if item.get("type") == "Video" else None,
                "images": item.get("images", []),
                
                # Additional metadata
                "owner_username": item.get("ownerUsername"),
                "owner_full_name": item.get("ownerFullName"),
                "is_sponsored": item.get("isSponsored", False),
                "comments_disabled": item.get("isCommentsDisabled", False),
                
                # Data availability flag
                "data_unavailable": False
            }
            
            posts_data.append(post_obj)
            
            # Keep text-only list for backward compatibility
            caption = post_obj["caption"]
            if caption:
                posts_text_only.append(caption)
        
        print(f"✅ Scraped {len(posts_data)} Instagram posts")
        if posts_data:
            print(f"   First post: ID={posts_data[0]['post_id']}, Type={posts_data[0]['type']}, Timestamp={posts_data[0]['created_at']}")
        
        # Check if account is accessible
        is_accessible, result = check_scraping_result(posts_text_only, "Instagram", username)
        if not is_accessible:
            return result
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Instagram scraping failed: {e}")
        print(f"Full traceback:\n{error_trace}")
        
        # Return structured error object (no fabricated data)
        return [{
            "post": f"⚠️ Unable to scrape Instagram account @{username}",
            "post_data": {
                "post_id": None,
                "caption": None,
                "created_at": None,
                "post_url": None,
                "data_unavailable": True,
                "error": str(e),
                "error_type": "scraping_failed"
            },
            "analysis": {
                "Instagram": {
                    "content_reinforcement": {"status": "error", "reason": f"Scraping failed: {str(e)}", "recommendation": None},
                    "content_suppression": {"status": "error", "reason": "No data available", "recommendation": None},
                    "content_flag": {"status": "error", "reason": "No data available", "recommendation": None},
                    "risk_score": -1
                }
            }
        }]

    # ==== PROFILE ASSESSMENT ====
    # Generate AI assessment of username/full name (once per account)
    profile_assessment = None
    if posts_data:
        try:
            from dashboard.intelligent_analyzer import analyze_profile_identity
            owner_username = posts_data[0].get('owner_username', username)
            owner_full_name = posts_data[0].get('owner_full_name', 'Not available')
            
            if owner_username and owner_full_name:
                print(f"👤 Generating profile assessment for @{owner_username}...")
                profile_assessment = analyze_profile_identity("Instagram", owner_username, owner_full_name)
        except Exception as e:
            print(f"⚠️ Profile assessment failed: {e}")
            profile_assessment = None
    
    # ==== INTELLIGENT AI ANALYSIS ====
    print(f"🤖 Starting intelligent analysis for {len(posts_data)} Instagram posts...")
    
    from dashboard.intelligent_analyzer import analyze_posts_batch
    
    try:
        results = analyze_posts_batch("Instagram", posts_data)
        
        # Add profile assessment to results (attach to first post)
        if profile_assessment and results:
            results[0]['profile_assessment'] = {
                'username': posts_data[0].get('owner_username', username),
                'full_name': posts_data[0].get('owner_full_name', 'Not available'),
                'assessment': profile_assessment
            }
        
        print(f"✅ Instagram intelligent analysis complete: {len(results)} posts analyzed")
        return results
    except Exception as e:
        import traceback
        print(f"❌ Intelligent analysis failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Fallback: Return structured error
        return [{
            "post": post_data.get("caption", "[No caption]"),
            "post_data": post_data,
            "analysis": {
                "Instagram": {
                    "content_reinforcement": {
                        "status": "Needs Improvement",
                        "reason": f"Analysis service error: {str(e)[:100]}",
                        "recommendation": "Try again later"
                    },
                    "content_suppression": {
                        "status": "Caution",
                        "reason": "Could not assess content risk",
                        "recommendation": "Manual review recommended"
                    },
                    "content_flag": {
                        "status": "Safe",
                        "reason": "No data available",
                        "recommendation": "Review manually"
                    },
                    "risk_score": -1
                }
            }
        } for post_data in posts_data]


# # ==== Example Run ====
# if __name__ == "__main__":
#     username = "asim._.19"   # <- change this to test
#     result = analyze_instagram_posts(username, limit=5)
#     print(json.dumps(result, indent=2))
