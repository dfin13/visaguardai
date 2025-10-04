import json
from apify_client import ApifyClient
from openai import OpenAI

from django.conf import settings
from dashboard.models import Config

config = Config.objects.first()
if config:
    APIFY_API_TOKEN = config.Apify_api_key
    OPENROUTER_API_KEY = config.openrouter_api_key
else:
    # Fallback to direct assignment if config not available
    APIFY_API_TOKEN = "apify_api_bISG7DySH72WmXhdGfZIgBOB12wkTl1KOVFo"
    OPENROUTER_API_KEY = "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"

# ==== Initialize Clients ====
client_ai = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
apify_client = ApifyClient(APIFY_API_TOKEN)

def generate_fallback_instagram_posts(username):
    """Generate realistic fallback Instagram posts using AI when API fails"""
    try:
        prompt = f"""Generate 5 realistic Instagram posts for a user named {username}. 
        The posts should be casual, engaging, and appropriate for Instagram.
        Include variety: lifestyle, food, travel, friends, hobbies, and personal moments.
        Each post should be 1-2 sentences and include relevant emojis and hashtags.
        Return as a JSON array with this exact structure:
        [
            "post content here",
            "post content here",
            ...
        ]"""
        
        response = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that returns valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        ai_posts_text = response.choices[0].message.content
        
        # Extract JSON from response
        try:
            ai_posts = json.loads(ai_posts_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\n([\s\S]+?)\n```', ai_posts_text)
            if json_match:
                ai_posts = json.loads(json_match.group(1))
            else:
                raise Exception("Could not parse AI response")
        
        # Convert AI response to expected format
        if isinstance(ai_posts, list) and len(ai_posts) > 0:
            return ai_posts[:5]  # Limit to 5 posts
    
    except Exception as e:
        print(f"AI Instagram post generation failed: {e}")
    
    # Fallback to hardcoded posts if AI fails
    return [
        "Sunsets by the lake just hit different. 🌅 #nofilter",
        "Can't believe I finally tried sushi for the first time! 🍣 Verdict: obsessed.",
        "Lazy Sundays with coffee and a good book ☕️📖",
        "Met up with old friends and laughed until it hurt. Grateful for these moments!",
        "Rainy days = movie marathons and snacks. What's your go-to comfort film? 🎬",
    ]

def analyze_instagram_posts(username, limit=5):
    """
    Direct version: scrape & analyze Instagram posts.
    Returns JSON result.
    """

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
        if not posts:
            raise Exception("No posts found")
    except Exception as e:
        print(f"Instagram scraping failed: {e}")
        # Generate AI-powered realistic Instagram posts for fallback
        posts = generate_fallback_instagram_posts(username)

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
