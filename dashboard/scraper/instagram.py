import json
import os
from apify_client import ApifyClient
from openai import OpenAI

from django.conf import settings
from dashboard.models import Config

# Get API keys from environment variables or Django settings
APIFY_API_TOKEN = os.getenv('APIFY_API_KEY') or getattr(settings, 'APIFY_API_KEY', None)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY') or getattr(settings, 'OPENROUTER_API_KEY', None)

# Log which Apify key source is being used
if os.getenv('APIFY_API_KEY'):
    print("🔑 [Instagram] Using Apify key from .env")
else:
    print("🔑 [Instagram] Using Apify key from Config table")

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

def analyze_instagram_posts(username, limit=10):
    """
    Scrape & analyze Instagram posts.
    Returns proper response for inaccessible accounts instead of fabricating content.
    Maximum limit: 10 posts to prevent excessive API usage.
    """
    from .account_checker import check_scraping_result, create_inaccessible_account_response, is_account_private_error

    # Cap limit at 10 posts maximum
    limit = min(limit, 10)
    
    print(f"\n🔍 INSTAGRAM ANALYSIS STARTING")
    print(f"   Username: {username}")
    print(f"   Limit: {limit} posts (capped at 10 max)")

    # ==== SCRAPE INSTAGRAM POSTS ====
    run_input = {
        "username": [username],
        "resultsLimit": limit,
        "scrapePostsUntilDate": None,
        "shouldDownloadMedia": False,
    }

    print(f"📡 Triggering Apify Instagram scraper for {username}...")
    try:
        # Add timeout to prevent hanging on problematic accounts
        import time
        start_time = time.time()
        
        # Start actor without waiting - check status immediately
        run = apify_client.actor("apify/instagram-post-scraper").start(run_input=run_input)
        run_id = run.get("id")
        
        print(f"📡 Actor started with run ID: {run_id}")
        
        # Poll for status - check every second for fast failure detection
        max_wait = 10  # Maximum 10 seconds to detect failures
        check_interval = 1  # Check every second
        
        for i in range(max_wait):
            time.sleep(check_interval)
            run_info = apify_client.run(run_id).get()
            run_status = run_info.get("status")
            
            print(f"⏱️  Check {i+1}/{max_wait}: Status = {run_status}")
            
            # FAST FAILURE: If actor failed, return immediately
            if run_status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                elapsed_time = time.time() - start_time
                print(f"❌ Instagram scraper FAILED for @{username} in {elapsed_time:.1f}s")
                print(f"   Status: {run_status} - Account may be private/suspended/nonexistent")
                return []  # Return empty immediately
            
            # If succeeded, break and continue to scraping
            if run_status == "SUCCEEDED":
                break
        
        # Wait for actor to finish (only if not failed)
        run = apify_client.run(run_id).wait_for_finish(timeout_secs=50)
        elapsed_time = time.time() - start_time
        
        if elapsed_time > 100:  # If it took too long, return timeout error
            print(f"⏰ Instagram actor took too long ({elapsed_time:.1f}s) for @{username}")
            return [{
                "post": f"⚠️ Unable to analyze Instagram account @{username}",
                "post_data": {
                    "post_id": None,
                    "caption": None,
                    "created_at": None,
                    "post_url": None,
                    "data_unavailable": True,
                    "error": "Scraping service timed out",
                    "error_type": "timeout"
                },
                "analysis": {
                    "Instagram": {
                        "content_reinforcement": {"status": "error", "reason": "Service timeout - please try again", "recommendation": "Account may be temporarily inaccessible"},
                        "content_suppression": {"status": "error", "reason": "No data available", "recommendation": None},
                        "content_flag": {"status": "error", "reason": "No data available", "recommendation": None},
                        "risk_score": -1
                    }
                }
            }]
        
        print(f"✅ Apify run completed in {elapsed_time:.1f}s! Run ID: {run.get('id', 'unknown')}")
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
        
        # Enforce 10 post limit (safety slice in case actor returns more)
        posts_data = posts_data[:10]
        posts_text_only = posts_text_only[:10]
        
        print(f"✅ Scraped {len(posts_data)} Instagram posts (capped at 10)")
        if posts_data:
            print(f"   First post: ID={posts_data[0]['post_id']}, Type={posts_data[0]['type']}, Timestamp={posts_data[0]['created_at']}")
        else:
            print(f"⚠️ No posts found for @{username} - account may be private, empty, or inaccessible")
            # Return proper response for empty account
            return [{
                "post": f"No posts found for Instagram account @{username}",
                "post_data": {
                    "post_id": None,
                    "caption": None,
                    "created_at": None,
                    "post_url": None,
                    "data_unavailable": True,
                    "error": "No posts found",
                    "error_type": "empty_account"
                },
                "analysis": {
                    "Instagram": {
                        "content_reinforcement": {"status": "info", "reason": "Account has no accessible posts", "recommendation": None},
                        "content_suppression": {"status": "info", "reason": "No posts to analyze", "recommendation": None},
                        "content_flag": {"status": "info", "reason": "No posts available", "recommendation": None},
                        "risk_score": 0
                    }
                }
            }]
        
        # Check if account is accessible
        is_accessible, result = check_scraping_result(posts_text_only, "Instagram", username)
        if not is_accessible:
            return result
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        # Check if it's a timeout or connection issue
        error_message = str(e).lower()
        if 'timeout' in error_message or 'timed out' in error_message:
            print(f"⏰ Instagram scraping timed out for @{username} (2min limit reached)")
            error_reason = "Scraping timed out - account may have limited accessibility"
        elif 'connection' in error_message or 'network' in error_message:
            print(f"🌐 Instagram scraping network error for @{username}")
            error_reason = "Network connection issue during scraping"
        else:
            print(f"❌ Instagram scraping failed for @{username}: {e}")
            error_reason = f"Scraping failed: {str(e)[:100]}"
        
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
                    "content_reinforcement": {"status": "error", "reason": error_reason, "recommendation": "Try again later or verify account is public"},
                    "content_suppression": {"status": "error", "reason": "No data available", "recommendation": None},
                    "content_flag": {"status": "error", "reason": "No data available", "recommendation": None},
                    "risk_score": -1
                }
            }
        }]

    # ==== INTELLIGENT AI ANALYSIS ====
    print(f"🤖 Starting intelligent analysis for {len(posts_data)} Instagram posts...")
    
    from dashboard.intelligent_analyzer import analyze_posts_batch
    
    try:
        results = analyze_posts_batch("Instagram", posts_data)
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

        print(f"Instagram scraping failed: {e}")
        # Check if error indicates private/inaccessible account
        if is_account_private_error(str(e)):
            return create_inaccessible_account_response("Instagram", username, "is private or inaccessible")
        else:
            # For other errors (API issues, etc.), return a generic inaccessible response
            return create_inaccessible_account_response("Instagram", username, "could not be accessed")

    # ==== Build Prompt ====
    posts_text = "\n\n".join([f"Post {i+1}: {text}" for i, text in enumerate(posts)])
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

    # ==== Final output ====
    final = []
    for i, post in enumerate(posts):
        analysis = results[i] if isinstance(results, list) and i < len(results) else results
        final.append({"post": post, "analysis": analysis})

    return final


# # ==== Example Run ====
# if __name__ == "__main__":
#     username = "asim._.19"   # <- change this to test
#     result = analyze_instagram_posts(username, limit=5)
#     print(json.dumps(result, indent=2))

