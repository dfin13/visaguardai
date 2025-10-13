# tiktok_analyzer.py
import os
from apify_client import ApifyClient
from openai import OpenAI
import json
import time
from django.conf import settings
from dashboard.models import Config
from dashboard.utils_email import send_api_expiry_alert

# Get API keys from environment variables or Django settings
APIFY_API_TOKEN = os.getenv('APIFY_API_KEY') or getattr(settings, 'APIFY_API_KEY', None)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY') or getattr(settings, 'OPENROUTER_API_KEY', None)

# Log which Apify key source is being used
if os.getenv('APIFY_API_KEY'):
    print("🔑 [TikTok] Using Apify key from .env")
else:
    print("🔑 [TikTok] Using Apify key from Config table")

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


def analyze_tiktok_profile(username: str, videos_desired: int = 5):
    """
    Analyze TikTok profile.
    Returns proper response for inaccessible accounts instead of fabricating content.
    """
    from .account_checker import check_scraping_result, create_inaccessible_account_response, is_account_private_error
    
    print(f"Starting TikTok analysis for @{username}")
    
    # === APIFY ACTOR CONFIG ===
    actor_id = "clockworks/tiktok-profile-scraper"
    
    # Prepare username (remove @ if present)
    clean_username = username.lstrip('@')
    
    run_input = {
        "profiles": [f"@{clean_username}"],
        "resultsPerPage": videos_desired,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadSlideshowImages": False,
    }

    try:
        # === RUN ACTOR ===
        print(f"Starting Apify actor: {actor_id}...")
        run = apify_client.actor(actor_id).call(run_input=run_input, wait_secs=120)
        
        # Wait for dataset to populate
        time.sleep(5)
        
        # === GET DATASET ITEMS ===
        dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        print(f"Retrieved {len(dataset_items)} items from dataset")
        
        # Debug: show raw dataset items (first item only)
        if dataset_items:
            print("Raw dataset sample:", json.dumps(dataset_items[0], indent=2, default=str)[:500])
        
        # === Extract TikTok videos ===
        videos = []
        for item in dataset_items:
            # Extract video data with multiple fallback fields
            caption = item.get("text") or item.get("caption") or item.get("desc") or item.get("description") or ""
            
            # Extract video URL
            video_url = (
                item.get("videoUrl") or 
                item.get("video_url") or 
                item.get("webVideoUrl") or 
                item.get("playUrl") or
                item.get("url")
            )
            
            # Extract post URL
            post_url = (
                item.get("webVideoUrl") or 
                item.get("url") or
                item.get("shareUrl") or
                item.get("postUrl") or
                f"https://www.tiktok.com/@{clean_username}/video/{item.get('id', '')}"
            )
            
            # Extract timestamp
            timestamp = (
                item.get("createTime") or 
                item.get("created_at") or 
                item.get("createTimeISO") or
                item.get("timestamp")
            )
            
            # Extract engagement metrics
            likes = item.get("diggCount", 0) or item.get("likesCount", 0) or item.get("likes", 0)
            comments = item.get("commentCount", 0) or item.get("commentsCount", 0) or item.get("comments", 0)
            shares = item.get("shareCount", 0) or item.get("sharesCount", 0) or item.get("shares", 0)
            views = item.get("playCount", 0) or item.get("viewsCount", 0) or item.get("views", 0)
            
            # Extract hashtags and mentions (handle both list of strings and list of dicts)
            hashtags_raw = item.get("hashtags", [])
            hashtags = []
            if hashtags_raw and isinstance(hashtags_raw, list):
                for tag in hashtags_raw:
                    if isinstance(tag, str):
                        hashtags.append(tag)
                    elif isinstance(tag, dict):
                        hashtags.append(tag.get('name', tag.get('title', str(tag))))
            
            mentions_raw = item.get("mentions", [])
            mentions = []
            if mentions_raw and isinstance(mentions_raw, list):
                for mention in mentions_raw:
                    if isinstance(mention, str):
                        mentions.append(mention)
                    elif isinstance(mention, dict):
                        mentions.append(mention.get('name', mention.get('username', str(mention))))
            
            if caption or video_url:
                videos.append({
                    "video": caption,
                    "caption": caption,
                    "video_url": video_url,
                    "post_url": post_url,
                    "timestamp": timestamp,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "views": views,
                    "hashtags": hashtags,
                    "mentions": mentions,
                })
        
        # Check if account is accessible
        is_accessible, result = check_scraping_result(videos, "TikTok", username)
        if not is_accessible:
            return result
            
    except TypeError as e:
        print(f"Error calling Apify task: {e}")
        if is_account_private_error(str(e)):
            return create_inaccessible_account_response("TikTok", username, "is private or inaccessible")
        else:
            return create_inaccessible_account_response("TikTok", username, "could not be accessed")
    except Exception as e:
        print(f"Error during TikTok analysis: {str(e)}")
        error_str = str(e).lower()
        if any(word in error_str for word in ["expired", "invalid", "authentication", "quota", "rate-limit", "permission"]):
            send_api_expiry_alert(
                subject="VisaGuardAI: Apify API Expiry/Failure Alert",
                body=f"TikTok Apify API error: {e}",
                to_email="syedawaisalishah46@gmail.com"
            )
        
        if is_account_private_error(str(e)):
            return create_inaccessible_account_response("TikTok", username, "is private or inaccessible")
        else:
            return create_inaccessible_account_response("TikTok", username, "could not be accessed")

    print(f"🤖 Starting intelligent analysis for {len(videos)} TikTok videos...")
    
    # === INTELLIGENT AI ANALYSIS ===
    from dashboard.intelligent_analyzer import analyze_posts_batch
    
    # Convert videos to standard format
    videos_data = []
    for video in videos:
        videos_data.append({
            'caption': video.get('caption', ''),
            'text': video.get('caption', ''),
            'post_text': video.get('caption', ''),
            'post_url': video.get('post_url'),
            'timestamp': video.get('timestamp'),
            'created_at': video.get('timestamp'),
            'likes_count': video.get('likes', 0),
            'comments_count': video.get('comments', 0),
            'shares_count': video.get('shares', 0),
            'views_count': video.get('views', 0),
            'type': 'tiktok_video',
            'hashtags': video.get('hashtags', []),
            'mentions': video.get('mentions', []),
        })
    
    try:
        results = analyze_posts_batch("TikTok", videos_data)
        print(f"✅ TikTok intelligent analysis complete: {len(results)} videos")
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        import traceback
        print(f"❌ TikTok intelligent analysis failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        error_str = str(e).lower()
        if any(word in error_str for word in ["expired", "invalid", "authentication", "quota", "rate-limit"]):
            send_api_expiry_alert(
                subject="VisaGuardAI: AI Analysis Alert",
                body=f"TikTok intelligent analysis error: {e}",
                to_email="syedawaisalishah46@gmail.com"
            )
        
        # Return fallback error state
        fallback_analysis = []
        for video in videos:
            fallback_analysis.append({
                "post": video["caption"],
                "post_data": {
                    'caption': video["caption"],
                    'data_unavailable': True,
                },
                "TikTok": {
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


if __name__ == "__main__":
    # Test the scraper
    username = "charlidamelio"  # Sample TikTok account
    videos_desired = 5
    
    print(f"Testing TikTok scraper with @{username}...")
    result = analyze_tiktok_profile(username, videos_desired)
    print("Analysis result:")
    print(result[:500] if len(result) > 500 else result)

