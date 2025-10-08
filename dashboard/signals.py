from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile when a new User is created (including OAuth signups).
    Update the existing UserProfile when the User is updated.
    """
    if created:
        # Create new profile for new users
        UserProfile.objects.create(user=instance, first_login=True)
    else:
        # Update existing profile only if it exists
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
