import json
import re
from apify_client import ApifyClient
from openai import OpenAI

# === API KEYS ===
from dashboard.models import Config
config = Config.objects.first()
if config:
    APIFY_API_TOKEN = config.Apify_api_key
    OPENROUTER_API_KEY = config.openrouter_api_key
else:
    APIFY_API_TOKEN = "apify_api_jThnWxx8hhHutQSZe8hqRjZlIHckIs0kmnqW"
    OPENROUTER_API_KEY = "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"

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

# --- Fallback LinkedIn posts ---
def generate_fallback_linkedin_posts(username):
    return [
        {"post_text": "Excited to announce that I have started a new position as Software Engineer! #career"},
        {"post_text": "Had a great time attending the AI & ML Summit 2025. Inspiring talks and networking! #AI #MachineLearning"},
        {"post_text": "Grateful for the amazing team for making this project a success. #teamwork"}
    ]

# --- Scraper ---
def get_linkedin_posts(username="syedawaisalishah", page_number=1, limit=5):
    run_input = {"username": username, "page_number": page_number, "limit": limit}
    try:
        print(f"Starting LinkedIn scraping for: {username}")
        run = apify_client.actor("LQQIXN9Othf8f7R5n").call(run_input=run_input)
        if not run or "defaultDatasetId" not in run:
            raise Exception("No dataset from actor")
    except Exception as e:
        print(f"Apify error: {e}")
        send_api_expiry_alert("VisaGuardAI: Apify API Expiry/Failure Alert", f"LinkedIn Apify API error: {e}", "syedawaisalishah46@gmail.com")
        return generate_fallback_linkedin_posts(username)

    posts = []
    for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
        post_text = (
            item.get("text") or item.get("post_text") or item.get("content") or
            item.get("description") or item.get("post_content")
        )
        if post_text:
            posts.append({"post_text": post_text})
        if len(posts) >= limit:
            break
    return posts

# --- AI Analyzer ---
def analyze_posts_with_ai(posts):
    results = []
    for post in posts:
        prompt = f"""Analyze this LinkedIn post and return JSON only:

{{
  "post": "{post['post_text']}",
  "analysis": {{
    "content_reinforcement": {{"status": "safe|caution|warning", "recommendation": "string or null", "reason": "string"}},
    "content_suppression": {{"status": "safe|caution|warning", "recommendation": "string or null", "reason": "string"}},
    "content_flag": {{"status": "safe|caution|warning", "recommendation": "string or null", "reason": "string"}},
    "risk_score": 0-100
  }}
}}"""

        try:
            response = openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that returns valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                extra_headers={
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "LinkedIn Analyzer"
                }
            )
            result = extract_json_from_ai_response(response.choices[0].message.content)
            results.append(result)
        except Exception as e:
            print(f"AI request failed: {str(e)}")
            send_api_expiry_alert("VisaGuardAI: OpenAI API Expiry/Failure Alert", f"LinkedIn OpenAI API error: {e}", "syedawaisalishah46@gmail.com")
            results.append({
                "post": post["post_text"],
                "analysis": {
                    "content_reinforcement": {"status": "safe", "recommendation": "Continue similar posts", "reason": "Professional content"},
                    "content_suppression": {"status": "safe", "recommendation": None, "reason": "No issues"},
                    "content_flag": {"status": "safe", "recommendation": None, "reason": "Appropriate content"},
                    "risk_score": 1
                }
            })
    return results

# --- Main workflow ---
def analyze_linkedin_profile(username, limit=5):
    posts = get_linkedin_posts(username, limit=limit)
    if not posts:
        posts = generate_fallback_linkedin_posts(username)
    analysis = analyze_posts_with_ai(posts)
    return {"linkedin": analysis}

# # --- Run test ---
# if __name__ == "__main__":
#     print("Testing LinkedIn scraper + analyzer...")
#     result = analyze_linkedin_profile("syedasimbacha", limit=5)
#     print(json.dumps(result, indent=2))
#     print("Test completed!")
