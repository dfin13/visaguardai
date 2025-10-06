"""
Utility functions for checking social media account accessibility
and handling private/inaccessible accounts without fabricating content.
"""

def create_inaccessible_account_response(platform, username, reason="private or unavailable"):
    """
    Create a standardized response for inaccessible accounts.
    
    Args:
        platform (str): The social media platform (Instagram, Twitter, etc.)
        username (str): The username that was attempted to be accessed
        reason (str): The reason the account is inaccessible
    
    Returns:
        dict: Standardized response indicating account is inaccessible
    """
    return {
        platform.lower(): {
            "account_status": "inaccessible",
            "username": username,
            "message": f"⚠️ This account is {reason}. No content analyzed.",
            "posts_analyzed": 0,
            "analysis": {
                "content_reinforcement": {
                    "status": "unavailable",
                    "recommendation": None,
                    "reason": f"Account {reason} - no content to analyze"
                },
                "content_suppression": {
                    "status": "unavailable", 
                    "recommendation": None,
                    "reason": f"Account {reason} - no content to analyze"
                },
                "content_flag": {
                    "status": "unavailable",
                    "recommendation": None,
                    "reason": f"Account {reason} - no content to analyze"
                },
                "risk_score": 0
            }
        }
    }


def is_account_private_error(error_message):
    """
    Check if an error message indicates the account is private or inaccessible.
    
    Args:
        error_message (str): The error message from the scraping attempt
    
    Returns:
        bool: True if the error indicates a private/inaccessible account
    """
    error_lower = str(error_message).lower()
    
    private_indicators = [
        "private",
        "inaccessible", 
        "not found",
        "does not exist",
        "account not found",
        "profile not found",
        "user not found",
        "page not found",
        "access denied",
        "permission denied",
        "blocked",
        "restricted",
        "unavailable",
        "no posts found",
        "no data found",
        "empty profile",
        "profile is private",
        "account is private"
    ]
    
    return any(indicator in error_lower for indicator in private_indicators)


def log_account_access_attempt(platform, username, success, error_message=None):
    """
    Log account access attempts for debugging and monitoring.
    
    Args:
        platform (str): The social media platform
        username (str): The username attempted
        success (bool): Whether the access was successful
        error_message (str): Error message if access failed
    """
    status = "SUCCESS" if success else "FAILED"
    print(f"[ACCOUNT_CHECK] {platform} @{username}: {status}")
    
    if not success and error_message:
        print(f"[ACCOUNT_CHECK] Error: {error_message}")
        
        if is_account_private_error(error_message):
            print(f"[ACCOUNT_CHECK] Account appears to be private/inaccessible")


def check_scraping_result(posts_data, platform, username):
    """
    Check if scraping returned valid data or if account is inaccessible.
    
    Args:
        posts_data (list): List of posts/tweets/content from scraping
        platform (str): The social media platform
        username (str): The username that was scraped
    
    Returns:
        tuple: (is_accessible, response_data)
            - is_accessible (bool): Whether account is accessible
            - response_data (dict): Either real data or inaccessible response
    """
    if not posts_data or len(posts_data) == 0:
        log_account_access_attempt(platform, username, False, "No posts found")
        return False, create_inaccessible_account_response(platform, username, "has no accessible content")
    
    # Check if posts contain actual content (not just empty strings)
    valid_posts = [post for post in posts_data if post and str(post).strip()]
    
    if not valid_posts:
        log_account_access_attempt(platform, username, False, "No valid posts found")
        return False, create_inaccessible_account_response(platform, username, "has no accessible content")
    
    log_account_access_attempt(platform, username, True)
    return True, {"posts": valid_posts, "count": len(valid_posts)}

