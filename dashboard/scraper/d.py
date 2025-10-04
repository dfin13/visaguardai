from apify_client import ApifyClient

def get_linkedin_posts(username=None):
    """
    Get LinkedIn posts using Apify scraper
    
    Args:
        username (str): Optional LinkedIn username to filter posts
    """
    # Initialize the ApifyClient with your API token
    client = ApifyClient("apify_api_NDeIB7HUn3ZHOFuXLoQzlx7AZscr3u4Eu29r")

    # Prepare Actor input
    actor_input = {
        "startUrls": [{"url": f"https://www.linkedin.com/in/{username}"}] if username else [],
        "maxPosts": 10,
    }

    # Run the Actor task and wait for it to finish
    try:
        run = client.task("imAuoa5mvuLZdpq48").call(task_input=actor_input)
    except TypeError as e:
        print(f"Error calling Apify task: {e}")
        return
    except Exception as e:
        print(f"General error: {e}")
        return

    # Fetch and print Actor task results from the run's dataset
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        # Extract data based on the actual structure from your output
        username = item.get("author", {}).get("username") if item.get("author") else None
        profile_url = item.get("author", {}).get("profileUrl") if item.get("author") else None
        post_text = item.get("text")
        
        print("Username:", username)
        print("Profile URL:", profile_url)
        print("Post:", post_text)
        print("-" * 50)
        
        # You can also return the data or process it further
        yield {
            "username": username,
            "profile_url": profile_url,
            "post_text": post_text,
            "full_data": item  # Include the full item data for reference
        }

# Example usage:
if __name__ == "__main__":
    # Call without username to get general posts
    posts = get_linkedin_posts()
    for post in posts:
        print(f"User: {post['username']}")
        print(f"Post: {post['post_text'][:100]}...")  # Show first 100 chars
        print()
    
    # Or call with a specific username
    posts = get_linkedin_posts("syedasimbacha")









    