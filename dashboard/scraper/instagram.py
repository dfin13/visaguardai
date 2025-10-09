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

    # ==== Build Prompt with rich post data ====
    posts_text = "\n\n".join([
        f"Post {i+1} (ID: {p['post_id']}, Type: {p['type']}, {p['likes_count']} likes, {p['comments_count']} comments):\n{p['caption']}" 
        for i, p in enumerate(posts_data)
    ])
    prompt = f"""
You are an AI-based content recommendation engine.
Analyze the following Instagram posts and return ONLY valid JSON.

Schema per post:
[
  {{
    "Instagram": {{
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
  }}
]

Posts:
{posts_text}
"""

    # ==== AI CALL ====
    print(f"🤖 Sending {len(posts)} posts to OpenRouter AI for analysis...")
    try:
        completion = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that returns valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )

        ai_response = completion.choices[0].message.content
        print(f"✅ OpenRouter AI analysis completed")

        # Clean up ```json fences if present
        ai_response = (
            ai_response.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

        try:
            results = json.loads(ai_response)
        except Exception as je:
            print(f"JSON parsing failed: {je}\nRaw AI response: {ai_response}")
            results = [{"Instagram": {"error": "AI parsing failed", "raw": ai_response}} for _ in posts]
    except Exception as e:
        print(f"AI analysis failed: {e}")
        results = [{"Instagram": {"error": "AI call failed", "raw": str(e)}} for _ in posts]

    # ==== Final output with full post data ====
    final = []
    for i, post_data in enumerate(posts_data):
        analysis = results[i] if isinstance(results, list) and i < len(results) else results
        final.append({
            "post": post_data["caption"],  # Keep for backward compatibility
            "post_data": post_data,  # Full structured data
            "analysis": analysis
        })

    print(f"✅ Instagram analysis complete: {len(final)} posts analyzed")
    return final


# # ==== Example Run ====
# if __name__ == "__main__":
#     username = "asim._.19"   # <- change this to test
#     result = analyze_instagram_posts(username, limit=5)
#     print(json.dumps(result, indent=2))
