import json
import os
from apify_client import ApifyClient
from openai import OpenAI
from django.conf import settings
from dashboard.models import Config
from dashboard.utils_email import send_api_expiry_alert

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

# ==== Initialize OpenRouter Client ====
client_ai = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ==== Initialize Apify client ====
apify_client = ApifyClient(APIFY_API_TOKEN)


def analyze_facebook_posts(username_or_url, limit=10, user_id=None):
    """
    Scrapes Facebook posts for a given username/page ID or full URL and analyzes them in ONE AI call.
    """
    from django.core.cache import cache
    
    # Set progress stages
    if user_id:
        cache.set(f'analysis_stage_{user_id}', 'facebook_analysis', timeout=60*60)
        cache.set(f'stage_progress_{user_id}', 0, timeout=60*60)

    # Ensure we always have a valid Facebook URL
    if username_or_url.startswith("http"):
        fb_url = username_or_url
    else:
        fb_url = f"https://www.facebook.com/{username_or_url}"

    if user_id:
        cache.set(f'analysis_stage_{user_id}', 'blueprint_scanning', timeout=60*60)
        cache.set(f'stage_progress_{user_id}', 5, timeout=60*60)

    # ==== SCRAPE FACEBOOK POSTS ====
    run_input = {
        "startUrls": [{"url": fb_url}],
        "resultsLimit": limit,
        "scrapePostsUntilDate": None,
        "includeReactions": True,   # Enable to get engagement data
        "includeComments": True,    # Enable to get comment counts
        "includePostUrls": True     # Enable to get post URLs
    }

    print(f"Scraping up to {limit} Facebook posts for {fb_url}...")
    
    if user_id:
        cache.set(f'analysis_stage_{user_id}', 'post_scanning', timeout=60*60)
        cache.set(f'stage_progress_{user_id}', 10, timeout=60*60)
    
    try:
        from .account_checker import create_inaccessible_account_response
        
        run = apify_client.actor("apify/facebook-posts-scraper").call(run_input=run_input)

        # Collect all posts with full metadata
        posts = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            post_text = item.get("text", "").strip()
            if post_text:
                # Extract all available fields for analysis
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
                
                posts.append({
                    'text': post_text,
                    'post_url': post_url,
                    'timestamp': timestamp,
                    'likes_count': likes_count,
                    'comments_count': comments_count,
                    'shares_count': shares_count,
                })

        # Check if account is accessible (pass text content for check)
        from .account_checker import check_scraping_result
        post_texts = [post['text'] for post in posts]
        is_accessible, result = check_scraping_result(post_texts, "Facebook", username_or_url)
        if not is_accessible:
            return result
    except Exception as e:
        print(f"Scraping failed: {e}")
        error_str = str(e).lower()
        
        # Check for Apify plan limitations
        if "cannot run this public actor" in error_str or "current plan does not support" in error_str:
            print("❌ Facebook scraper unavailable: Apify plan doesn't support public actors")
            return create_inaccessible_account_response(
                "Facebook", 
                username_or_url, 
                "scraper is unavailable due to API plan limitations. Please upgrade Apify subscription to enable Facebook analysis."
            )
        
        if any(word in error_str for word in ["expired", "invalid", "authentication", "quota", "rate-limit"]):
            send_api_expiry_alert(
                subject="VisaGuardAI: Apify API Expiry/Failure Alert",
                body=f"Apify API error: {e}",
                to_email="syedawaisalishah46@gmail.com"
            )
        
        # Return proper inaccessible account response instead of fabricating posts
        from .account_checker import create_inaccessible_account_response, is_account_private_error
        if is_account_private_error(str(e)):
            return create_inaccessible_account_response("Facebook", username_or_url, "is private or inaccessible")
        else:
            return create_inaccessible_account_response("Facebook", username_or_url, "could not be accessed")

    if user_id:
        cache.set(f'analysis_stage_{user_id}', 'comment_scanning', timeout=60*60)
        cache.set(f'stage_progress_{user_id}', 15, timeout=60*60)

    # ==== Create single prompt ====
    print(f"🤖 Starting intelligent analysis for {len(posts)} Facebook posts...")
    
    # === INTELLIGENT AI ANALYSIS ===
    from dashboard.intelligent_analyzer import analyze_posts_batch
    
    # Convert posts to standard format with all metadata
    posts_data = []
    for post in posts:
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
    
    try:
        results = analyze_posts_batch("Facebook", posts_data)
        print(f"✅ Facebook intelligent analysis complete: {len(results)} posts")
        
        # Return in same format as LinkedIn/Instagram: {"facebook": [...]}
        return {"facebook": results}
        
    except Exception as e:
        import traceback
        print(f"❌ Facebook intelligent analysis failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Return error in consistent format
        return {"facebook": [{
            "post": "Facebook analysis error",
            "post_data": {"data_unavailable": True, "error": str(e)},
            "analysis": {
                "Facebook": {
                    "content_reinforcement": {
                        "status": "error",
                        "reason": f"Analysis unavailable: {str(e)[:80]}",
                        "recommendation": "Try again later"
                    },
                    "content_suppression": {
                        "status": "error",
                        "reason": "Unable to assess content",
                        "recommendation": None
                    },
                    "content_flag": {
                        "status": "error",
                        "reason": "No data available",
                        "recommendation": None
                    },
                    "risk_score": -1
                }
            }
        }]}


# # Example usage:
# if __name__ == "__main__":
#     # You can pass either "nytimes" or "https://www.facebook.com/nytimes"
#     username_or_url = "nytimes"
#     analysis = analyze_facebook_posts(username_or_url, limit=5)
#     print(json.dumps(analysis, indent=2, ensure_ascii=False))
