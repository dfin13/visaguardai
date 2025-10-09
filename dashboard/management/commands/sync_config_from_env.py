from django.core.management.base import BaseCommand
from dashboard.models import Config
import os


class Command(BaseCommand):
    help = 'Sync Config model with environment variables'

    def handle(self, *args, **options):
        self.stdout.write("Syncing Config with environment variables...")
        
        config, created = Config.objects.get_or_create(
            pk=1,
            defaults={
                'Apify_api_key': os.getenv('APIFY_API_KEY', ''),
                'Gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
                'openrouter_api_key': os.getenv('OPENROUTER_API_KEY', ''),
                'STRIPE_SECRET_KEY_TEST': os.getenv('STRIPE_SECRET_KEY_TEST', ''),
                'STRIPE_PUBLISHABLE_KEY_TEST': os.getenv('STRIPE_PUBLISHABLE_KEY_TEST', ''),
                'STRIPE_SECRET_KEY_LIVE': os.getenv('STRIPE_SECRET_KEY_LIVE', 'sk_live_placeholder'),
                'STRIPE_PUBLISHABLE_KEY_LIVE': os.getenv('STRIPE_PUBLISHABLE_KEY_LIVE', 'pk_live_placeholder'),
                'Price': 1500,  # $15.00 in cents
                'live': False  # Use test mode by default
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created new Config entry'))
        else:
            # Update existing config with env vars (skip if value is placeholder)
            apify_key = os.getenv('APIFY_API_KEY')
            if apify_key and 'placeholder' not in apify_key.lower():
                config.Apify_api_key = apify_key
            
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key and 'placeholder' not in gemini_key.lower():
                config.Gemini_api_key = gemini_key
            
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            if openrouter_key and 'your_' not in openrouter_key and openrouter_key.startswith('sk-or-v1-'):
                config.openrouter_api_key = openrouter_key
            
            stripe_test_secret = os.getenv('STRIPE_SECRET_KEY_TEST')
            if stripe_test_secret and stripe_test_secret.startswith('sk_test_'):
                config.STRIPE_SECRET_KEY_TEST = stripe_test_secret
            
            stripe_test_pub = os.getenv('STRIPE_PUBLISHABLE_KEY_TEST')
            if stripe_test_pub and stripe_test_pub.startswith('pk_test_'):
                config.STRIPE_PUBLISHABLE_KEY_TEST = stripe_test_pub
            
            # Only update live keys if they're not placeholders in env
            stripe_live_secret = os.getenv('STRIPE_SECRET_KEY_LIVE')
            if stripe_live_secret and stripe_live_secret != 'sk_live_placeholder':
                config.STRIPE_SECRET_KEY_LIVE = stripe_live_secret
            
            stripe_live_pub = os.getenv('STRIPE_PUBLISHABLE_KEY_LIVE')
            if stripe_live_pub and stripe_live_pub != 'pk_live_placeholder':
                config.STRIPE_PUBLISHABLE_KEY_LIVE = stripe_live_pub
            
            config.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Updated existing Config entry'))
        
        self.stdout.write(f"\n📊 Config Status:")
        self.stdout.write(f"   Price: ${config.price_dollars}")
        self.stdout.write(f"   Mode: {'LIVE' if config.live else 'TEST'}")
        self.stdout.write(f"   Apify: {'✅' if config.Apify_api_key and 'placeholder' not in config.Apify_api_key.lower() else '❌'}")
        self.stdout.write(f"   Gemini: {'✅' if config.Gemini_api_key and 'placeholder' not in config.Gemini_api_key.lower() else '❌'}")
        self.stdout.write(f"   OpenRouter: {'✅' if config.openrouter_api_key and 'your_' not in config.openrouter_api_key else '❌'}")
        self.stdout.write(f"   Stripe Test: {'✅' if config.STRIPE_SECRET_KEY_TEST and config.STRIPE_SECRET_KEY_TEST.startswith('sk_test_') else '❌'}")

