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

# Log which Apify key source is being used
if os.getenv('APIFY_API_KEY'):
    print("🔑 [Facebook] Using Apify key from .env")
else:
    print("🔑 [Facebook] Using Apify key from Config table")

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
    Maximum limit: 10 posts to prevent excessive API usage.
    """
    from django.core.cache import cache
    
    # Cap limit at 10 posts maximum
    limit = min(limit, 10)

    # Ensure we always have a valid Facebook URL
    if username_or_url.startswith("http"):
        fb_url = username_or_url
    else:
        fb_url = f"https://www.facebook.com/{username_or_url}"

    # ==== SCRAPE FACEBOOK POSTS ====
    run_input = {
        "startUrls": [{"url": fb_url}],
        "resultsLimit": limit,  # Hard limit: max 10 posts
        "scrapePostsUntilDate": None,
        "includeReactions": True,   # Enable to get engagement data (likes count)
        "includePostUrls": True     # Enable to get post URLs
        # Comments not included - not used in analysis
    }

    print(f"Scraping up to {limit} Facebook posts for {fb_url}...")
    print(f"   Actor: apify/facebook-posts-scraper (approved actor)")
    print(f"   Limit: {limit} posts (max 10)")
    
    try:
        from .account_checker import create_inaccessible_account_response
        
        # Use Facebook Posts Scraper with strict timeout
        import time
        start_time = time.time()
        
        run = apify_client.actor("apify/facebook-posts-scraper").call(
            run_input=run_input,
            timeout_secs=60,   # Reduced to 60 seconds - faster failure detection
            wait_secs=5        # Shorter wait for initial response
        )
        
        elapsed_time = time.time() - start_time
        
        # CHECK RUN STATUS IMMEDIATELY - Detect failures early
        run_status = run.get("status")
        print(f"📊 Apify run status: {run_status} (took {elapsed_time:.1f}s)")
        
        if run_status in ["FAILED", "ABORTED", "TIMED-OUT"]:
            print(f"❌ Facebook scraper FAILED for {username_or_url} - Status: {run_status}")
            print(f"   Account may be private, suspended, or doesn't exist")
            return []  # Return empty list - will be caught by validation
        
        if elapsed_time > 100:  # If too slow, return timeout error
            print(f"⏰ Facebook actor took too long ({elapsed_time:.1f}s)")
            return [{
                "post": f"⚠️ Unable to analyze Facebook account {username_or_url}",
                "post_data": {
                    "caption": None,
                    "created_at": None,
                    "post_url": None,
                    "data_unavailable": True,
                    "error": "Scraping service timed out",
                    "error_type": "timeout"
                },
                "analysis": {
                    "Facebook": {
                        "content_reinforcement": {"status": "error", "reason": "Service timeout - please try again", "recommendation": "Account may be temporarily inaccessible"},
                        "content_suppression": {"status": "error", "reason": "No data available", "recommendation": None},
                        "content_flag": {"status": "error", "reason": "Unable to assess", "recommendation": None},
                        "risk_score": -1
                    }
                }
            }]

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
                
                # Extract author/profile name information
                # DEBUG: Print what fields are available in the Apify response
                if len(posts) == 0:  # Only print for first post to avoid spam
                    print(f"🔍 [FACEBOOK APIFY DEBUG] Item keys: {list(item.keys())}")
                    if item.get("author"):
                        print(f"🔍 [FACEBOOK APIFY DEBUG] Author object: {item.get('author')}")
                
                # Author name extraction removed - no longer needed
                
                posts.append({
                    'text': post_text,
                    'post_url': post_url,
                    'timestamp': timestamp,
                    'likes_count': likes_count,
                    'comments_count': comments_count,
                    'shares_count': shares_count,
                    'author_name': author_name,
                })

        # Enforce 10 post limit (safety slice in case actor returns more)
        posts = posts[:10]
        print(f"✅ Final count: {len(posts)} Facebook posts (capped at 10)")

        # Check if account is accessible (pass text content for check)
        from .account_checker import check_scraping_result
        post_texts = [post['text'] for post in posts]
        is_accessible, result = check_scraping_result(post_texts, "Facebook", username_or_url)
        if not is_accessible:
            return result
    except Exception as e:
        print(f"Scraping failed: {e}")
        error_str = str(e).lower()
        
        # Alert on API issues
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
        
        # Return list directly, not nested in dict
        return results
        
    except Exception as e:
        import traceback
        print(f"❌ Facebook intelligent analysis failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Return error in consistent format (as list)
        return [{
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
        }]


# # Example usage:
# if __name__ == "__main__":
#     # You can pass either "nytimes" or "https://www.facebook.com/nytimes"
#     username_or_url = "nytimes"
#     analysis = analyze_facebook_posts(username_or_url, limit=5)
#     print(json.dumps(analysis, indent=2, ensure_ascii=False))

    prompt = f"""
You are an AI-based content recommendation engine for paid users.
Analyze the following Facebook posts and return a JSON array where each element corresponds to one post.

Rules:
1. Content Reinforcement: If safe, positive, low-risk → encourage similar content.
2. Content Suppression: If political → suggest avoiding such topics.
3. Content Flag: If culturally sensitive or controversial → recommend removing it.
4. Output must be valid JSON ONLY with the following structure for EACH post:

[
  {{
    "Facebook": {{
      "content_reinforcement": {{
        "status": "safe|caution|warning",
        "recommendation": "string or null",
        "reason": "string"
      }},
      "content_suppression": {{
        "status": "safe|caution|warning",
        "recommendation": "string or null",
        "reason": "string"
      }},
      "content_flag": {{
        "status": "safe|caution|warning",
        "recommendation": "string or null",
        "reason": "string"
      }},
      "risk_score": 0
    }}
  }},
  ...
]

Posts to analyze:
{posts_text}
"""

    # ==== One AI Call for all posts ====
    completion = client_ai.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "Facebook Analyzer",
        },
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant that returns valid JSON only."},
            {"role": "user", "content": prompt}
        ]
    )

    ai_response = completion.choices[0].message.content

    # Handle OpenRouter 429 rate limit gracefully
    if 'rate-limited' in ai_response or '429' in ai_response or 'temporarily rate-limited' in ai_response:
        return {"error": "Facebook analysis is temporarily unavailable due to AI rate-limiting. Please try again in a few minutes or add your own OpenRouter API key for higher limits."}

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
