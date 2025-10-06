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

    # ==== SCRAPE INSTAGRAM POSTS ====
    run_input = {
        "username": [username],
        "resultsLimit": limit,
        "scrapePostsUntilDate": None,
        "shouldDownloadMedia": False,
    }

    print(f"Scraping {limit} Instagram posts for {username}...")
    try:
        run = apify_client.actor("apify/instagram-post-scraper").call(run_input=run_input)
        posts = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            post_text = item.get("caption", "").strip()
            if post_text:
                posts.append(post_text)
        
        # Check if account is accessible
        is_accessible, result = check_scraping_result(posts, "Instagram", username)
        if not is_accessible:
            return result
            
    except Exception as e:
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
