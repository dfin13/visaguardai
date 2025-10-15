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
    Analyze all platforms using intelligent context-aware AI analysis with parallel execution.
    Returns real analysis results or error states (never dummy/fake data).
    Each platform uses the intelligent_analyzer for unique, content-based assessments.
    Platforms are analyzed concurrently for speed optimization.
    """
    from .scraper.instagram import analyze_instagram_posts
    from .scraper.linkedin import analyze_linkedin_profile
    from .scraper.t import analyze_twitter_profile
    from .scraper.facebook import analyze_facebook_posts
    from .intelligent_analyzer import generate_profile_assessment
    from django.core.cache import cache
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time
    
    results = {}
    
    # Define platform analysis functions for parallel execution
    def analyze_instagram():
        if instagram_username:
            cache.set(f'analysis_stage_{user_id}', 'analyzing_instagram', timeout=60*60)
            cache.set(f'stage_progress_{user_id}', 25, timeout=60*60)
            return ('instagram', analyze_instagram_posts(instagram_username))
        return ('instagram', [])
    
    def analyze_linkedin():
        if linkedin_username:
            cache.set(f'analysis_stage_{user_id}', 'analyzing_linkedin', timeout=60*60)
            cache.set(f'stage_progress_{user_id}', 50, timeout=60*60)
            return ('linkedin', analyze_linkedin_profile(linkedin_username))
        return ('linkedin', [])
    
    def analyze_twitter():
        if twitter_username:
            cache.set(f'analysis_stage_{user_id}', 'analyzing_twitter', timeout=60*60)
            cache.set(f'stage_progress_{user_id}', 75, timeout=60*60)
            return ('twitter', analyze_twitter_profile(twitter_username))
        return ('twitter', [])
    
    def analyze_facebook():
        if facebook_username:
            cache.set(f'analysis_stage_{user_id}', 'analyzing_facebook', timeout=60*60)
            cache.set(f'stage_progress_{user_id}', 90, timeout=60*60)
            return ('facebook', analyze_facebook_posts(facebook_username, limit=10, user_id=user_id))
        return ('facebook', [])
    
    # Execute all platform analyses in parallel
    print(f"🚀 Starting parallel analysis for user {user_id}")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all platform tasks
        futures = []
        if instagram_username:
            futures.append(executor.submit(analyze_instagram))
        if linkedin_username:
            futures.append(executor.submit(analyze_linkedin))
        if twitter_username:
            futures.append(executor.submit(analyze_twitter))
        if facebook_username:
            futures.append(executor.submit(analyze_facebook))
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                platform_name, platform_result = future.result()
                results[platform_name] = platform_result
                print(f"✅ {platform_name.title()} analysis completed")
            except Exception as e:
                print(f"❌ Platform analysis error: {e}")
                import traceback
                traceback.print_exc()
    
    elapsed = time.time() - start_time
    print(f"⏱️  Parallel analysis completed in {elapsed:.2f} seconds")
    
    # Process Instagram results and generate profile
    if instagram_username and 'instagram' in results:
        # Extract full name from scraped Instagram data (first post)
        scraped_full_name = "User"
        if results.get('instagram') and len(results['instagram']) > 0:
            first_post = results['instagram'][0]
            if isinstance(first_post, dict) and 'owner_full_name' in first_post:
                scraped_full_name = first_post['owner_full_name'] or "User"
        
        # Generate profile assessment (username only)
        profile_assessment = generate_profile_assessment("Instagram", instagram_username)
        results['instagram_profile'] = {
            'username': instagram_username,
            'full_name': scraped_full_name,
            'assessment': profile_assessment
        }
        cache.set(f'instagram_profile_{user_id}', results['instagram_profile'], 3600)
    
    # Process Twitter results and generate profile
    if twitter_username and 'twitter' in results:
        twitter_result = results.get('twitter')
        
        # Check if result is an error string (account doesn't exist)
        if isinstance(twitter_result, str):
            print(f"⚠️  Twitter scraper returned error: {twitter_result[:100]}")
            # Convert error string to proper error state
            results['twitter'] = [{
                "post": f"⚠️ Unable to analyze Twitter account @{twitter_username}",
                "post_data": {
                    "caption": None,
                    "data_unavailable": True,
                    "error": twitter_result,
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
        if isinstance(results.get('twitter'), list) and len(results['twitter']) > 0:
            first_post = results['twitter'][0]
            if isinstance(first_post, dict):
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
        cache.set(f'twitter_profile_{user_id}', results['twitter_profile'], 3600)
    
    # Process Facebook results and generate profile
    if facebook_username and 'facebook' in results:
        # Extract full name from scraped Facebook data (first post)
        scraped_full_name = "User"
        if results.get('facebook') and len(results['facebook']) > 0:
            first_post = results['facebook'][0]
            if isinstance(first_post, dict):
                scraped_full_name = (
                    first_post.get('author_name') or 
                    first_post.get('user_name') or 
                    first_post.get('profile_name') or 
                    "User"
                )
        
        # Generate profile assessment (username only)
        profile_assessment = generate_profile_assessment("Facebook", facebook_username)
        results['facebook_profile'] = {
            'username': facebook_username,
            'full_name': scraped_full_name,
            'assessment': profile_assessment
        }
        cache.set(f'facebook_profile_{user_id}', results['facebook_profile'], 3600)
    
    # Cache all results
    if 'instagram' in results:
        cache.set(f'instagram_analysis_{user_id}', results.get('instagram', []), 3600)
    if 'twitter' in results:
        cache.set(f'twitter_analysis_{user_id}', results.get('twitter', []), 3600)
    if 'linkedin' in results:
        cache.set(f'linkedin_analysis_{user_id}', results.get('linkedin', []), 3600)
    if 'facebook' in results:
        cache.set(f'facebook_analysis_{user_id}', results.get('facebook', []), 3600)
    
    # Set completion stage
    cache.set(f'analysis_stage_{user_id}', 'complete', timeout=60*60)
    cache.set(f'stage_progress_{user_id}', 100, timeout=60*60)
    
    return results


# ==== RUN SCRIPT ====
if __name__ == "__main__":
    analysis = analyze_instagram_post(INSTAGRAM_USERNAME)
    if analysis:
        print(json.dumps(analysis, indent=2))
