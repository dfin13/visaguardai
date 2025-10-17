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
            timeout_secs=45  # Increased timeout
        )
        
        # Check if the run completed successfully
        if run.get("status") == "FAILED":
            return False, f"Instagram account @{username} is private or doesn't exist."
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        # If scraper ran successfully but returned no results, the account might be private or have no posts
        # But if it returned ANY data, consider it valid (even if it's metadata)
        if results and len(results) > 0:
            print(f"✅ Instagram account @{username} validated successfully ({len(results)} item(s) found)")
            return True, f"Successfully connected to Instagram (@{username})!"
        
        # No results at all - likely private or doesn't exist
        print(f"❌ Instagram validation failed for @{username}: No data returned")
        return False, f"Instagram account @{username} is private or doesn't exist."
        
    except Exception as e:
        error_str = str(e).lower()
        # Check if it's a genuine error (not found, private, etc.)
        if any(err in error_str for err in ['not found', 'private', 'suspended', 'deleted', 'invalid']):
            print(f"❌ Instagram validation error for @{username}: {e}")
            return False, f"Instagram account @{username} is private or doesn't exist."
        # Other errors might be temporary - allow them
        print(f"⚠️  Instagram validation warning for @{username}: {e} (allowing anyway)")
        return True, f"Instagram account @{username} connected (validation inconclusive)."


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
        
        # Check if we got any data
        if not results or len(results) == 0:
            return False, f"LinkedIn profile '{username}' is private or doesn't exist."
        
        # Check for valid post data
        first_item = results[0]
        if not isinstance(first_item, dict):
            return False, f"LinkedIn profile '{username}' returned invalid data."
        
        # Check for actual post fields (indicates valid profile with posts)
        if 'text' in first_item or 'postText' in first_item or 'post_text' in first_item:
            print(f"✅ LinkedIn account {username} validated successfully")
            return True, f"Successfully connected to LinkedIn ({username})!"
        
        # Check for profile-level fields (indicates profile exists even without posts)
        profile_indicators = ['profileUrl', 'profile_url', 'url', 'actorRunUrl']
        if any(indicator in first_item for indicator in profile_indicators):
            # Additional check: make sure it's not an error response
            error_indicators = ['error', 'failed', 'not found', 'does not exist', 'unavailable']
            item_str = str(first_item).lower()
            if not any(error in item_str for error in error_indicators):
                print(f"✅ LinkedIn account {username} validated (profile exists)")
                return True, f"Successfully connected to LinkedIn ({username})!"
        
        print(f"❌ LinkedIn validation failed for {username}: No valid profile or post data found")
        print(f"   First item keys: {list(first_item.keys())}")
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
        
        # Try both page and profile URL formats
        url = f"https://www.facebook.com/{username}/"  # Add trailing slash
        
        # Run minimal scrape (1 post only)
        run_input = {
            "startUrls": [{"url": url}],  # Use object format instead of string
            "maxPosts": 1,  # Only get 1 post for validation
        }
        
        run = apify_client.actor("apify/facebook-posts-scraper").call(
            run_input=run_input,
            timeout_secs=45  # Increased timeout
        )
        
        # Check if the run completed successfully
        if run.get("status") == "FAILED":
            return False, f"Facebook page '{username}' is private or doesn't exist."
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        # If scraper ran successfully and returned ANY data, consider it valid
        if results and len(results) > 0:
            print(f"✅ Facebook account {username} validated successfully ({len(results)} item(s) found)")
            return True, f"Successfully connected to Facebook ({username})!"
        
        # No results - might be private or have no posts
        print(f"❌ Facebook validation failed for {username}: No data returned")
        return False, f"Facebook page '{username}' is private or doesn't exist."
        
    except Exception as e:
        error_str = str(e).lower()
        # Check for genuine errors
        if any(err in error_str for err in ['not found', 'private', 'invalid', 'unavailable', 'not valid', 'does not exist']):
            print(f"❌ Facebook validation error for {username}: {e}")
            return False, f"Unable to access Facebook page '{username}'. Please check the username."
        # Other errors might be temporary - allow them
        print(f"⚠️  Facebook validation warning for {username}: {e} (allowing anyway)")
        return True, f"Facebook page '{username}' connected (validation inconclusive)."


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

