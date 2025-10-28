from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
from allauth.socialaccount.signals import pre_social_login, social_account_added
from allauth.account.signals import user_signed_up

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create UserProfile when a new User is created (manual signup or OAuth).
    """
    if created:
        try:
            UserProfile.objects.create(user=instance, first_login=True)
            print(f"✅ UserProfile created for user: {instance.username} (ID: {instance.id})")
        except Exception as e:
            print(f"❌ Error creating UserProfile for {instance.username}: {e}")
            # Try to get_or_create as fallback
            UserProfile.objects.get_or_create(user=instance, defaults={'first_login': True})

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Ensure UserProfile exists and save it.
    """
    # Check if profile exists before trying to save
    try:
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
        else:
            # Create profile if it doesn't exist (safety net)
            UserProfile.objects.get_or_create(user=instance, defaults={'first_login': True})
            print(f"⚠️  UserProfile was missing for user: {instance.username} - created now")
    except Exception as e:
        print(f"❌ Error in save_user_profile for {instance.username}: {e}")

@receiver(user_signed_up)
def user_signed_up_handler(request, user, **kwargs):
    """
    Handle both manual and social signups.
    Ensures UserProfile exists for OAuth users.
    """
    try:
        # Ensure profile exists (usually created by post_save signal, but this is a safety net)
        profile, created = UserProfile.objects.get_or_create(user=user, defaults={'first_login': True})
        if created:
            print(f"✅ UserProfile created via signup handler for: {user.username}")
        else:
            print(f"✓ UserProfile already exists for: {user.username}")
    except Exception as e:
        print(f"❌ Error in user_signed_up_handler for {user.username}: {e}")

@receiver(social_account_added)
def social_account_added_handler(request, sociallogin, **kwargs):
    """
    Handle when a social account (Google OAuth) is added.
    Ensures UserProfile exists for the user.
    """
    try:
        user = sociallogin.user
        profile, created = UserProfile.objects.get_or_create(user=user, defaults={'first_login': True})
        if created:
            print(f"✅ UserProfile created for OAuth user: {user.username} via {sociallogin.account.provider}")
        else:
            print(f"✓ UserProfile exists for OAuth user: {user.username}")
    except Exception as e:
        print(f"❌ Error in social_account_added_handler: {e}")
