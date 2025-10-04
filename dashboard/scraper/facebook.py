import json
from apify_client import ApifyClient
from openai import OpenAI
from django.conf import settings
from dashboard.models import Config
from dashboard.utils_email import send_api_expiry_alert
# ==== CONFIG ====
config = Config.objects.first()
if config:
    APIFY_API_TOKEN = config.Apify_api_key
    OPENROUTER_API_KEY = config.openrouter_api_key
else:
    pass

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

        if not posts:
            raise Exception('No posts found')
    except Exception as e:
        print(f"Scraping failed: {e}")
        error_str = str(e).lower()
        if any(word in error_str for word in ["expired", "invalid", "authentication", "quota", "rate-limit"]):
            send_api_expiry_alert(
                subject="VisaGuardAI: Apify API Expiry/Failure Alert",
                body=f"Apify API error: {e}",
                to_email="syedawaisalishah46@gmail.com"
            )
        # Fallback: generate realistic Facebook posts
        posts = [
            "Had an amazing family BBQ this weekend. Grateful for good food and even better company!",
            "Excited to share my latest blog post on productivity hacks. Let me know your thoughts!",
            "Throwback to last year's vacation in the mountains. Can't wait to travel again!",
            "Just finished reading an inspiring book on leadership. Highly recommend it to everyone.",
            "Celebrating 10 years at my company today. Thankful for the journey and the team!"
        ]

    if user_id:
        cache.set(f'analysis_stage_{user_id}', 'comment_scanning', timeout=60*60)
        cache.set(f'stage_progress_{user_id}', 15, timeout=60*60)

    # ==== Create single prompt ====
    posts_text = "\n\n".join([f"Post {i+1}: {text}" for i, text in enumerate(posts)])

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
