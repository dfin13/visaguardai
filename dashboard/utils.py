import requests
import json
import google.generativeai as genai

# ==== CONFIG ====
import os
from django.conf import settings

# Get API keys from environment variables or Django settings
APIFY_API_KEY = os.getenv('APIFY_API_KEY') or getattr(settings, 'APIFY_API_KEY', None)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
PLATFORM = "Instagram"
INSTAGRAM_USERNAME = "natgeo"  # Change to desired username

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


# ==== SCRAPE INSTAGRAM POST ====
def scrape_instagram_posts(username):
    """
    Runs the Apify Instagram post scraper and returns the caption text of the latest post.
    """
    run_url = (
        f"https://api.apify.com/v2/acts/apify~instagram-post-scraper/"
        f"run-sync-get-dataset-items?token={APIFY_API_KEY}"
    )

    payload = {
        "username": [username],
        "resultsType": "posts",
        "resultsLimit": 1
    }

    response = requests.post(run_url, json=payload)
    response.raise_for_status()
    data = response.json()

    if data:
        first_post = data[0]
        return first_post.get("caption", "")
    return ""


# ==== ANALYZE WITH GEMINI ====
def analyze_with_gemini(platform, text_content):
    """
    Sends the Instagram post text to Gemini for analysis according to your rules.
    """
    prompt = f"""
You are an AI-based content recommendation engine for paid users.
Analyze the following {platform} post and return a JSON object with recommendations.

Rules:
1. Content Reinforcement: If safe, positive, low-risk → encourage similar content.
2. Content Suppression: If political → suggest avoiding such topics.
3. Content Flag: If culturally sensitive or controversial → recommend removing it.
4. Output must be valid JSON ONLY with the following structure:

{{
  "{platform}": {{
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

Post to analyze:
{text_content}
"""

    model = genai.GenerativeModel("gemini-2.0-flash")  # latest supported in this SDK
    response = model.generate_content(prompt)

    try:
        return json.loads(response.text)  # Parse into JSON
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini did not return valid JSON:\n{response.text}") from e


# ==== MAIN FUNCTION ====
def analyze_instagram_post(username):
    print(f"Scraping latest post from: {username}")
    post_text = scrape_instagram_posts(username)

    if not post_text:
        print("No post text found.")
        return None

    print("Analyzing with Gemini...")
    result = analyze_with_gemini(PLATFORM, post_text)
    return result


def analyze_all_platforms(user_id, instagram_username, linkedin_username, twitter_username, facebook_username=None):
    """
    Analyze all platforms using intelligent context-aware AI analysis.
    Returns real analysis results or error states (never dummy/fake data).
    Each platform uses the intelligent_analyzer for unique, content-based assessments.
    """
    from .scraper.instagram import analyze_instagram_posts
    from .scraper.linkedin import analyze_linkedin_profile
    from .scraper.t import analyze_twitter_profile
    from .scraper.facebook import analyze_facebook_posts
    from .intelligent_analyzer import generate_profile_assessment
    from django.core.cache import cache
    
    results = {}
    # Instagram - Process with detailed progress stages
    import time
    try:
        if instagram_username:
            # Set detailed progress stages for Instagram analysis with delays
            cache.set(f'analysis_stage_{user_id}', 'instagram_processing', timeout=60*60)
            cache.set(f'stage_progress_{user_id}', 20, timeout=60*60)
            time.sleep(2)  # 2 second delay to show progress
            
            # Blueprint scanning stage
            cache.set(f'analysis_stage_{user_id}', 'blueprint_scanning', timeout=60*60)
            cache.set(f'stage_progress_{user_id}', 55, timeout=60*60)
            time.sleep(3)  # 3 second delay to show progress
            
            # Post scanning stage  
            cache.set(f'analysis_stage_{user_id}', 'post_scanning', timeout=60*60)
            cache.set(f'stage_progress_{user_id}', 70, timeout=60*60)
            time.sleep(3)  # 3 second delay to show progress
            
            # Comment scanning stage
            cache.set(f'analysis_stage_{user_id}', 'comment_scanning', timeout=60*60)
            cache.set(f'stage_progress_{user_id}', 85, timeout=60*60)
            time.sleep(2)  # 2 second delay to show progress
            
            results['instagram'] = analyze_instagram_posts(instagram_username)
            
            # Extract full name from scraped Instagram data (first post)
            scraped_full_name = "User"
            if results['instagram'] and len(results['instagram']) > 0:
                first_post = results['instagram'][0]
                if 'owner_full_name' in first_post:
                    scraped_full_name = first_post['owner_full_name'] or "User"
            
            # Generate profile assessment (username only)
            profile_assessment = generate_profile_assessment("Instagram", instagram_username)
            results['instagram_profile'] = {
                'username': instagram_username,
                'full_name': scraped_full_name,
                'assessment': profile_assessment
            }
            print(f"DEBUG: Instagram analysis result: {results['instagram']}")
            print(f"DEBUG: Instagram profile: @{instagram_username}, Name: {scraped_full_name}")
        else:
            results['instagram'] = []
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Instagram analysis FAILED: {e}")
        print(f"Full error trace:\n{error_details}")
        # Return error state instead of fake "safe" data
        results['instagram'] = [{
            "error": True,
            "message": f"Instagram analysis failed: {str(e)}",
            "post": f"⚠️ Unable to analyze Instagram account @{instagram_username}",
            "analysis": {
                "Instagram": {
                    "content_reinforcement": {"status": "error", "recommendation": "Please try again", "reason": f"API error: {str(e)}"},
                    "content_suppression": {"status": "error", "recommendation": None, "reason": "Analysis unavailable"},
                    "content_flag": {"status": "error", "recommendation": None, "reason": "Analysis unavailable"},
                    "risk_score": -1
                }
            }
        }]
        print(f"DEBUG: Instagram error state set (not fake safe data)")
    cache.set(f'instagram_analysis_{user_id}', results['instagram'], 3600)
    if 'instagram_profile' in results:
        cache.set(f'instagram_profile_{user_id}', results['instagram_profile'], 3600)

    # LinkedIn - Skip since it's already processed in the main thread
    # LinkedIn analysis is handled directly in start_analysis() to avoid duplication
    results['linkedin'] = []  # Placeholder, actual results are cached from main thread
    print(f"DEBUG: LinkedIn data placeholder set (actual data is cached in main thread): {results['linkedin']}")

    # Twitter
    try:
        if twitter_username:
            results['twitter'] = analyze_twitter_profile(twitter_username)
            
            # Check if result is an error string (account doesn't exist)
            if isinstance(results['twitter'], str):
                print(f"⚠️  Twitter scraper returned error: {results['twitter'][:100]}")
                # Convert error string to proper error state
                results['twitter'] = [{
                    "tweet": f"⚠️ Unable to analyze Twitter account @{twitter_username}",
                    "post_data": {
                        "caption": None,
                        "data_unavailable": True,
                        "error": results['twitter'],
                        "error_type": "account_not_found"
                    },
                    "analysis": {
                        "Twitter": {
                            "content_reinforcement": {
                                "status": "error",
                                "reason": "Account not found or has no tweets",
                                "recommendation": "Verify the username is correct and the account is public"
                            },
                            "content_suppression": {"status": "error", "reason": "No data available", "recommendation": None},
                            "content_flag": {"status": "error", "reason": "Unable to assess", "recommendation": None},
                            "risk_score": -1
                        }
                    }
                }]
            
            # Extract full name from scraped Twitter data (first post)
            scraped_full_name = "User"
            if isinstance(results['twitter'], list) and len(results['twitter']) > 0:
                first_post = results['twitter'][0]
                # Try various field names for Twitter profile name
                scraped_full_name = (
                    first_post.get('author_name') or 
                    first_post.get('user_name') or 
                    first_post.get('profile_name') or 
                    "User"
                )
            
            # Generate profile assessment (username only)
            profile_assessment = generate_profile_assessment("X", twitter_username)
            results['twitter_profile'] = {
                'username': twitter_username,
                'full_name': scraped_full_name,
                'assessment': profile_assessment
            }
            print(f"DEBUG: Twitter analysis result type: {type(results['twitter'])}, length: {len(results['twitter']) if isinstance(results['twitter'], list) else 'N/A'}")
            print(f"DEBUG: Twitter profile: @{twitter_username}, Name: {scraped_full_name}")
        else:
            results['twitter'] = []
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Twitter analysis failed: {e}")
        print(f"Full traceback:\n{error_trace}")
        # Return proper error state (no fake data)
        results['twitter'] = [{
            "tweet": f"⚠️ Unable to analyze Twitter account @{twitter_username}",
            "post_data": {
                "caption": None,
                "data_unavailable": True,
                "error": str(e),
                "error_type": "analysis_failed"
            },
            "Twitter": {
                "content_reinforcement": {
                    "status": "error",
                    "reason": f"Twitter analysis unavailable: {str(e)[:100]}",
                    "recommendation": "Try again later or check if account is accessible"
                },
                "content_suppression": {
                    "status": "error",
                    "reason": "No data available for assessment",
                    "recommendation": None
                },
                "content_flag": {
                    "status": "error",
                    "reason": "Unable to flag content without data",
                    "recommendation": None
                },
                "risk_score": -1
            }
        }]
        print(f"DEBUG: Twitter error state set (no fake data)")
    cache.set(f'twitter_analysis_{user_id}', results['twitter'], 3600)
    if 'twitter_profile' in results:
        cache.set(f'twitter_profile_{user_id}', results['twitter_profile'], 3600)

    # Facebook
    try:
        if facebook_username:
            results['facebook'] = analyze_facebook_posts(facebook_username, limit=5, user_id=user_id)
            
            # Extract full name from scraped Facebook data
            scraped_full_name = "User"
            if results['facebook'] and isinstance(results['facebook'], dict) and 'facebook' in results['facebook']:
                fb_posts = results['facebook']['facebook']
                if fb_posts and len(fb_posts) > 0:
                    first_post = fb_posts[0]
                    # Try various field names for Facebook profile name
                    scraped_full_name = (
                        first_post.get('author_name') or 
                        first_post.get('user_name') or 
                        first_post.get('profile_name') or 
                        first_post.get('owner_full_name') or
                        "User"
                    )
            
            # Generate profile assessment (username only)
            profile_assessment = generate_profile_assessment("Facebook", facebook_username)
            results['facebook_profile'] = {
                'username': facebook_username,
                'full_name': scraped_full_name,
                'assessment': profile_assessment
            }
            print(f"DEBUG: Facebook analysis result: {results['facebook']}")
            print(f"DEBUG: Facebook profile: {facebook_username}, Name: {scraped_full_name}")
            print(f"DEBUG: Facebook data before caching: {results['facebook']}")
        else:
            results['facebook'] = []
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Facebook analysis failed: {e}")
        print(f"Full traceback:\n{error_trace}")
        # Return proper error state (no fake data)
        results['facebook'] = [{
            "post": f"⚠️ Unable to analyze Facebook account {facebook_username}",
            "post_data": {
                "caption": None,
                "data_unavailable": True,
                "error": str(e),
                "error_type": "analysis_failed"
            },
            "Facebook": {
                "content_reinforcement": {
                    "status": "error",
                    "reason": f"Facebook analysis unavailable: {str(e)[:100]}",
                    "recommendation": "Try again later or check if account is accessible"
                },
                "content_suppression": {
                    "status": "error",
                    "reason": "No data available for assessment",
                    "recommendation": None
                },
                "content_flag": {
                    "status": "error",
                    "reason": "Unable to flag content without data",
                    "recommendation": None
                },
                "risk_score": -1
            }
        }]
        print(f"DEBUG: Facebook error state set (no fake data)")
        print(f"DEBUG: Facebook data before caching: {results['facebook']}")
    cache.set(f'facebook_analysis_{user_id}', results['facebook'], 3600)
    if 'facebook_profile' in results:
        cache.set(f'facebook_profile_{user_id}', results['facebook_profile'], 3600)

    return results


# ==== RUN SCRIPT ====
if __name__ == "__main__":
    analysis = analyze_instagram_post(INSTAGRAM_USERNAME)
    if analysis:
        print(json.dumps(analysis, indent=2))
