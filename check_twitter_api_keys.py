#!/usr/bin/env python3
"""
Check if Twitter scraper is using the correct API key
Run this on production to diagnose the issue
"""

import os
import sys
import django

# Django setup
sys.path.append('/var/www/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from dashboard.models import Config
from dotenv import load_dotenv

print("\n" + "="*80)
print("🔍 TWITTER API KEY DIAGNOSTIC")
print("="*80 + "\n")

# Load .env file
env_path = '/var/www/visaguardai/.env'
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Check APIFY_API_KEY in .env
env_key = os.getenv('APIFY_API_KEY')
if env_key:
    print(f"✅ APIFY_API_KEY in .env: {env_key[:10]}...{env_key[-4:]}")
else:
    print("❌ APIFY_API_KEY NOT in .env")

# Check Config table
try:
    config = Config.objects.first()
    if config and config.Apify_api_key:
        print(f"✅ Apify_api_key in Config: {config.Apify_api_key[:10]}...{config.Apify_api_key[-4:]}")
    else:
        print("❌ Apify_api_key NOT in Config table")
except Exception as e:
    print(f"❌ Error reading Config: {e}")

# Check if they're the same
if env_key and config and config.Apify_api_key:
    if env_key == config.Apify_api_key:
        print("\n✅ KEYS MATCH - Using same key everywhere")
    else:
        print("\n⚠️  WARNING: KEYS ARE DIFFERENT!")
        print("   .env key:", env_key[:15], "...")
        print("   Config key:", config.Apify_api_key[:15], "...")

# Test what Twitter scraper would load
print("\n" + "-"*80)
print("Testing Twitter scraper key loading pattern:")
print("-"*80 + "\n")

# Simulate the Twitter scraper's loading logic
APIFY_API_TOKEN = os.getenv('APIFY_API_KEY')

if APIFY_API_TOKEN:
    print(f"✅ Twitter would use .env key: {APIFY_API_TOKEN[:10]}...{APIFY_API_TOKEN[-4:]}")
else:
    print("⚠️  .env key not found, falling back to Config")
    if config:
        APIFY_API_TOKEN = config.Apify_api_key
        print(f"✅ Twitter would use Config key: {APIFY_API_TOKEN[:10]}...{APIFY_API_TOKEN[-4:]}")
    else:
        print("❌ No API key found anywhere!")

# Test the key with Apify
print("\n" + "-"*80)
print("Testing key with Apify API:")
print("-"*80 + "\n")

try:
    from apify_client import ApifyClient
    client = ApifyClient(APIFY_API_TOKEN)
    
    # Try to get user info
    user = client.user().get()
    if user:
        print(f"✅ Apify key is VALID")
        print(f"   Username: {user.get('username', 'N/A')}")
        print(f"   Email: {user.get('email', 'N/A')}")
    else:
        print("⚠️  Key connects but user info unavailable")
        
except Exception as e:
    print(f"❌ Apify key test FAILED: {e}")

# Test the Twitter actor
print("\n" + "-"*80)
print("Testing Twitter actor accessibility:")
print("-"*80 + "\n")

try:
    actor_id = "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest"
    print(f"Actor: {actor_id}")
    
    actor = client.actor(actor_id).get()
    if actor:
        print(f"✅ Actor is accessible")
        print(f"   Name: {actor.get('name', 'N/A')}")
        print(f"   Username: {actor.get('username', 'N/A')}")
    else:
        print("⚠️  Actor not found or not accessible")
        
except Exception as e:
    print(f"❌ Actor accessibility test FAILED: {e}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80 + "\n")

if env_key and env_key == APIFY_API_TOKEN:
    print("✅ Twitter is using the .env API key (correct)")
elif config and config.Apify_api_key == APIFY_API_TOKEN:
    print("⚠️  Twitter is using the Config table key (may differ from other platforms)")
else:
    print("❌ Unable to determine which key Twitter is using")

print("\n" + "="*80)

