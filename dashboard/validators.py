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

# Ensure API token is available
if not APIFY_API_TOKEN:
    print("❌ No APIFY_API_TOKEN found - validation will fail")

apify_client = ApifyClient(APIFY_API_TOKEN) if APIFY_API_TOKEN else None


def validate_instagram_account(username):
    """
    Validate Instagram account exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        if not apify_client:
            print(f"❌ Apify client not configured for Instagram validation")
            return False, "Validation service unavailable"
            
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
        if not apify_client:
            print(f"❌ Apify client not configured for LinkedIn validation")
            return False, "Validation service unavailable"
            
        print(f"🔍 Validating LinkedIn account: {username}")
        
        # Run minimal scrape (1 post only)
        run_input = {
            "startUrls": [f"https://www.linkedin.com/in/{username}/"],
            "maxPosts": 1,  # Only get 1 post for validation
        }
        
        run = apify_client.actor("apimaestro/linkedin-profile-posts").call(
            run_input=run_input,
            timeout_secs=45  # Increased timeout
        )
        
        # Check if the run completed successfully
        if run.get("status") == "FAILED":
            return False, f"LinkedIn profile '{username}' is private or doesn't exist."
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        # If scraper ran successfully and returned ANY data, consider it valid
        if results and len(results) > 0:
            print(f"✅ LinkedIn account {username} validated successfully ({len(results)} item(s) found)")
            return True, f"Successfully connected to LinkedIn ({username})!"
        
        # No results - might be private or have no posts
        print(f"❌ LinkedIn validation failed for {username}: No data returned")
        return False, f"LinkedIn profile '{username}' is private or doesn't exist."
        
    except Exception as e:
        error_str = str(e).lower()
        # Check for genuine errors
        if any(err in error_str for err in ['not found', 'private', 'invalid', 'unavailable', 'does not exist']):
            print(f"❌ LinkedIn validation error for {username}: {e}")
            return False, f"Unable to access LinkedIn profile '{username}'. Please check the username."
        # Other errors might be temporary - allow them
        print(f"⚠️  LinkedIn validation warning for {username}: {e} (allowing anyway)")
        return True, f"LinkedIn profile '{username}' connected (validation inconclusive)."


def validate_twitter_account(username):
    """
    Validate Twitter/X account exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        if not apify_client:
            print(f"❌ Apify client not configured for Twitter validation")
            return False, "Validation service unavailable"
            
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
            timeout_secs=45  # Increased timeout
        )
        
        # Check if the run completed successfully
        if run.get("status") == "FAILED":
            return False, f"Twitter account @{username} is private, suspended, or doesn't exist."
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        # Filter out mock tweets (returned when account doesn't exist)
        real_results = [r for r in results if not (isinstance(r, dict) and r.get('type') == 'mock_tweet')]
        
        # If scraper ran successfully and returned ANY real data, consider it valid
        if real_results and len(real_results) > 0:
            print(f"✅ Twitter account @{username} validated successfully ({len(real_results)} tweet(s) found)")
            return True, f"Successfully connected to Twitter/X (@{username})!"
        
        # No real results - might be private, suspended, or doesn't exist
        print(f"❌ Twitter validation failed for @{username}: No tweets found")
        return False, f"Twitter account @{username} is private, suspended, or doesn't exist."
        
    except Exception as e:
        error_str = str(e).lower()
        # Check for genuine errors
        if any(err in error_str for err in ['not found', 'private', 'suspended', 'invalid', 'unavailable', 'does not exist']):
            print(f"❌ Twitter validation error for @{username}: {e}")
            return False, f"Unable to access Twitter account @{username}. Please check the username."
        # Other errors might be temporary - allow them
        print(f"⚠️  Twitter validation warning for @{username}: {e} (allowing anyway)")
        return True, f"Twitter account @{username} connected (validation inconclusive)."


def validate_facebook_account(username):
    """
    Validate Facebook account/page exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        if not apify_client:
            print(f"❌ Apify client not configured for Facebook validation")
            return False, "Validation service unavailable"
            
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
    has_any_accounts = False
    
    # Validate each platform if username provided
    if instagram_username:
        has_any_accounts = True
        is_valid, message = validate_instagram_account(instagram_username)
        results['instagram'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    if linkedin_username:
        has_any_accounts = True
        is_valid, message = validate_linkedin_account(linkedin_username)
        results['linkedin'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    if twitter_username:
        has_any_accounts = True
        is_valid, message = validate_twitter_account(twitter_username)
        results['twitter'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    if facebook_username:
        has_any_accounts = True
        is_valid, message = validate_facebook_account(facebook_username)
        results['facebook'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    # If no accounts provided, that's invalid
    if not has_any_accounts:
        all_valid = False
    
    return all_valid, results


def validate_instagram_account(username):
    """
    Validate Instagram account exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        if not apify_client:
            print(f"❌ Apify client not configured for Instagram validation")
            return False, "Validation service unavailable"
            
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
        if not apify_client:
            print(f"❌ Apify client not configured for LinkedIn validation")
            return False, "Validation service unavailable"
            
        print(f"🔍 Validating LinkedIn account: {username}")
        
        # Run minimal scrape (1 post only)
        run_input = {
            "startUrls": [f"https://www.linkedin.com/in/{username}/"],
            "maxPosts": 1,  # Only get 1 post for validation
        }
        
        run = apify_client.actor("apimaestro/linkedin-profile-posts").call(
            run_input=run_input,
            timeout_secs=45  # Increased timeout
        )
        
        # Check if the run completed successfully
        if run.get("status") == "FAILED":
            return False, f"LinkedIn profile '{username}' is private or doesn't exist."
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        # If scraper ran successfully and returned ANY data, consider it valid
        if results and len(results) > 0:
            print(f"✅ LinkedIn account {username} validated successfully ({len(results)} item(s) found)")
            return True, f"Successfully connected to LinkedIn ({username})!"
        
        # No results - might be private or have no posts
        print(f"❌ LinkedIn validation failed for {username}: No data returned")
        return False, f"LinkedIn profile '{username}' is private or doesn't exist."
        
    except Exception as e:
        error_str = str(e).lower()
        # Check for genuine errors
        if any(err in error_str for err in ['not found', 'private', 'invalid', 'unavailable', 'does not exist']):
            print(f"❌ LinkedIn validation error for {username}: {e}")
            return False, f"Unable to access LinkedIn profile '{username}'. Please check the username."
        # Other errors might be temporary - allow them
        print(f"⚠️  LinkedIn validation warning for {username}: {e} (allowing anyway)")
        return True, f"LinkedIn profile '{username}' connected (validation inconclusive)."


def validate_twitter_account(username):
    """
    Validate Twitter/X account exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        if not apify_client:
            print(f"❌ Apify client not configured for Twitter validation")
            return False, "Validation service unavailable"
            
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
            timeout_secs=45  # Increased timeout
        )
        
        # Check if the run completed successfully
        if run.get("status") == "FAILED":
            return False, f"Twitter account @{username} is private, suspended, or doesn't exist."
        
        # Get results
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
        
        # Filter out mock tweets (returned when account doesn't exist)
        real_results = [r for r in results if not (isinstance(r, dict) and r.get('type') == 'mock_tweet')]
        
        # If scraper ran successfully and returned ANY real data, consider it valid
        if real_results and len(real_results) > 0:
            print(f"✅ Twitter account @{username} validated successfully ({len(real_results)} tweet(s) found)")
            return True, f"Successfully connected to Twitter/X (@{username})!"
        
        # No real results - might be private, suspended, or doesn't exist
        print(f"❌ Twitter validation failed for @{username}: No tweets found")
        return False, f"Twitter account @{username} is private, suspended, or doesn't exist."
        
    except Exception as e:
        error_str = str(e).lower()
        # Check for genuine errors
        if any(err in error_str for err in ['not found', 'private', 'suspended', 'invalid', 'unavailable', 'does not exist']):
            print(f"❌ Twitter validation error for @{username}: {e}")
            return False, f"Unable to access Twitter account @{username}. Please check the username."
        # Other errors might be temporary - allow them
        print(f"⚠️  Twitter validation warning for @{username}: {e} (allowing anyway)")
        return True, f"Twitter account @{username} connected (validation inconclusive)."


def validate_facebook_account(username):
    """
    Validate Facebook account/page exists and is public.
    Returns: (bool, str) - (is_valid, message)
    """
    try:
        if not apify_client:
            print(f"❌ Apify client not configured for Facebook validation")
            return False, "Validation service unavailable"
            
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
    has_any_accounts = False
    
    # Validate each platform if username provided
    if instagram_username:
        has_any_accounts = True
        is_valid, message = validate_instagram_account(instagram_username)
        results['instagram'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    if linkedin_username:
        has_any_accounts = True
        is_valid, message = validate_linkedin_account(linkedin_username)
        results['linkedin'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    if twitter_username:
        has_any_accounts = True
        is_valid, message = validate_twitter_account(twitter_username)
        results['twitter'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    if facebook_username:
        has_any_accounts = True
        is_valid, message = validate_facebook_account(facebook_username)
        results['facebook'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            all_valid = False
    
    # If no accounts provided, that's invalid
    if not has_any_accounts:
        all_valid = False
    
    return all_valid, results
























