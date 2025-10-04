from django.contrib import admin
from .models import UserProfile, Config

# Configure admin site
admin.site.site_header = "VisaGuard Admin"
admin.site.site_title = "VisaGuard Admin Portal"
admin.site.index_title = "Welcome to the VisaGuard Admin Portal"

# Register models
admin.site.register(UserProfile)
from django import forms

class ConfigAdminForm(forms.ModelForm):
    price_dollars = forms.FloatField(
        label="Price (Dollars)",
        help_text="Enter the price in dollars (e.g., 15 for $15.00). Will be stored as cents.",
        required=True,
    )

    class Meta:
        model = Config
        fields = [
            "Apify_api_key",
            "Gemini_api_key",
            "openrouter_api_key",
            "price_dollars",
            "STRIPE_SECRET_KEY_TEST",
            "STRIPE_PUBLISHABLE_KEY_TEST",
            "STRIPE_SECRET_KEY_LIVE",
            "STRIPE_PUBLISHABLE_KEY_LIVE",
            "live",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["price_dollars"].initial = self.instance.price_dollars

    def clean(self):
        cleaned_data = super().clean()
        price_dollars = cleaned_data.get("price_dollars")
        if price_dollars is not None:
            cleaned_data["Price"] = int(round(float(price_dollars) * 100))
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        price_dollars = self.cleaned_data.get("price_dollars")
        if price_dollars is not None:
            instance.Price = int(round(float(price_dollars) * 100))
        if commit:
            instance.save()
        return instance

@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    form = ConfigAdminForm
    list_display = ("id", "price_dollars", "Price", "live", "created_at", "updated_at")
    readonly_fields = ("Price",)

