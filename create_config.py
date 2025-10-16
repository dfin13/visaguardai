#!/usr/bin/env python
"""
Create initial Config entry in database with values from environment variables.
This script should be run on the production server after PostgreSQL migration.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from dashboard.models import Config

def create_initial_config():
    """Create Config entry if it doesn't exist"""
    
    if Config.objects.exists():
        print(f"✅ Config already exists (count: {Config.objects.count()})")
        config = Config.objects.first()
        print(f"   Price: ${config.price_dollars}")
        print(f"   Mode: {'LIVE' if config.live else 'TEST'}")
        return config
    
    print("Creating Config entry from environment variables...")
    
    config = Config.objects.create(
        Apify_api_key=os.getenv('APIFY_API_KEY', ''),
        Gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
        openrouter_api_key=os.getenv('OPENROUTER_API_KEY', ''),
        STRIPE_SECRET_KEY_TEST=os.getenv('STRIPE_SECRET_KEY_TEST', ''),
        STRIPE_PUBLISHABLE_KEY_TEST=os.getenv('STRIPE_PUBLISHABLE_KEY_TEST', ''),
        STRIPE_SECRET_KEY_LIVE=os.getenv('STRIPE_SECRET_KEY_LIVE', 'sk_live_placeholder'),
        STRIPE_PUBLISHABLE_KEY_LIVE=os.getenv('STRIPE_PUBLISHABLE_KEY_LIVE', 'pk_live_placeholder'),
        Price=1500,  # $15.00 in cents
        live=False  # Start with test mode
    )
    
    print(f"✅ Config created successfully!")
    print(f"   ID: {config.id}")
    print(f"   Price: ${config.price_dollars}")
    print(f"   Mode: {'LIVE' if config.live else 'TEST'}")
    print(f"   Apify key: {'✅ Set' if config.Apify_api_key else '❌ Empty'}")
    print(f"   Gemini key: {'✅ Set' if config.Gemini_api_key else '❌ Empty'}")
    print(f"   OpenRouter key: {'✅ Set' if config.openrouter_api_key else '❌ Empty'}")
    print(f"   Stripe Test: {'✅ Set' if config.STRIPE_SECRET_KEY_TEST else '❌ Empty'}")
    
    return config

if __name__ == '__main__':
    create_initial_config()







