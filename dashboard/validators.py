"""
Account validation functions for pre-scrape checks.
Performs lightweight 1-post test scrapes to verify accounts exist and are public.
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from apify_client import ApifyClient
from django.conf import settings
from django.core.cache import cache

# Get API key
APIFY_API_TOKEN = os.getenv('APIFY_API_KEY') or getattr(settings, 'APIFY_API_KEY', None)
if not APIFY_API_TOKEN:
    from dashboard.models import Config
    config = Config.objects.first()
    if config:
        APIFY_API_TOKEN = config.Apify_api_key

apify_client = ApifyClient(APIFY_API_TOKEN)

# Validation cache settings (5 minutes)
VALIDATION_CACHE_TIMEOUT = 300  # 5 minutes

def get_validation_cache_key(platform, username):
    """Generate cache key for validation results."""
    return f"validation_{platform}_{username.lower()}"


def validate_instagram_account(username):
    """
    Validate Instagram account exists and is public.
    Uses caching for faster repeated validations.
    Returns: (bool, str) - (is_valid, message)
    """
    # Check cache first
    cache_key = get_validation_cache_key('instagram', username)
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"⚡ Instagram validation from cache: @{username}")
        return cached_result
    
    try:
        print(f"🔍 Validating Instagram account: @{username}")
        start_time = time.time()
        
        # Run minimal scrape (1 post only)
        run_input = {
            "username": [username],
            "resultsLimit": 1,  # Only get 1 post for validation
        }
        
        run = apify_client.actor("apify/instagram-post-scraper").call(
            run_input=run_input,
            timeout_secs=15  # Faster validation
        )
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        if not results or len(results) == 0:
            return False, f"Instagram account @{username} is private or doesn't exist."
        
        # Additional validation: check if first item has expected fields
        first_item = results[0]
        if not isinstance(first_item, dict):
            return False, f"Instagram account @{username} returned invalid data."
        
        # Check for post indicators (caption, url, likes, etc.)
        post_indicators = ['caption', 'url', 'likesCount', 'likes_count', 'ownerUsername', 'owner_username']
        if not any(indicator in first_item for indicator in post_indicators):
            print(f"❌ Instagram validation failed for @{username}: No valid post data")
            print(f"   First item keys: {list(first_item.keys())}")
            result = (False, f"Instagram account @{username} is private or doesn't exist.")
            cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
            return result
        
        elapsed = time.time() - start_time
        print(f"✅ Instagram account @{username} validated successfully ({elapsed:.1f}s)")
        result = (True, f"Successfully connected to Instagram (@{username})!")
        cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Instagram validation error for @{username}: {e} ({elapsed:.1f}s)")
        result = (False, f"Unable to access Instagram account @{username}. Please check the username.")
        cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
        return result


def validate_linkedin_account(username):
    """
    Validate LinkedIn account exists and is public.
    Uses caching for faster repeated validations.
    Returns: (bool, str) - (is_valid, message)
    """
    # Check cache first
    cache_key = get_validation_cache_key('linkedin', username)
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"⚡ LinkedIn validation from cache: {username}")
        return cached_result
    
    try:
        print(f"🔍 Validating LinkedIn account: {username}")
        start_time = time.time()
        
        # Run minimal scrape (1 post only)
        run_input = {
            "startUrls": [f"https://www.linkedin.com/in/{username}/"],
            "maxPosts": 1,  # Only get 1 post for validation
        }
        
        run = apify_client.actor("apimaestro/linkedin-profile-posts").call(
            run_input=run_input,
            timeout_secs=15
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
            elapsed = time.time() - start_time
            print(f"✅ LinkedIn account {username} validated successfully ({elapsed:.1f}s)")
            result = (True, f"Successfully connected to LinkedIn ({username})!")
            cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
            return result
        
        # Check for profile-level fields (indicates profile exists even without posts)
        profile_indicators = ['profileUrl', 'profile_url', 'url', 'actorRunUrl']
        if any(indicator in first_item for indicator in profile_indicators):
            # Additional check: make sure it's not an error response
            error_indicators = ['error', 'failed', 'not found', 'does not exist', 'unavailable']
            item_str = str(first_item).lower()
            if not any(error in item_str for error in error_indicators):
                elapsed = time.time() - start_time
                print(f"✅ LinkedIn account {username} validated (profile exists) ({elapsed:.1f}s)")
                result = (True, f"Successfully connected to LinkedIn ({username})!")
                cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
                return result
        
        print(f"❌ LinkedIn validation failed for {username}: No valid profile or post data found")
        print(f"   First item keys: {list(first_item.keys())}")
        result = (False, f"LinkedIn profile '{username}' is private or doesn't exist.")
        cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ LinkedIn validation error for {username}: {e} ({elapsed:.1f}s)")
        result = (False, f"Unable to access LinkedIn profile '{username}'. Please check the username.")
        cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
        return result


def validate_twitter_account(username):
    """
    Validate Twitter/X account exists and is public.
    Uses caching for faster repeated validations.
    Returns: (bool, str) - (is_valid, message)
    """
    # Check cache first
    cache_key = get_validation_cache_key('twitter', username)
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"⚡ Twitter validation from cache: @{username}")
        return cached_result
    
    try:
        print(f"🔍 Validating Twitter account: @{username}")
        start_time = time.time()
        
        # Run minimal scrape (1 tweet only)
        run_input = {
            "searchTerms": [f"from:{username}"],
            "maxItems": 1,  # Only get 1 tweet for validation
            "addUserInfo": False,
            "queryType": "Latest"
        }
        
        run = apify_client.actor("kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest").call(
            run_input=run_input,
            timeout_secs=15
        )
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        # Filter out mock tweets (returned when account doesn't exist)
        real_results = [r for r in results if not (isinstance(r, dict) and r.get('type') == 'mock_tweet')]
        
        if not real_results or len(real_results) == 0:
            result = (False, f"Twitter account @{username} is private, suspended, or doesn't exist.")
            cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
            return result
        
        elapsed = time.time() - start_time
        print(f"✅ Twitter account @{username} validated successfully ({elapsed:.1f}s)")
        result = (True, f"Successfully connected to Twitter/X (@{username})!")
        cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Twitter validation error for @{username}: {e} ({elapsed:.1f}s)")
        result = (False, f"Unable to access Twitter account @{username}. Please check the username.")
        cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
        return result


def validate_facebook_account(username):
    """
    Validate Facebook account/page exists and is public.
    Uses caching for faster repeated validations.
    Returns: (bool, str) - (is_valid, message)
    """
    # Check cache first
    cache_key = get_validation_cache_key('facebook', username)
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"⚡ Facebook validation from cache: {username}")
        return cached_result
    
    try:
        print(f"🔍 Validating Facebook account: {username}")
        start_time = time.time()
        
        # Run minimal scrape (1 post only)
        run_input = {
            "startUrls": [f"https://www.facebook.com/{username}"],
            "maxPosts": 1,  # Only get 1 post for validation
        }
        
        run = apify_client.actor("apify/facebook-posts-scraper").call(
            run_input=run_input,
            timeout_secs=15
        )
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        if not results or len(results) == 0:
            return False, f"Facebook page '{username}' is private or doesn't exist."
        
        # Check for valid post data
        first_item = results[0]
        if not isinstance(first_item, dict):
            return False, f"Facebook page '{username}' returned invalid data."
        
        # Check for error indicators first
        error_indicators = ['error', 'failed', 'not found', 'does not exist', 'unavailable', 'invalid']
        item_str = str(first_item).lower()
        if any(error in item_str for error in error_indicators):
            result = (False, f"Facebook page '{username}' is not accessible.")
            cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
            return result
        
        # Check for actual post fields (indicates valid page with posts)
        post_indicators = ['text', 'post_text', 'postText', 'caption', 'message', 'post_url']
        if any(indicator in first_item for indicator in post_indicators):
            elapsed = time.time() - start_time
            print(f"✅ Facebook account {username} validated successfully ({elapsed:.1f}s)")
            result = (True, f"Successfully connected to Facebook ({username})!")
            cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
            return result
        
        # If no post fields found, it's likely invalid
        print(f"❌ Facebook validation failed for {username}: No valid post data found")
        print(f"   First item keys: {list(first_item.keys())}")
        result = (False, f"Facebook page '{username}' is private or doesn't exist.")
        cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Facebook validation error for {username}: {e} ({elapsed:.1f}s)")
        result = (False, f"Unable to access Facebook page '{username}'. Please check the username.")
        cache.set(cache_key, result, VALIDATION_CACHE_TIMEOUT)
        return result


def validate_all_accounts(instagram_username=None, linkedin_username=None, 
                         twitter_username=None, facebook_username=None):
    """
    Validate all provided accounts before starting analysis.
    Uses parallel execution for speed (all validations run simultaneously).
    
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
    
    # Build validation tasks
    validation_tasks = []
    if instagram_username:
        validation_tasks.append(('instagram', validate_instagram_account, instagram_username))
    if linkedin_username:
        validation_tasks.append(('linkedin', validate_linkedin_account, linkedin_username))
    if twitter_username:
        validation_tasks.append(('twitter', validate_twitter_account, twitter_username))
    if facebook_username:
        validation_tasks.append(('facebook', validate_facebook_account, facebook_username))
    
    # Run all validations in parallel
    if validation_tasks:
        print(f"\n🚀 Starting parallel validation for {len(validation_tasks)} platform(s)...")
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks
            future_to_platform = {
                executor.submit(validator_func, username): platform
                for platform, validator_func, username in validation_tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    is_valid, message = future.result()
                    results[platform] = {'valid': is_valid, 'message': message}
                    if not is_valid:
                        all_valid = False
                    print(f"   ✓ {platform.capitalize()} validation completed: {'✅' if is_valid else '❌'}")
                except Exception as e:
                    print(f"   ❌ {platform.capitalize()} validation failed with exception: {e}")
                    results[platform] = {'valid': False, 'message': f"Validation error: {str(e)}"}
                    all_valid = False
        
        print(f"✅ All validations complete! Total: {len(validation_tasks)} platform(s)\n")
    
    return all_valid, results

