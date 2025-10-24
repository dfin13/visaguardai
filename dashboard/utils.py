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
    
    # Skip all profile generation - just cache analysis results directly
    print(f"📦 Caching results to cache (skipping profile generation):")
    print(f"   Results keys: {list(results.keys())}")
    
    if 'instagram' in results:
        data = results.get('instagram', [])
        print(f"   ✅ Caching Instagram: {len(data) if isinstance(data, list) else type(data).__name__}")
        cache.set(f'instagram_analysis_{user_id}', data, 3600)
    
    if 'twitter' in results:
        data = results.get('twitter', [])
        print(f"   ✅ Caching Twitter: {len(data) if isinstance(data, list) else type(data).__name__}")
        cache.set(f'twitter_analysis_{user_id}', data, 3600)
    
    if 'linkedin' in results:
        data = results.get('linkedin', [])
        print(f"   ✅ Caching LinkedIn: {len(data) if isinstance(data, list) else type(data).__name__}")
        cache.set(f'linkedin_analysis_{user_id}', data, 3600)
    
    if 'facebook' in results:
        data = results.get('facebook', [])
        print(f"   ✅ Caching Facebook: {len(data) if isinstance(data, list) else type(data).__name__}")
        cache.set(f'facebook_analysis_{user_id}', data, 3600)
    
    print(f"✅ All results cached successfully")
    print(f"\n✅ Background analysis completed for user {user_id}\n")
    
    # Profile generation - Extract full name from scraped Instagram data (first post)
    if instagram_username:
        scraped_full_name = "User"
        if isinstance(results.get('instagram'), list) and len(results['instagram']) > 0:
            first_post = results['instagram'][0]
            if isinstance(first_post, dict):
                # Check multiple possible locations for the full name
                # First check post_data (which contains the raw scraped data)
                post_data = first_post.get('post_data', {})
                
                # DEBUG: Print what we have in the data
                print(f"🔍 [INSTAGRAM DEBUG] First post keys: {list(first_post.keys())}")
                print(f"🔍 [INSTAGRAM DEBUG] Post_data keys: {list(post_data.keys())}")
                print(f"🔍 [INSTAGRAM DEBUG] owner_full_name from post_data: {post_data.get('owner_full_name')}")
                print(f"🔍 [INSTAGRAM DEBUG] owner_full_name from first_post: {first_post.get('owner_full_name')}")
                
                scraped_full_name = (
                    post_data.get('owner_full_name') or
                    post_data.get('ownerFullName') or
                    first_post.get('owner_full_name') or
                    first_post.get('ownerFullName') or
                    "User"
                )
                
                print(f"🔍 [INSTAGRAM DEBUG] Final scraped_full_name: {scraped_full_name}")
        
        # Generate profile assessment (username only)
        profile_assessment = generate_profile_assessment("Instagram", instagram_username)
        results['instagram_profile'] = {
            'username': instagram_username,
            'full_name': scraped_full_name,
            'assessment': profile_assessment
        }
        cache.set(f'instagram_profile_{user_id}', results['instagram_profile'], 3600)
    
    # Process Twitter results and generate profile
    if twitter_username:
        # Extract full name from scraped Twitter data (first post)
        scraped_full_name = "User"
        
        # Try to get author name from post data first
        if 'twitter' in results and isinstance(results.get('twitter'), list) and len(results['twitter']) > 0:
            first_post = results['twitter'][0]
            if isinstance(first_post, dict):
                # Check post_data first (contains raw scraped data), then direct fields
                post_data = first_post.get('post_data', {})
                
                # DEBUG: Print what we have in the data
                print(f"🔍 [TWITTER DEBUG] First post keys: {list(first_post.keys())}")
                print(f"🔍 [TWITTER DEBUG] Post_data keys: {list(post_data.keys())}")
                print(f"🔍 [TWITTER DEBUG] author_name from post_data: {post_data.get('author_name')}")
                print(f"🔍 [TWITTER DEBUG] author_name from first_post: {first_post.get('author_name')}")
                
                # Try to extract author name from the data
                potential_name = (
                    post_data.get('author_name') or
                    post_data.get('user_name') or
                    post_data.get('display_name') or
                    post_data.get('full_name') or
                    first_post.get('author_name') or 
                    first_post.get('user_name') or 
                    first_post.get('profile_name') or
                    first_post.get('display_name') or
                    first_post.get('full_name') or
                    None
                )
                
                if potential_name and potential_name.strip():
                    scraped_full_name = potential_name
        
        # Always try fallback if we don't have a name yet
        if scraped_full_name == "User" and twitter_username and twitter_username.strip():
            scraped_full_name = twitter_username.replace('_', ' ').replace('-', ' ').title()
        
        print(f"🔍 [TWITTER DEBUG] Final scraped_full_name: {scraped_full_name}")
        
        # Generate profile assessment (username only)
        profile_assessment = generate_profile_assessment("X", twitter_username)
        results['twitter_profile'] = {
            'username': twitter_username,
            'full_name': scraped_full_name,
            'assessment': profile_assessment
        }
        cache.set(f'twitter_profile_{user_id}', results['twitter_profile'], 3600)
        print(f"🔍 [TWITTER DEBUG] Cached profile: {results['twitter_profile']}")
    
    # Process Facebook results and generate profile
    if facebook_username:
        # Extract full name from scraped Facebook data (first post)
        scraped_full_name = "User"
        
        # Try to get author name from post data first
        if 'facebook' in results and isinstance(results.get('facebook'), list) and len(results['facebook']) > 0:
            first_post = results['facebook'][0]
            if isinstance(first_post, dict):
                # Check post_data first (contains raw scraped data), then direct fields
                post_data = first_post.get('post_data', {})
                
                # DEBUG: Print what we have in the data
                print(f"🔍 [FACEBOOK DEBUG] First post keys: {list(first_post.keys())}")
                print(f"🔍 [FACEBOOK DEBUG] Post_data keys: {list(post_data.keys())}")
                print(f"🔍 [FACEBOOK DEBUG] author_name from post_data: {post_data.get('author_name')}")
                print(f"🔍 [FACEBOOK DEBUG] author_name from first_post: {first_post.get('author_name')}")
                
                # Try to extract author name from the data
                potential_name = (
                    post_data.get('author_name') or
                    post_data.get('user_name') or
                    post_data.get('display_name') or
                    post_data.get('full_name') or
                    post_data.get('profile_name') or
                    post_data.get('page_name') or
                    post_data.get('pageName') or
                    first_post.get('author_name') or 
                    first_post.get('user_name') or 
                    first_post.get('profile_name') or
                    first_post.get('display_name') or
                    first_post.get('full_name') or
                    None
                )
                
                if potential_name and potential_name.strip():
                    scraped_full_name = potential_name
        
        # Always try fallback if we don't have a name yet
        if scraped_full_name == "User" and facebook_username and facebook_username.strip():
            scraped_full_name = facebook_username.replace('_', ' ').replace('-', ' ').title()
        
        print(f"🔍 [FACEBOOK DEBUG] Final scraped_full_name: {scraped_full_name}")
        
        # Generate profile assessment (username only)
        profile_assessment = generate_profile_assessment("Facebook", facebook_username)
        results['facebook_profile'] = {
            'username': facebook_username,
            'full_name': scraped_full_name,
            'assessment': profile_assessment
        }
        cache.set(f'facebook_profile_{user_id}', results['facebook_profile'], 3600)
        print(f"🔍 [FACEBOOK DEBUG] Cached profile: {results['facebook_profile']}")
    
    # Process LinkedIn results and generate profile
    if linkedin_username:
        # Extract full name from scraped LinkedIn data (first post)
        scraped_full_name = "User"
        
        # Try to get author name from post data first
        if 'linkedin' in results:
            # LinkedIn data might be in different format (dict with 'linkedin' key or list)
            linkedin_data = results.get('linkedin')
            linkedin_posts = []
            
            if isinstance(linkedin_data, dict) and 'linkedin' in linkedin_data:
                linkedin_posts = linkedin_data['linkedin']
            elif isinstance(linkedin_data, list):
                linkedin_posts = linkedin_data
                
            if linkedin_posts and len(linkedin_posts) > 0:
                first_post = linkedin_posts[0]
                if isinstance(first_post, dict):
                    # Check post_data first (contains raw scraped data), then direct fields
                    post_data = first_post.get('post_data', {})
                    
                    # DEBUG: Print what we have in the data
                    print(f"🔍 [LINKEDIN DEBUG] First post keys: {list(first_post.keys())}")
                    print(f"🔍 [LINKEDIN DEBUG] Post_data keys: {list(post_data.keys())}")
                    print(f"🔍 [LINKEDIN DEBUG] author_name from post_data: {post_data.get('author_name')}")
                    print(f"🔍 [LINKEDIN DEBUG] author_name from first_post: {first_post.get('author_name')}")
                    
                    # Try to extract author name from the data
                    potential_name = (
                        post_data.get('author_name') or
                        post_data.get('user_name') or
                        post_data.get('display_name') or
                        post_data.get('full_name') or
                        post_data.get('profile_name') or
                        post_data.get('page_name') or
                        post_data.get('pageName') or
                        first_post.get('author_name') or 
                        first_post.get('user_name') or 
                        first_post.get('profile_name') or
                        first_post.get('display_name') or
                        first_post.get('full_name') or
                        None
                    )
                    
                    if potential_name and isinstance(potential_name, str) and potential_name.strip():
                        scraped_full_name = potential_name
        
        # Always try fallback if we don't have a name yet
        if scraped_full_name == "User" and linkedin_username and linkedin_username.strip():
            scraped_full_name = linkedin_username.replace('_', ' ').replace('-', ' ').title()
        
        print(f"🔍 [LINKEDIN DEBUG] Final scraped_full_name: {scraped_full_name}")
        
        # Generate profile assessment (username only)
        profile_assessment = generate_profile_assessment("LinkedIn", linkedin_username)
        results['linkedin_profile'] = {
            'username': linkedin_username,
            'full_name': scraped_full_name,
            'assessment': profile_assessment
        }
        cache.set(f'linkedin_profile_{user_id}', results['linkedin_profile'], 3600)
        print(f"🔍 [LINKEDIN DEBUG] Cached profile: {results['linkedin_profile']}")
    
    # Cache all results (temporary fast access)
    print(f"📦 Caching results to cache:")
    print(f"   Results keys: {list(results.keys())}")
    
    if 'instagram' in results:
        data = results.get('instagram', [])
        print(f"   ✅ Caching Instagram: {len(data) if isinstance(data, list) else type(data).__name__}")
        cache.set(f'instagram_analysis_{user_id}', data, 3600)
    
    if 'twitter' in results:
        data = results.get('twitter', [])
        print(f"   ✅ Caching Twitter: {len(data) if isinstance(data, list) else type(data).__name__}")
        cache.set(f'twitter_analysis_{user_id}', data, 3600)
    
    if 'linkedin' in results:
        data = results.get('linkedin', [])
        print(f"   ✅ Caching LinkedIn: {len(data) if isinstance(data, list) else type(data).__name__} - Data: {data if not isinstance(data, list) else f'{len(data)} posts'}")
        cache.set(f'linkedin_analysis_{user_id}', data, 3600)
    
    if 'facebook' in results:
        data = results.get('facebook', [])
        print(f"   ✅ Caching Facebook: {len(data) if isinstance(data, list) else type(data).__name__} - Data: {data if not isinstance(data, list) else f'{len(data)} posts'}")
        cache.set(f'facebook_analysis_{user_id}', data, 3600)
    
    # Verify cache was set
    print(f"🔍 Verifying cache after save:")
    print(f"   Instagram cache: {type(cache.get(f'instagram_analysis_{user_id}')).__name__}")
    print(f"   Twitter cache: {type(cache.get(f'twitter_analysis_{user_id}')).__name__}")
    print(f"   LinkedIn cache: {type(cache.get(f'linkedin_analysis_{user_id}')).__name__}")
    print(f"   Facebook cache: {type(cache.get(f'facebook_analysis_{user_id}')).__name__}")
    
    # Persist results to database for permanent storage
    # Instagram - Process with detailed progress stages
    import time
    try: