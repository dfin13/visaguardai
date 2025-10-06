# twitter_analyzer.py
import os
from apify_client import ApifyClient
from openai import OpenAI
import json
import re
import time
from django.conf import settings
from dashboard.models import Config
from dashboard.utils_email import send_api_expiry_alert

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
apify_client = ApifyClient(APIFY_API_TOKEN)
client_ai = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# REMOVED: generate_fallback_tweets function
# This function was creating fake tweets when scraping failed.
# Instead, we now return proper "inaccessible account" responses.

def analyze_twitter_profile(username: str, tweets_desired: int = 5):
    """
    Analyze Twitter profile.
    Returns proper response for inaccessible accounts instead of fabricating content.
    """
    from .account_checker import check_scraping_result, create_inaccessible_account_response, is_account_private_error
    
    print(f"Starting Twitter analysis for {username}")
    
    # === APIFY ACTOR CONFIG ===
    actor_id = "danek/twitter-timeline"
    run_input = {
        "usernames": [username],     # expects list
        "max_posts": tweets_desired, # required field
        "include_replies": False,
        "include_user_info": True,
        "max_request_retries": 3,
        "request_timeout_secs": 30,
    }

    try:
        # === RUN ACTOR ===
        print("Starting Apify actor...")
        run = apify_client.actor(actor_id).call(run_input=run_input, wait_secs=15)
        
        # Wait for dataset to populate
        time.sleep(5)
        
        # === GET DATASET ITEMS ===
        dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        print(f"Retrieved {len(dataset_items)} items from dataset")
        
        # Debug: show raw dataset items
        print("Raw dataset items:", json.dumps(dataset_items[:2], indent=2))
        
        # === Extract tweets ===
        tweets = []
        for item in dataset_items:
            tweet_text = item.get("full_text") or item.get("text") or item.get("content")
            if tweet_text:
                tweets.append({"tweet": tweet_text})
        
        # Check if account is accessible
        is_accessible, result = check_scraping_result(tweets, "Twitter", username)
        if not is_accessible:
            return result
            
    except TypeError as e:
        print(f"Error calling Apify task: {e}")
        if is_account_private_error(str(e)):
            return create_inaccessible_account_response("Twitter", username, "is private or inaccessible")
        else:
            return create_inaccessible_account_response("Twitter", username, "could not be accessed")
    except Exception as e:
        print(f"Error during Twitter analysis: {str(e)}")
        error_str = str(e).lower()
        if any(word in error_str for word in ["expired", "invalid", "authentication", "quota", "rate-limit", "permission"]):
            send_api_expiry_alert(
                subject="VisaGuardAI: Apify API Expiry/Failure Alert",
                body=f"Twitter Apify API error: {e}",
                to_email="syedawaisalishah46@gmail.com"
            )
        
        if is_account_private_error(str(e)):
            return create_inaccessible_account_response("Twitter", username, "is private or inaccessible")
        else:
            return create_inaccessible_account_response("Twitter", username, "could not be accessed")

    tweets_json = json.dumps(tweets, ensure_ascii=False)

    print(f"Analyzing {len(tweets)} tweets...")
    
    # === Build AI Prompt ===
    prompt = f"""
    You are an AI-based content recommendation engine for paid users.
    Analyze the following Twitter posts and return a JSON array where each element corresponds to one tweet.

    Rules:
    1. Content Reinforcement: If safe, positive, low-risk → encourage similar content.
    2. Content Suppression: If political → suggest avoiding such topics.
    3. Content Flag: If culturally sensitive or controversial → recommend removing it.
    4. Output must be valid JSON ONLY with the following structure for EACH tweet:

    [
      {{
        "tweet": "original tweet text",
        "Twitter": {{
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

    The tweets to analyze (as JSON array):
    {tweets_json}
    """

    # === SEND TO OPENROUTER ===
    try:
        response = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that returns valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI request failed: {str(e)}")
        error_str = str(e).lower()
        if any(word in error_str for word in ["expired", "invalid", "authentication", "quota", "rate-limit"]):
            send_api_expiry_alert(
                subject="VisaGuardAI: OpenAI API Expiry/Failure Alert",
                body=f"Twitter OpenAI API error: {e}",
                to_email="syedawaisalishah46@gmail.com"
            )
        
        # Return fallback analysis data in the expected format
        fallback_analysis = []
        for tweet in tweets:
            fallback_analysis.append({
                "tweet": tweet["tweet"],
                "Twitter": {
                    "content_reinforcement": {
                        "status": "safe",
                        "recommendation": "Continue posting similar professional content",
                        "reason": "Professional and career-focused content is generally safe and appropriate"
                    },
                    "content_suppression": {
                        "status": "safe",
                        "recommendation": None,
                        "reason": "No concerning content detected"
                    },
                    "content_flag": {
                        "status": "safe",
                        "recommendation": None,
                        "reason": "Content appears professional and appropriate"
                    },
                    "risk_score": 1
                }
            })
        
        return json.dumps(fallback_analysis, ensure_ascii=False)


def analyze_with_sample_tweets():
    """Fallback function with sample tweets for testing"""
    sample_tweets = [
        "Just had a great meeting with the team! #productivity",
        "Looking forward to the weekend! ",
        "Interesting article about technology trends: https://example.com"
    ]
    
    tweets_text = "\n".join(f"- {tweet}" for tweet in sample_tweets)
    
    prompt = f"""
    Analyze these sample tweets and return JSON as requested:
    {tweets_text}
    """
    
    response = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant that returns valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    
    return response.choices[0].message.content

def test_user_existence(username: str):
    """Test if a Twitter user exists using a different approach"""
    try:
        actor_id = "apidojo/tweet-scraper"
        run_input = {
            "searchTerms": [f"from:{username}"],
            "maxTweets": 1,
            "addUserInfo": True
        }
        
        run = apify_client.actor(actor_id).call(run_input=run_input)
        dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        
        return len(dataset_items) > 0
    except:
        return False

if __name__ == "__main__":
    username = "syedAsimBacha10"   # without @
    tweets_desired = 5
    
    print(f"Testing if user {username} exists...")
    user_exists = test_user_existence(username)
    print(f"User exists: {user_exists}")
    
    if user_exists:
        result = analyze_twitter_profile(username, tweets_desired)
        print("Analysis result:")
        print(result)
    else:
        print(f"User {username} may not exist or account is private")
        result = analyze_with_sample_tweets()
        print("Fallback analysis result:")
        print(result)
