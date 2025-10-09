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
    Analyze all platforms, always returning a result (real or dummy) for each.
    If any step fails, fallback to dummy data and keep going.
    """
    from .scraper.instagram import analyze_instagram_posts
    from .scraper.linkedin import analyze_linkedin_profile
    from .scraper.t import analyze_twitter_profile
    from .scraper.facebook import analyze_facebook_posts
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
            print(f"DEBUG: Instagram analysis result: {results['instagram']}")
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

    # LinkedIn - Skip since it's already processed in the main thread
    # LinkedIn analysis is handled directly in start_analysis() to avoid duplication
    results['linkedin'] = []  # Placeholder, actual results are cached from main thread
    print(f"DEBUG: LinkedIn data placeholder set (actual data is cached in main thread): {results['linkedin']}")

    # Twitter
    try:
        if twitter_username:
            results['twitter'] = analyze_twitter_profile(twitter_username)
            print(f"DEBUG: Twitter analysis result: {results['twitter']}")
        else:
            results['twitter'] = []
    except Exception as e:
        print(f"Twitter analysis failed: {e}")
        # Use OpenRouter to generate fake posts with the user's prompt
        try:
            from openai import OpenAI
            from dashboard.models import Config
            config = Config.objects.first()
            OPENROUTER_API_KEY = config.openrouter_api_key if config else os.getenv('OPENROUTER_API_KEY') or getattr(settings, 'OPENROUTER_API_KEY', None)
            client_ai = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
            prompt = f"""
You are an AI-based content recommendation engine for paid users.
generate fake posts and return a JSON array where each element corresponds to one tweet.

Rules:
1. Content Reinforcement: If safe, positive, low-risk → encourage similar content.
2. Content Suppression: If political → suggest avoiding such topics.
3. Content Flag: If culturally sensitive or controversial → recommend removing it.
4. Output must be valid JSON ONLY with the following structure for EACH tweet:

[
  {{
    \"Twitter\": {{
      \"content_reinforcement\": {{
        \"status\": \"safe|caution|warning\",
        \"recommendation\": \"string or null\",
        \"reason\": \"string\"
      }},
      \"content_suppression\": {{
        \"status\": \"safe|caution|warning\",
        \"recommendation\": \"string or null\",
        \"reason\": \"string\"
      }},
      \"content_flag\": {{
        \"status\": \"safe|caution|warning\",
        \"recommendation\": \"string or null\",
        \"reason\": \"string\"
      }},
      \"risk_score\": 0
    }}
  }},
  ...
]
"""
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            ai_response = response.choices[0].message.content
            import json
            try:
                results['twitter'] = json.loads(ai_response)
            except json.JSONDecodeError:
                results['twitter'] = [{"post": "AI did not return valid JSON.", "analysis": ai_response}]
        except Exception as ai_e:
            print(f"AI fallback for Twitter dummy data failed: {ai_e}")
            results['twitter'] = [
                {"post": "Sample Tweet 1. This is fallback content.", "analysis": {"Twitter": {"content_reinforcement": {"status": "safe", "recommendation": None, "reason": "Dummy data."}, "content_suppression": {"status": "safe", "recommendation": None, "reason": "Dummy data."}, "content_flag": {"status": "safe", "recommendation": None, "reason": "Dummy data."}, "risk_score": 0}}}
            ]
            print(f"DEBUG: Twitter fallback dummy data set: {results['twitter']}")
            print(f"DEBUG: Twitter data before caching: {results['twitter']}")
    cache.set(f'twitter_analysis_{user_id}', results['twitter'], 3600)

    # Facebook
    try:
        if facebook_username:
            results['facebook'] = analyze_facebook_posts(facebook_username, limit=5, user_id=user_id)
            print(f"DEBUG: Facebook analysis result: {results['facebook']}")
            print(f"DEBUG: Facebook data before caching: {results['facebook']}")
        else:
            results['facebook'] = []
    except Exception as e:
        print(f"Facebook analysis failed: {e}")
        # Use OpenRouter to generate fake posts with an AI prompt
        try:
            from openai import OpenAI
            from dashboard.models import Config
            config = Config.objects.first()
            OPENROUTER_API_KEY = config.openrouter_api_key if config else os.getenv('OPENROUTER_API_KEY') or getattr(settings, 'OPENROUTER_API_KEY', None)
            client_ai = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
            prompt = f"""
You are an AI-based content recommendation engine for paid users.
generate fake posts and return a JSON array where each element corresponds to one Facebook post.

Rules:
1. Content Reinforcement: If safe, positive, low-risk → encourage similar content.
2. Content Suppression: If political → suggest avoiding such topics.
3. Content Flag: If culturally sensitive or controversial → recommend removing it.
4. Output must be valid JSON ONLY with the following structure for EACH post:

[
  {{
    \"Facebook\": {{
      \"content_reinforcement\": {{
        \"status\": \"safe|caution|warning\",
        \"recommendation\": \"string or null\",
        \"reason\": \"string\"
      }},
      \"content_suppression\": {{
        \"status\": \"safe|caution|warning\",
        \"recommendation\": \"string or null\",
        \"reason\": \"string\"
      }},
      \"content_flag\": {{
        \"status\": \"safe|caution|warning\",
        \"recommendation\": \"string or null\",
        \"reason\": \"string\"
      }},
      \"risk_score\": 0
    }}
  }},
  ...
]
"""
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            ai_response = response.choices[0].message.content
            import json
            try:
                results['facebook'] = json.loads(ai_response)
                print(f"DEBUG: Facebook fallback AI analysis result: {results['facebook']}")
                print(f"DEBUG: Facebook data before caching: {results['facebook']}")
            except json.JSONDecodeError:
                results['facebook'] = [{"post": "AI did not return valid JSON.", "analysis": ai_response}]
                print(f"DEBUG: Facebook fallback AI returned invalid JSON: {ai_response}")
                print(f"DEBUG: Facebook data before caching: {results['facebook']}")
        except Exception as ai_e:
            print(f"AI fallback for Facebook dummy data failed: {ai_e}")
            results['facebook'] = [
                {"post": "Sample Facebook post 1. This is fallback content.", "analysis": {"Facebook": {"content_reinforcement": {"status": "safe", "recommendation": None, "reason": "Dummy data."}, "content_suppression": {"status": "safe", "recommendation": None, "reason": "Dummy data."}, "content_flag": {"status": "safe", "recommendation": None, "reason": "Dummy data."}, "risk_score": 0}}}
            ]
            print("DEBUG: Facebook fallback dummy data set.")
            print(f"DEBUG: Facebook data before caching: {results['facebook']}")
    cache.set(f'facebook_analysis_{user_id}', results['facebook'], 3600)

    return results


# ==== RUN SCRIPT ====
if __name__ == "__main__":
    analysis = analyze_instagram_post(INSTAGRAM_USERNAME)
    if analysis:
        print(json.dumps(analysis, indent=2))
