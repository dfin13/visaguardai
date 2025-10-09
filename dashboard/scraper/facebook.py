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
        "includeReactions": False,
        "includeComments": False,
        "includePostUrls": False
    }

    print(f"Scraping up to {limit} Facebook posts for {fb_url}...")
    
    if user_id:
        cache.set(f'analysis_stage_{user_id}', 'post_scanning', timeout=60*60)
        cache.set(f'stage_progress_{user_id}', 10, timeout=60*60)
    
    try:
        run = apify_client.actor("apify/facebook-posts-scraper").call(run_input=run_input)

        # Collect all post texts
        posts = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            post_text = item.get("text", "").strip()
            if post_text:
                posts.append(post_text)

        # Check if account is accessible
        from .account_checker import check_scraping_result
        is_accessible, result = check_scraping_result(posts, "Facebook", username_or_url)
        if not is_accessible:
            return result
    except Exception as e:
        print(f"Scraping failed: {e}")
        error_str = str(e).lower()
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
    
    # Convert posts to standard format
    posts_data = []
    for post_text in posts:
        posts_data.append({
            'caption': post_text,
            'text': post_text,
            'post_text': post_text,
            'type': 'post',
            'hashtags': [],
            'mentions': [],
        })
    
    try:
        results = analyze_posts_batch("Facebook", posts_data)
        print(f"✅ Facebook intelligent analysis complete: {len(results)} posts")
        ai_response = json.dumps(results, ensure_ascii=False)
    except Exception as e:
        import traceback
        print(f"❌ Facebook intelligent analysis failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Handle error as rate limit for consistency
        return {"error": f"Facebook analysis temporarily unavailable: {str(e)[:100]}"}

    try:
        results = json.loads(ai_response)
    except json.JSONDecodeError:
        results = {"error": "Invalid JSON from AI", "raw_output": ai_response}

    return [
        {"post": posts[i], "analysis": results[i] if isinstance(results, list) and i < len(results) else results}
        for i in range(len(posts))
    ]


# # Example usage:
# if __name__ == "__main__":
#     # You can pass either "nytimes" or "https://www.facebook.com/nytimes"
#     username_or_url = "nytimes"
#     analysis = analyze_facebook_posts(username_or_url, limit=5)
#     print(json.dumps(analysis, indent=2, ensure_ascii=False))
