import json
import re
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
    print("🔑 [LinkedIn] Using Apify key from .env")
else:
    print("🔑 [LinkedIn] Using Apify key from Config table")

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

# === CLIENTS ===
apify_client = ApifyClient(APIFY_API_TOKEN)
openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# --- Helper: Alert ---
def send_api_expiry_alert(subject, body, to_email):
    print(f"[ALERT] {subject}\n{body}\n(To: {to_email})")

# --- Helper: Extract JSON ---
def extract_json_from_ai_response(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r'```(?:json)?\n([\s\S]+?)\n```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        return {"error": "Invalid JSON", "raw_output": text}

# REMOVED: generate_fallback_linkedin_posts function
# This function was creating fake LinkedIn posts when scraping failed.
# Instead, we now return proper "inaccessible account" responses.

# --- Scraper ---
def get_linkedin_posts(username="syedawaisalishah", page_number=1, limit=10):
    """
    Scrape LinkedIn posts with optimized settings.
    Fetches up to 10 most recent posts for the specific username.
    LinkedIn scraping is inherently slower due to anti-scraping measures.
    Maximum limit: 10 posts to prevent excessive API usage.
    """
    from .account_checker import create_inaccessible_account_response, is_account_private_error, check_scraping_result
    
    # Cap limit at 10 posts maximum
    limit = min(limit, 10)
    
    # Configure scraper to fetch only latest posts for specific user profile
    run_input = {
        "username": username,
        "page_number": page_number,
        "limit": limit,  # Hard limit: max 10 posts
        "profileUrl": f"https://www.linkedin.com/in/{username}/"  # Target specific profile
    }
    
    try:
        print(f"⏱️  Starting LinkedIn scraping for: {username} (limit: {limit} posts, capped at 10 max)")
        print(f"   Profile URL: https://www.linkedin.com/in/{username}/")
        print(f"   Mode: Latest posts only (no feed scanning)")
        print(f"   Actor: apimaestro/linkedin-profile-posts (approved actor)")
        
        # Use approved LinkedIn actor with strict timeout
        import time
        start_time = time.time()
        
        run = apify_client.actor("apimaestro/linkedin-profile-posts").call(
            run_input=run_input,
            timeout_secs=120,  # Allow up to 2 minutes for scraping
            wait_secs=10       # Wait a bit longer for initial response
        )
        
        elapsed_time = time.time() - start_time
        if elapsed_time > 100:  # If too slow, return timeout error
            print(f"⏰ LinkedIn actor took too long ({elapsed_time:.1f}s)")
            return None, [{
                "post": f"⚠️ Unable to analyze LinkedIn account @{username}",
                "post_data": {
                    "caption": None,
                    "created_at": None,
                    "post_url": None,
                    "data_unavailable": True,
                    "error": "Scraping service timed out",
                    "error_type": "timeout"
                },
                "analysis": {
                    "LinkedIn": {
                        "content_reinforcement": {"status": "error", "reason": "Service timeout - please try again", "recommendation": "Account may be temporarily inaccessible"},
                        "content_suppression": {"status": "error", "reason": "No data available", "recommendation": None},
                        "content_flag": {"status": "error", "reason": "Unable to assess", "recommendation": None},
                        "risk_score": -1
                    }
                }
            }]
        
        if not run or "defaultDatasetId" not in run:
            raise Exception("No dataset from actor")
    except Exception as e:
        print(f"Apify error: {e}")
        send_api_expiry_alert("VisaGuardAI: Apify API Expiry/Failure Alert", f"LinkedIn Apify API error: {e}", "syedawaisalishah46@gmail.com")
        
        # Return proper inaccessible account response instead of fabricating posts
        if is_account_private_error(str(e)):
            return None, create_inaccessible_account_response("LinkedIn", username, "is private or inaccessible")
        else:
            return None, create_inaccessible_account_response("LinkedIn", username, "could not be accessed")

    posts = []
    post_count = 0
    
    # Iterate through dataset and collect post text AND URLs
    for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
        # Extract the caption/text content
        post_text = (
            item.get("text") or item.get("post_text") or item.get("content") or
            item.get("description") or item.get("post_content")
        )
        
        # Extract the post URL
        post_url = (
            item.get("url") or item.get("post_url") or item.get("postUrl") or 
            item.get("link") or item.get("permalink") or None
        )
        
        # Extract author/profile name information
        # DEBUG: Print what fields are available in the Apify response
        if post_count == 0:  # Only print for first post to avoid spam
            print(f"🔍 [LINKEDIN APIFY DEBUG] Item keys: {list(item.keys())}")
            if item.get("author"):
                print(f"🔍 [LINKEDIN APIFY DEBUG] Author object: {item.get('author')}")
        
        if post_text:
            posts.append({
                "post_text": post_text,
                "post_url": post_url,
                "timestamp": item.get("timestamp") or item.get("created_at") or item.get("date"),
                "reactions": item.get("reactions") or item.get("likes") or 0,
                "comments": item.get("comments") or item.get("commentsCount") or 0,
            })
            post_count += 1
            print(f"   ✓ Collected post {post_count}/{limit} (URL: {'✓' if post_url else '✗'})")
        
        # Hard stop at limit to prevent excessive scanning
        if post_count >= limit:
            print(f"   ✅ Reached limit of {limit} posts - stopping iteration")
            break
    
    print(f"   📊 Total posts collected: {len(posts)}")
    
    # Enforce 10 post limit (safety slice in case actor returns more)
    posts = posts[:10]
    print(f"   ✅ Final count: {len(posts)} posts (capped at 10)")
    
    # Check if account is accessible
    post_texts = [post["post_text"] for post in posts]
    is_accessible, result = check_scraping_result(post_texts, "LinkedIn", username)
    if not is_accessible:
        return None, result
    
    return posts, None

# --- AI Analyzer (Intelligent Context-Aware) ---
def analyze_posts_with_ai(posts):
    """
    Analyze LinkedIn posts using intelligent, context-aware AI.
    
    Args:
        posts: list - List of post dicts with 'post_text' field
    
    Returns:
        list - Analyzed posts with full post_data and analysis
    """
    from dashboard.intelligent_analyzer import analyze_posts_batch
    
    # Convert posts to standard format for intelligent analyzer
    posts_data = []
    for post in posts:
        posts_data.append({
            'caption': post.get('post_text', ''),
            'text': post.get('post_text', ''),
            'post_text': post.get('post_text', ''),
            'post_url': post.get('post_url'),  # Add post URL for template display
            'created_at': post.get('timestamp'),
            'timestamp': post.get('timestamp'),  # Add timestamp field for consistency with other platforms
            'likes_count': post.get('reactions', 0),
            'comments_count': post.get('comments', 0),
            'type': 'text',
            'hashtags': [],
            'mentions': [],
        })
    
    try:
        print(f"🤖 Starting intelligent LinkedIn analysis for {len(posts_data)} posts...")
        results = analyze_posts_batch("LinkedIn", posts_data)
        print(f"✅ LinkedIn intelligent analysis complete")
        return results
    except Exception as e:
        import traceback
        print(f"❌ LinkedIn intelligent analysis failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        send_api_expiry_alert("VisaGuardAI: AI Analysis Alert", f"LinkedIn intelligent analysis error: {e}", "syedawaisalishah46@gmail.com")
        
        # Fallback to error state
        return [{
            "post": post['post_text'],
            "post_data": {
                'caption': post['post_text'],
                'data_unavailable': True,
            },
            "analysis": {
                "LinkedIn": {
                    "content_reinforcement": {
                        "status": "Needs Improvement",
                        "reason": f"Analysis error: {str(e)[:80]}",
                        "recommendation": "Try again later"
                    },
                    "content_suppression": {
                        "status": "Caution",
                        "reason": "Could not assess content",
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
        } for post in posts]

# --- Main workflow ---
def analyze_linkedin_profile(username, limit=3):
    """
    Analyze LinkedIn profile with optimized post limit.
    Default reduced to 3 posts (from 5) for faster processing.
    """
    posts, inaccessible_response = get_linkedin_posts(username, limit=limit)
    
    # If account is inaccessible, return the proper response
    if inaccessible_response:
        return inaccessible_response
    
    if not posts:
        from .account_checker import create_inaccessible_account_response
        return create_inaccessible_account_response("LinkedIn", username, "has no accessible content")                                                                              
    
    analysis = analyze_posts_with_ai(posts)
    return analysis  # Return list directly, not nested in dict

# # --- Run test ---
# if __name__ == "__main__":
#     print("Testing LinkedIn scraper + analyzer...")
#     result = analyze_linkedin_profile("syedasimbacha", limit=5)
#     print(json.dumps(result, indent=2))
#     print("Test completed!")
