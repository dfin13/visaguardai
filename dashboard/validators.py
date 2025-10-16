"""
Account validation functions for pre-scrape checks.
Performs lightweight 1-post test scrapes to verify accounts exist and are public.
"""
import os
from apify_client import ApifyClient
from django.conf import settings

# Get API key
APIFY_API_TOKEN = os.getenv('APIFY_API_KEY') or getattr(settings, 'APIFY_API_KEY', None)
if not APIFY_API_TOKEN:
    from dashboard.models import Config
    config = Config.objects.first()
    if config:
        APIFY_API_TOKEN = config.Apify_api_key

apify_client = ApifyClient(APIFY_API_TOKEN)


def validate_instagram_account(username):
    """
    Validate Instagram account exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        print(f"🔍 Validating Instagram account: @{username}")
        
        # Run minimal scrape (1 post only)
        run_input = {
            "username": [username],
            "resultsLimit": 1,  # Only get 1 post for validation
        }
        
        run = apify_client.actor("apify/instagram-post-scraper").call(
            run_input=run_input,
            timeout_secs=30  # Quick validation
        )
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        if not results or len(results) == 0:
            return False, f"Instagram account @{username} is private or doesn't exist."
        
        print(f"✅ Instagram account @{username} validated successfully")
        return True, f"Successfully connected to Instagram (@{username})!"
        
    except Exception as e:
        print(f"❌ Instagram validation error for @{username}: {e}")
        return False, f"Unable to access Instagram account @{username}. Please check the username."


def validate_linkedin_account(username):
    """
    Validate LinkedIn account exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        print(f"🔍 Validating LinkedIn account: {username}")
        
        # Run minimal scrape (1 post only)
        run_input = {
            "startUrls": [f"https://www.linkedin.com/in/{username}/"],
            "maxPosts": 1,  # Only get 1 post for validation
        }
        
        run = apify_client.actor("apimaestro/linkedin-profile-posts").call(
            run_input=run_input,
            timeout_secs=30
        )
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        # Check if we got any data (even 0 posts is OK if profile exists)
        if not results:
            return False, f"LinkedIn profile '{username}' is private or doesn't exist."
        
        # Check for common error indicators
        first_item = results[0]
        if isinstance(first_item, dict):
            # If we got profile data, it's valid
            if 'text' in first_item or 'postText' in first_item or 'post_text' in first_item:
                print(f"✅ LinkedIn account {username} validated successfully")
                return True, f"Successfully connected to LinkedIn ({username})!"
            # Profile exists but no posts (still valid)
            if 'error' not in str(first_item).lower():
                print(f"✅ LinkedIn account {username} validated (no posts)")
                return True, f"Successfully connected to LinkedIn ({username})!"
        
        return False, f"LinkedIn profile '{username}' is private or doesn't exist."
        
    except Exception as e:
        print(f"❌ LinkedIn validation error for {username}: {e}")
        return False, f"Unable to access LinkedIn profile '{username}'. Please check the username."


def validate_twitter_account(username):
    """
    Validate Twitter/X account exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        print(f"🔍 Validating Twitter account: @{username}")
        
        # Run minimal scrape (1 tweet only)
        run_input = {
            "searchTerms": [f"from:{username}"],
            "maxItems": 1,  # Only get 1 tweet for validation
            "addUserInfo": False,
            "queryType": "Latest"
        }
        
        run = apify_client.actor("kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest").call(
            run_input=run_input,
            timeout_secs=30
        )
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        # Filter out mock tweets (returned when account doesn't exist)
        real_results = [r for r in results if not (isinstance(r, dict) and r.get('type') == 'mock_tweet')]
        
        if not real_results or len(real_results) == 0:
            return False, f"Twitter account @{username} is private, suspended, or doesn't exist."
        
        print(f"✅ Twitter account @{username} validated successfully")
        return True, f"Successfully connected to Twitter/X (@{username})!"
        
    except Exception as e:
        print(f"❌ Twitter validation error for @{username}: {e}")
        return False, f"Unable to access Twitter account @{username}. Please check the username."


def validate_facebook_account(username):
    """
    Validate Facebook account/page exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        print(f"🔍 Validating Facebook account: {username}")
        
        # Run minimal scrape (1 post only)
        run_input = {
            "startUrls": [f"https://www.facebook.com/{username}"],
            "maxPosts": 1,  # Only get 1 post for validation
        }
        
        run = apify_client.actor("apify/facebook-posts-scraper").call(
            run_input=run_input,
            timeout_secs=30
        )
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        if not results or len(results) == 0:
            return False, f"Facebook page '{username}' is private or doesn't exist."
        
        # Check for error indicators
        first_item = results[0]
        if isinstance(first_item, dict) and 'error' in str(first_item).lower():
            return False, f"Facebook page '{username}' is not accessible."
        
        print(f"✅ Facebook account {username} validated successfully")
        return True, f"Successfully connected to Facebook ({username})!"
        
    except Exception as e:
        print(f"❌ Facebook validation error for {username}: {e}")
        return False, f"Unable to access Facebook page '{username}'. Please check the username."


def validate_all_accounts(instagram_username=None, linkedin_username=None, 
                         twitter_username=None, facebook_username=None):
    """
    Validate all provided accounts before starting analysis.
    Returns: (bool, dict) - (all_valid, results)
    
    results format: {
        'instagram': {'valid': bool, 'message': str},
        'linkedin': {'valid': bool, 'message': str},
        'twitter': {'valid': bool, 'message': str},
        'facebook': {'valid': bool, 'message': str},
    }
    """
    results = {}
    all_valid = True
    
    # Validate each platform if username provided
    if instagram_username:
        is_valid, message = validate_instagram_account(instagram_username)
        results['instagram'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    if linkedin_username:
        is_valid, message = validate_linkedin_account(linkedin_username)
        results['linkedin'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    if twitter_username:
        is_valid, message = validate_twitter_account(twitter_username)
        results['twitter'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    if facebook_username:
        is_valid, message = validate_facebook_account(facebook_username)
        results['facebook'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    return all_valid, results

