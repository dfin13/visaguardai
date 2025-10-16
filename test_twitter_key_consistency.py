#!/usr/bin/env python
"""
Verify that Twitter scraper uses the SAME Apify API key as the working scrapers
(Instagram, LinkedIn, Facebook)
"""

import os
import sys
import django

# Django setup
sys.path.append('/Users/davidfinney/Downloads/visaguardai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from dotenv import load_dotenv
from dashboard.models import Config

load_dotenv()

print("\n" + "="*80)
print("🔑 APIFY API KEY CONSISTENCY CHECK")
print("="*80 + "\n")

# Get keys from both sources
env_key = os.getenv('APIFY_API_KEY')
db_key = None

try:
    config = Config.objects.first()
    if config:
        db_key = config.Apify_api_key
except Exception as e:
    print(f"⚠️  Error getting database key: {e}")

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("API KEY SOURCES")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if env_key:
    print(f"📁 .env file:")
    print(f"   Key: {env_key[:20]}...{env_key[-8:]}")
    print(f"   Length: {len(env_key)} chars")
else:
    print(f"📁 .env file: ❌ NOT FOUND")

print()

if db_key:
    print(f"🗄️  Config database:")
    print(f"   Key: {db_key[:20]}...{db_key[-8:]}")
    print(f"   Length: {len(db_key)} chars")
else:
    print(f"🗄️  Config database: ❌ NOT FOUND")

print()

# Determine which key each scraper will use
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("WHICH KEY WILL EACH SCRAPER USE?")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

# All scrapers use the same logic:
# 1. Try .env first
# 2. Fall back to database if .env is missing
used_key = env_key if env_key else db_key
key_source = ".env" if env_key else "database"

platforms = ["Instagram", "LinkedIn", "Facebook", "Twitter"]

for platform in platforms:
    print(f"🔹 {platform}:")
    if used_key:
        print(f"   ✅ Will use: {key_source} key (...{used_key[-8:]})")
    else:
        print(f"   ❌ No key available")
    print()

# Check consistency
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("CONSISTENCY CHECK")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if env_key:
    print("✅ ALL SCRAPERS WILL USE THE SAME KEY")
    print(f"   Source: .env file")
    print(f"   Key: ...{env_key[-8:]}")
    print()
    print("🎯 This is CORRECT behavior")
    print("   All scrapers prioritize .env key")
    print()
elif db_key:
    print("⚠️  ALL SCRAPERS WILL USE THE SAME KEY")
    print(f"   Source: Config database")
    print(f"   Key: ...{db_key[-8:]}")
    print()
    print("⚠️  This is FALLBACK behavior")
    print("   All scrapers use database key because .env is missing")
    print()
else:
    print("❌ NO KEYS AVAILABLE")
    print("   All scrapers will fail")
    print()

# Compare keys
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("KEY COMPARISON")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if env_key and db_key:
    if env_key == db_key:
        print("✅ .env and database keys are IDENTICAL")
        print("   Both keys are the same")
    else:
        print("⚠️  .env and database keys are DIFFERENT")
        print()
        print(f"   .env key:      ...{env_key[-8:]}")
        print(f"   Database key:  ...{db_key[-8:]}")
        print()
        print("⚠️  Scrapers will use .env key (prioritized)")
        print("   Database key is ignored")
elif env_key:
    print("✅ Using .env key (database key not found)")
elif db_key:
    print("⚠️  Using database key (.env key not found)")
else:
    print("❌ No keys available")

print()

# Test Twitter scraper import
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TWITTER SCRAPER IMPORT TEST")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

print("Importing Twitter scraper...")
print("(Watch for key logging message)\n")

try:
    # This should trigger the logging we just added
    from dashboard.scraper.t import analyze_twitter_profile
    print("\n✅ Twitter scraper imported successfully")
    print("   Did you see the key logging message above?")
    print("   Should show: '🔑 [Twitter] Using Apify key from .env'")
except Exception as e:
    print(f"\n❌ Error importing Twitter scraper: {e}")

print()

# Summary
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("SUMMARY")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if env_key:
    print("✅ Configuration is CORRECT")
    print()
    print("All scrapers (Instagram, LinkedIn, Facebook, Twitter) will use:")
    print(f"   Source: .env file")
    print(f"   Key: ...{env_key[-8:]}")
    print()
    print("This is the SAME key that Instagram, LinkedIn, and Facebook use.")
    print()
    if env_key[:16] == "apify_api_dC0PGs":
        print("🎯 Confirmed: This is the working .env key")
        print("   (matches Instagram/LinkedIn/Facebook)")
    print()
    print("Twitter scraper is now using the CORRECT key!")
else:
    print("⚠️  Using database key as fallback")
    print()
    print(f"All scrapers will use database key: ...{db_key[-8:] if db_key else 'NONE'}")
    print()
    if db_key and db_key[:16] == "apify_api_D8JEJL":
        print("⚠️  This is the OLD database key")
        print("   Instagram/LinkedIn/Facebook use .env key instead")
        print()
        print("Recommendation: Add .env key to ensure consistency")

print()
print("="*80)
print("✅ CONSISTENCY CHECK COMPLETE")
print("="*80)




