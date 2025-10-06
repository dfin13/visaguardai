from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.google.provider import GoogleProvider


class Command(BaseCommand):
    help = 'Set up Google OAuth SocialApp with placeholder credentials for development'

    def handle(self, *args, **options):
        # Get or create the default site
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': '127.0.0.1:8000',
                'name': 'VisaGuardAI Development'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created site: {site.name} ({site.domain})')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Using existing site: {site.name} ({site.domain})')
            )

        # Get or create Google SocialApp
        social_app, created = SocialApp.objects.get_or_create(
            provider=GoogleProvider.id,
            defaults={
                'name': 'Google OAuth (Development)',
                'client_id': 'your-google-client-id.apps.googleusercontent.com',
                'secret': 'your-google-client-secret',
                'key': '',
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('Created Google OAuth SocialApp with placeholder credentials')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Google OAuth SocialApp already exists')
            )

        # Add the site to the social app if not already added
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'Added site {site.domain} to Google OAuth SocialApp')
            )

        self.stdout.write(
            self.style.WARNING(
                '\nIMPORTANT: Replace the placeholder credentials in Django Admin:\n'
                '1. Go to /admin/socialaccount/socialapp/\n'
                '2. Edit the Google OAuth app\n'
                '3. Update client_id and secret with your actual Google OAuth credentials\n'
                '4. For development, use: http://127.0.0.1:8000/accounts/google/login/callback/\n'
            )
        )

