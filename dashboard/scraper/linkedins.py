# import undetected_chromedriver as uc
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
# import time, json
# from datetime import datetime
# import os
# import pickle
# import google.generativeai as genai

# COOKIE_FILE = "linkedin_cookies.pkl"

# class LinkedInAuthenticator:
#     def __init__(self, username, password):
#         self.username = username
#         self.password = password

#         chrome_options = Options()
#         chrome_options.add_argument("--headless=new")
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_argument("window-size=1920,1080")
#         chrome_options.add_argument(
#             "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
#         )

#         self.driver = uc.Chrome(options=chrome_options)

#     def login(self):
#         if os.path.exists(COOKIE_FILE):
#             self.driver.get("https://www.linkedin.com/")
#             for cookie in pickle.load(open(COOKIE_FILE, "rb")):
#                 self.driver.add_cookie(cookie)
#             self.driver.refresh()
#             time.sleep(3)
#             # Screenshot after loading cookies
#             self.driver.save_screenshot("linkedin_after_cookie_login.png")
#             print("[INFO] Screenshot saved: linkedin_after_cookie_login.png")
#             # Check if login was successful
#             if "feed" not in self.driver.current_url:
#                 print("[WARNING] Not redirected to feed after cookie login. Might need to re-login.")
#             return self.driver

#         self.driver.get("https://www.linkedin.com/login")
#         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(self.username)
#         self.driver.find_element(By.ID, "password").send_keys(self.password)
#         self.driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
#         time.sleep(5)
#         # Screenshot after fresh login
#         self.driver.save_screenshot("linkedin_after_fresh_login.png")
#         print("[INFO] Screenshot saved: linkedin_after_fresh_login.png")
#         # Check if login was successful
#         if "feed" not in self.driver.current_url:
#             print("[WARNING] Not redirected to feed after fresh login. Login may have failed or CAPTCHA triggered.")
#         pickle.dump(self.driver.get_cookies(), open(COOKIE_FILE, "wb"))
#         return self.driver


# class ProfileNavigator:
#     def __init__(self, driver):
#         self.driver = driver

#     def navigate_to_profile(self, linkedin_username):
#         profile_url = f"https://www.linkedin.com/in/{linkedin_username}/recent-activity/all/"
#         self.driver.get(profile_url)
#         time.sleep(3)
#         # Screenshot after navigating to profile
#         filename = f"linkedin_profile_{linkedin_username}.png"
#         self.driver.save_screenshot(filename)
#         print(f"[INFO] Screenshot saved: {filename}")


# class PostScroller:
#     def __init__(self, driver):
#         self.driver = driver

#     def scroll_for_posts(self, limit=10):
#         last_height = self.driver.execute_script("return document.body.scrollHeight")
#         while True:
#             soup = BeautifulSoup(self.driver.page_source, 'html.parser')
#             posts = soup.find_all("div", {"class": "feed-shared-update-v2"})
#             if len(posts) >= limit:
#                 break
#             self.driver.execute_script("window.scrollBy(0, 800);")
#             time.sleep(1.5)
#             new_height = self.driver.execute_script("return document.body.scrollHeight")
#             if new_height == last_height:
#                 break
#             last_height = new_height


# class PostExtractor:
#     def __init__(self, driver):
#         self.driver = driver

#     def extract_posts(self, limit=10):
#         soup = BeautifulSoup(self.driver.page_source, 'html.parser')
#         posts = []
#         # TODO: Update the selector below if LinkedIn changes their HTML structure!
#         containers = soup.find_all("div", {"class": "feed-shared-update-v2"})
#         if not containers:
#             print("[WARNING] No posts found. Saving HTML and screenshot for debugging.")
#             with open("linkedin_no_posts.html", "w", encoding="utf-8") as f:
#                 f.write(self.driver.page_source)
#             self.driver.save_screenshot("linkedin_no_posts.png")
#             print("[INFO] Saved HTML: linkedin_no_posts.html and screenshot: linkedin_no_posts.png")
#         for container in containers[:limit]:
#             text = container.get_text(separator=" ", strip=True)
#             posts.append(text)
#         return posts


# class LinkedInPostAnalyzer:
#     def __init__(self, linkedin_email, linkedin_password, gemini_api_key):
#         self.linkedin_email = linkedin_email
#         self.linkedin_password = linkedin_password
#         self.gemini_api_key = gemini_api_key
#         genai.configure(api_key=self.gemini_api_key)

#     def analyze_profile(self, linkedin_username):
#         auth = LinkedInAuthenticator(self.linkedin_email, self.linkedin_password)
#         driver = None
#         try:
#             driver = auth.login()
#             navigator = ProfileNavigator(driver)
#             navigator.navigate_to_profile(linkedin_username)

#             scroller = PostScroller(driver)
#             scroller.scroll_for_posts(limit=10)

#             extractor = PostExtractor(driver)
#             posts = extractor.extract_posts(limit=10)

#             all_results = []
#             for post_text in posts:
#                 prompt = f"""
# You are an AI-based content recommendation engine for paid users.
# Analyze the following LinkedIn post and return a JSON object with recommendations.

# Rules:
# 1. Content Reinforcement: If safe, positive, low-risk → encourage similar content.
# 2. Content Suppression: If political → suggest avoiding such topics.
# 3. Content Flag: If culturally sensitive or controversial → recommend removing it.
# 4. Output must be valid JSON ONLY.

# Post to analyze:
# {post_text}
# """
#                 model = genai.GenerativeModel("gemini-pro")
#                 response = model.generate_content(prompt)
#                 try:
#                     json_result = json.loads(response.text)
#                 except:
#                     json_result = {"error": "Invalid JSON from AI", "raw_output": response.text}

#                 all_results.append({
#                     "post": post_text,
#                     "analysis": json_result
#                 })

#             return all_results

#         finally:
#             if driver:
#                 driver.quit()


# if __name__ == "__main__":
#     EMAIL = "syedawaisalishah46@gmail.com"
#     PASSWORD = "1093333435aA@"
#     GEMINI_API_KEY = "your-gemini-api-key-here"

#     scraper = LinkedInPostAnalyzer(EMAIL, PASSWORD, GEMINI_API_KEY)
#     results = scraper.analyze_profile("sana-kalam-🇵🇸-576166175")

#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     with open(f"linkedin_analysis_{timestamp}.json", "w", encoding="utf-8") as f:
#         json.dump(results, f, indent=2, ensure_ascii=False)

#     print(json.dumps(results, indent=2, ensure_ascii=False))
from apify_client import ApifyClient

# Store tokens
import os
from django.conf import settings

# Get API key from environment variables or Django settings
APIFY_API_TOKEN = os.getenv('APIFY_API_KEY') or getattr(settings, 'APIFY_API_KEY', None)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY') or getattr(settings, 'OPENROUTER_API_KEY', None)

# Config dict (optional, if you want to keep both tokens together)
config = {
    "APIFY_API_TOKEN": APIFY_API_TOKEN,
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY
}



from apify_client import ApifyClient

# Initialize the ApifyClient with your API token
client = ApifyClient(config["APIFY_API_TOKEN"])

# Prepare the Actor input
run_input = {
    "username": "syedawaisalishah",
    "page_number": 1,
    "limit": 5,
}

# Run the Actor and wait for it to finish
run = client.actor("LQQIXN9Othf8f7R5n").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)