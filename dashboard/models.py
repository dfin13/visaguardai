from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    username = models.CharField(max_length=150, )
    tiktok = models.CharField(blank=True, null=True, max_length=150)
    instagram = models.CharField(blank=True, null=True, max_length=150)
    linkedin = models.CharField(blank=True, null=True, max_length=150)
    twitter = models.CharField(blank=True, null=True, max_length=150)  # Re-added for persistent storage
    facebook = models.CharField(blank=True, null=True, max_length=150)
    
    instagram_connected = models.BooleanField(default=False)
    tiktok_connected = models.BooleanField(default=False)
    linkedin_connected = models.BooleanField(default=False)
    twitter_connected = models.BooleanField(default=False)  # Re-added
    facebook_connected = models.BooleanField(default=False)
    first_login = models.BooleanField(default=True)
    
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True,)  # Legacy field, kept for backward compatibility
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    country_of_application = models.CharField(max_length=100, blank=True, null=True)
    university = models.CharField(max_length=100, blank=True, null=True)
    payment_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class AnalysisSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile_username = models.CharField(max_length=255)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    payment_completed = models.BooleanField(default=False)
    # You can add more fields for storing results, etc.

    def __str__(self):
        return f"{self.user.username} - {self.profile_username} - {self.analyzed_at}"


class AnalysisResult(models.Model):
    """
    Persistent storage for analysis results.
    Stores analyzed posts, AI scores, and recommendations permanently.
    """
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('twitter', 'Twitter/X'),
        ('facebook', 'Facebook'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_results')
    session = models.ForeignKey(AnalysisSession, on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    # JSON fields for storing complex data
    posts_data = models.JSONField(default=list, help_text="List of analyzed posts with content")
    analysis_data = models.JSONField(default=dict, help_text="AI analysis results and risk scores")
    profile_data = models.JSONField(default=dict, help_text="Profile assessment data")
    
    # Metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    payment_completed = models.BooleanField(default=False)
    post_count = models.IntegerField(default=0)
    overall_risk_score = models.IntegerField(null=True, blank=True)
    
    # Retention
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this data should be cleaned up")
    
    class Meta:
        ordering = ['-analyzed_at']
        indexes = [
            models.Index(fields=['user', '-analyzed_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.analyzed_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Set expiration date if not set (7 days from now)
        if not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(days=7)
        # Update post count from posts_data
        if isinstance(self.posts_data, list):
            self.post_count = len(self.posts_data)
        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Track all payment transactions for reliability and audit trail.
    Prevents double charges and provides payment history.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
        ('expired', 'Expired'),  # Session timed out or became invalid
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    stripe_session_id = models.CharField(max_length=255, unique=True, db_index=True, help_text="Stripe Checkout Session ID")
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, db_index=True, help_text="Stripe Payment Intent ID")
    
    amount = models.IntegerField(help_text="Amount in cents")
    currency = models.CharField(max_length=3, default='usd')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Metadata
    customer_email = models.EmailField()
    analysis_granted = models.BooleanField(default=False, help_text="Whether analysis access was granted")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['stripe_session_id']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount/100:.2f} - {self.status}"
    
    def mark_succeeded(self):
        """Mark payment as succeeded and grant analysis access."""
        if self.status != 'succeeded':
            self.status = 'succeeded'
            self.completed_at = timezone.now()
            self.analysis_granted = True
            self.save()
            
            # Update user profile
            try:
                profile = self.user.userprofile
                profile.payment_completed = True
                profile.save()
            except Exception as e:
                # Log but don't fail
                print(f"Warning: Could not update user profile for payment {self.id}: {e}")
    
    def mark_failed(self, error_message=''):
        """Mark payment as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.save()
    
    def mark_canceled(self):
        """Mark payment as canceled."""
        self.status = 'canceled'
        self.save()


class Config(models.Model):
    """
    Global configuration with encrypted API keys.
    Requires FIELD_ENCRYPTION_KEY in environment or settings.
    """
    from encrypted_model_fields.fields import EncryptedTextField
    
    # Encrypted API keys for security (using TextField for flexibility)
    Apify_api_key = EncryptedTextField()
    Gemini_api_key = EncryptedTextField()
    openrouter_api_key = EncryptedTextField()
    STRIPE_SECRET_KEY_TEST = EncryptedTextField()
    STRIPE_SECRET_KEY_LIVE = EncryptedTextField()
    
    # Non-sensitive fields (not encrypted)
    Price = models.IntegerField(null=True, default=0, blank=True, help_text="Price in cents (e.g., 1500 = $15.00)")
    STRIPE_PUBLISHABLE_KEY_TEST = models.CharField(max_length=255)  # Public keys don't need encryption
    STRIPE_PUBLISHABLE_KEY_LIVE = models.CharField(max_length=255)  # Public keys don't need encryption
    live = models.BooleanField(default=False)
    stripe_webhook_secret = models.CharField(max_length=255, blank=True, null=True, help_text="Stripe webhook signing secret")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def price_dollars(self):
        """Returns the price as a float in dollars."""
        return (self.Price or 0) / 100.0

