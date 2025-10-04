from django.db import models

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    username = models.CharField(max_length=150, )
    tiktok = models.CharField(blank=True, null=True, max_length=150)
    instagram = models.CharField(blank=True, null=True, max_length=150)
    linkedin = models.CharField(blank=True, null=True, max_length=150)
    twitter = models.CharField(blank=True, null=True, max_length=150)
    instagram_connected = models.BooleanField(default=False)
    twitter_connected = models.BooleanField(default=False)
    linkedin_connected = models.BooleanField(default=False)
    facebook_connected = models.BooleanField(default=False)
    first_login = models.BooleanField(default=True)

    facebook = models.CharField(blank=True, null=True, max_length=150)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True,)
    university = models.CharField(max_length=100, blank=True, null=True)
    payment_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)  # Add this line

    def __str__(self):
        return f"{self.user.username}'s Profile"


from django.db import models
from django.contrib.auth.models import User

class AnalysisSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile_username = models.CharField(max_length=255)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    payment_completed = models.BooleanField(default=False)
    # You can add more fields for storing results, etc.

    def __str__(self):
        return f"{self.user.username} - {self.profile_username} - {self.analyzed_at}"
class Config(models.Model):
    Apify_api_key = models.CharField(max_length=255)
    Gemini_api_key = models.CharField(max_length=255)
    openrouter_api_key = models.CharField(max_length=255)
    Price = models.IntegerField(null=True, default=0, blank=True, help_text="Price in cents (e.g., 1500 = $15.00)")
    STRIPE_SECRET_KEY_TEST = models.CharField(max_length=255)
    STRIPE_PUBLISHABLE_KEY_TEST = models.CharField(max_length=255)
    STRIPE_SECRET_KEY_LIVE = models.CharField(max_length=255)
    STRIPE_PUBLISHABLE_KEY_LIVE = models.CharField(max_length=255)
    live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def price_dollars(self):
        """Returns the price as a float in dollars."""
        return (self.Price or 0) / 100.0

