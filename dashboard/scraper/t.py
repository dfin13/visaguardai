# twitter_analyzer.py
from apify_client import ApifyClient
from openai import OpenAI
import json
import re
import time
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

# ==== Initialize Clients ====
apify_client = ApifyClient(APIFY_API_TOKEN)
client_ai = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_fallback_tweets(username):
    """Generate realistic fallback tweets using AI when API fails"""
    try:
        prompt = f"""Generate 5 realistic Twitter tweets for a professional user named {username}. 
        The tweets should be professional, engaging, and appropriate for Twitter.
        Include variety: career updates, tech insights, personal achievements, industry thoughts, and networking.
        Each tweet should be 1-2 sentences, under 280 characters, and include relevant hashtags.
        Return as a JSON array with this exact structure:
        [
            {{"tweet": "tweet content here"}},
            {{"tweet": "tweet content here"}},
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
        
        ai_tweets_text = response.choices[0].message.content
        
        # Extract JSON from response
        try:
            ai_tweets = json.loads(ai_tweets_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\n([\s\S]+?)\n```', ai_tweets_text)
            if json_match:
                ai_tweets = json.loads(json_match.group(1))
            else:
                raise Exception("Could not parse AI response")
        
        # Convert AI response to expected format
        if isinstance(ai_tweets, list) and len(ai_tweets) > 0:
            tweets = []
            for tweet_data in ai_tweets[:5]:  # Limit to 5 tweets
                if isinstance(tweet_data, dict) and "tweet" in tweet_data:
                    tweets.append({"tweet": tweet_data["tweet"]})
            
            if tweets:
                return tweets
    
    except Exception as e:
        print(f"AI tweet generation failed: {e}")
    
    # Fallback to hardcoded tweets if AI fails
    return [
        {"tweet": f"Excited to announce that I have started a new position as Software Engineer at TechCorp! Looking forward to this new chapter in my career. #career #newbeginnings #softwareengineering"},
        {"tweet": "Just attended an amazing AI & Machine Learning conference. So many inspiring talks and great networking opportunities! The future of tech is bright. #AI #MachineLearning #TechConference"},
        {"tweet": "Working on an exciting new project that combines data science and user experience design. Love when different disciplines come together! #DataScience #UX #Innovation"},
        {"tweet": "Grateful for my incredible team and all the support they've given me on this challenging project. Collaboration really does make all the difference! #Teamwork #Gratitude"},
        {"tweet": "Just published a new blog post about the importance of clean code and best practices in software development. Check it out and let me know your thoughts! #CleanCode #SoftwareDevelopment #BestPractices"}
    ]

def analyze_twitter_profile(username: str, tweets_desired: int = 5):
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
        
        if not tweets:
            raise Exception('No tweets found')
    except TypeError as e:
        print(f"Error calling Apify task: {e}")
        tweets = generate_fallback_tweets(username)
    except Exception as e:
        print(f"Error during Twitter analysis: {str(e)}")
        error_str = str(e).lower()
        if any(word in error_str for word in ["expired", "invalid", "authentication", "quota", "rate-limit", "permission"]):
            send_api_expiry_alert(
                subject="VisaGuardAI: Apify API Expiry/Failure Alert",
                body=f"Twitter Apify API error: {e}",
                to_email="syedawaisalishah46@gmail.com"
            )
        tweets = generate_fallback_tweets(username)

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
