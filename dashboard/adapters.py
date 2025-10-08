from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to link existing user accounts when logging in with Google OAuth.
    If a user already signed up using the same Gmail address, the Google login will link to that account.
    This prevents duplicate accounts and enables seamless OAuth integration for existing users.
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a social provider,
        but before the login is actually processed.
        """
        # Extract email from the OAuth response
        email = sociallogin.account.extra_data.get('email')
        if not email:
            return

        # Check if this email already exists in the user table
        try:
            existing_user = User.objects.get(email__iexact=email)
            
            # If the social account isn't already linked, connect it
            if not SocialAccount.objects.filter(
                user=existing_user, 
                provider=sociallogin.account.provider
            ).exists():
                sociallogin.connect(request, existing_user)
                print(f'Linked Google account to existing user: {existing_user.email}')
        except User.DoesNotExist:
            # New user - will be created automatically by Allauth
            pass

