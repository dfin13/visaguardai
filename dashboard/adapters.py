from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User
from .models import UserProfile


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for handling OAuth signups (Google, etc.)
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Called just after a user successfully authenticates via OAuth.
        """
        # Check if user already exists
        if sociallogin.is_existing:
            return
        
        # For new users, check if email already exists
        if sociallogin.account.provider == 'google':
            try:
                email = sociallogin.account.extra_data.get('email')
                if email:
                    # Check if user with this email already exists
                    try:
                        existing_user = User.objects.get(email=email)
                        # Connect the social account to existing user
                        sociallogin.connect(request, existing_user)
                        print(f"✅ Connected Google account to existing user: {existing_user.username}")
                    except User.DoesNotExist:
                        # New user, will be created automatically
                        print(f"✅ New Google OAuth user will be created: {email}")
            except Exception as e:
                print(f"⚠️  Error in pre_social_login: {e}")
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user when they sign up via OAuth.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Ensure UserProfile exists
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'first_login': True}
        )
        
        if created:
            print(f"✅ UserProfile created for OAuth user: {user.username}")
        
        return user
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user information from OAuth provider data.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Extract data from Google OAuth
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            
            # Set first/last name if available
            if 'given_name' in extra_data:
                user.first_name = extra_data.get('given_name', '')
            if 'family_name' in extra_data:
                user.last_name = extra_data.get('family_name', '')
            
            print(f"✅ Populated user data from Google: {user.email}")
        
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter for handling regular account operations.
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user during manual signup.
        """
        user = super().save_user(request, user, form, commit=False)
        
        if commit:
            user.save()
            # Ensure UserProfile exists (usually created by signal, but this is a safety net)
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'first_login': True}
            )
            if created:
                print(f"✅ UserProfile created for manual signup: {user.username}")
        
        return user
    
    def get_login_redirect_url(self, request):
        """
        Redirect to dashboard after login.
        """
        return '/dashboard/'
    
    def get_signup_redirect_url(self, request):
        """
        Redirect to dashboard after signup.
        """
        return '/dashboard/'






