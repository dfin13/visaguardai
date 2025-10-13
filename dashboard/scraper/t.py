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

# Log which Apify key source is being used
if os.getenv('APIFY_API_KEY'):
    print("🔑 [Twitter] Using Apify key from .env")
else:
    print("🔑 [Twitter] Using Apify key from Config table")

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

def analyze_twitter_profile(username: str, tweets_desired: int = 10):
    """
    Analyze Twitter profile.
    Returns proper response for inaccessible accounts instead of fabricating content.
    Maximum limit: 10 tweets to prevent excessive API usage.
    """
    from .account_checker import check_scraping_result, create_inaccessible_account_response, is_account_private_error
    
    # Cap limit at 10 tweets maximum
    tweets_desired = min(tweets_desired, 10)
    
    print(f"Starting Twitter analysis for {username} (limit: {tweets_desired} tweets, capped at 10 max)")
    
    # === APIFY ACTOR CONFIG ===
    actor_id = "apidojo/tweet-scraper"
    run_input = {
        "searchTerms": [f"from:{username}"],
        "maxTweets": tweets_desired,
        "addUserInfo": True,
        "includeSearchTerms": False,
        "onlyImage": False,
        "onlyQuote": False,
        "onlyTwitterBlue": False,
        "onlyVerifiedUsers": False,
        "onlyVideo": False,
    }

    try:
        # === RUN ACTOR ===
        print("Starting Apify actor...")
        print(f"⚠️  WARNING: maxTweets set to {tweets_desired}, but actor may ignore this!")
        run = apify_client.actor(actor_id).call(run_input=run_input, wait_secs=15)
        
        # Wait for dataset to populate
        time.sleep(5)
        
        # === GET DATASET ITEMS WITH HARD LIMIT ===
        # CRITICAL: Use limit parameter to prevent pulling all tweets
        # This prevents billing for hundreds of tweets when we only need 10
        dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items(limit=tweets_desired).items
        print(f"Retrieved {len(dataset_items)} items from dataset (HARD LIMIT: {tweets_desired})")
        
        # Debug: show raw dataset items
        print("Raw dataset items:", json.dumps(dataset_items[:2], indent=2))
        
        # === Extract tweets with all metadata ===
        tweets = []
        for item in dataset_items:
            try:
                # Extract tweet text
                tweet_text = (
                    item.get("full_text") or 
                    item.get("text") or 
                    item.get("content") or 
                    item.get("tweet", {}).get("full_text") or
                    item.get("tweet", {}).get("text")
                )
                
                if not tweet_text:
                    continue
                
                # Extract URL
                tweet_url = (
                    item.get("url") or 
                    item.get("tweetUrl") or
                    item.get("tweet", {}).get("url") or
                    f"https://twitter.com/{username}/status/{item.get('id_str', '')}"
                )
                
                # Extract timestamp
                timestamp = (
                    item.get("created_at") or
                    item.get("createdAt") or
                    item.get("timestamp") or
                    item.get("tweet", {}).get("created_at")
                )
                
                # Extract engagement metrics
                likes_count = (
                    item.get("favorite_count") or
                    item.get("likes") or
                    item.get("likeCount") or
                    item.get("tweet", {}).get("favorite_count") or
                    0
                )
                
                replies_count = (
                    item.get("reply_count") or
                    item.get("replies") or
                    item.get("replyCount") or
                    item.get("tweet", {}).get("reply_count") or
                    0
                )
                
                retweets_count = (
                    item.get("retweet_count") or
                    item.get("retweets") or
                    item.get("retweetCount") or
                    item.get("tweet", {}).get("retweet_count") or
                    0
                )
                
                # Extract hashtags and mentions
                hashtags = []
                mentions = []
                
                entities = item.get("entities", {})
                if entities:
                    hashtags = [tag.get("text", "") for tag in entities.get("hashtags", [])]
                    mentions = [mention.get("screen_name", "") for mention in entities.get("user_mentions", [])]
                
                tweets.append({
                    "tweet": tweet_text,
                    "post_url": tweet_url,
                    "timestamp": timestamp,
                    "likes": likes_count,
                    "replies": replies_count,
                    "retweets": retweets_count,
                    "hashtags": hashtags,
                    "mentions": mentions,
                })
            except Exception as e:
                print(f"⚠️  Error extracting tweet data: {e}")
                continue
        
        # Enforce 10 tweet limit (safety slice in case actor returns more)
        tweets = tweets[:10]
        print(f"✅ Final count: {len(tweets)} tweets (capped at 10)")
        
        # Check if account is accessible
        is_accessible, result = check_scraping_result([{"tweet": t["tweet"]} for t in tweets], "Twitter", username)
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

    print(f"🤖 Starting intelligent analysis for {len(tweets)} tweets...")
    
    # === INTELLIGENT AI ANALYSIS ===
    from dashboard.intelligent_analyzer import analyze_posts_batch
    
    # Convert tweets to standard format
    tweets_data = []
    for tweet in tweets:
        tweets_data.append({
            'text': tweet.get('tweet', ''),
            'caption': tweet.get('tweet', ''),
            'post_text': tweet.get('tweet', ''),
            'post_url': tweet.get('post_url', ''),
            'timestamp': tweet.get('timestamp'),
            'created_at': tweet.get('timestamp'),
            'likes_count': tweet.get('likes', 0),
            'comments_count': tweet.get('replies', 0),
            'shares_count': tweet.get('retweets', 0),
            'type': 'tweet',
            'hashtags': tweet.get('hashtags', []),
            'mentions': tweet.get('mentions', []),
        })
    
    try:
        results = analyze_posts_batch("Twitter", tweets_data)
        print(f"✅ Twitter intelligent analysis complete: {len(results)} tweets")
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        import traceback
        print(f"❌ Twitter intelligent analysis failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        error_str = str(e).lower()
        if any(word in error_str for word in ["expired", "invalid", "authentication", "quota", "rate-limit"]):
            send_api_expiry_alert(
                subject="VisaGuardAI: AI Analysis Alert",
                body=f"Twitter intelligent analysis error: {e}",
                to_email="syedawaisalishah46@gmail.com"
            )
        
        # Return fallback error state
        fallback_analysis = []
        for tweet in tweets:
            fallback_analysis.append({
                "tweet": tweet["tweet"],
                "post_data": {
                    'caption': tweet["tweet"],
                    'post_url': tweet.get("post_url", ""),
                    'timestamp': tweet.get("timestamp"),
                    'likes_count': tweet.get("likes", 0),
                    'comments_count': tweet.get("replies", 0),
                    'shares_count': tweet.get("retweets", 0),
                    'data_unavailable': True,
                },
                "Twitter": {
                    "content_reinforcement": {
                        "status": "Needs Improvement",
                        "reason": f"Analysis error: {str(e)[:80]}",
                        "recommendation": "Try again later"
                    },
                    "content_suppression": {
                        "status": "Caution",
                        "reason": "Could not assess content",
                        "recommendation": "Manual review recommended"
                    },
                    "content_flag": {
                        "status": "Safe",
                        "reason": "No data available",
                        "recommendation": "Review manually"
                    },
                    "risk_score": -1
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
