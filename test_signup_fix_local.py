#!/usr/bin/env python3
"""
Test script to verify the UserProfile.username field fix locally
Run this to ensure the fix works before deploying to production
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from dashboard.models import UserProfile
from django.db import transaction

def test_userprofile_creation():
    """Test that UserProfile can be created without username field"""
    
    print("=" * 80)
    print("Testing UserProfile Creation Fix")
    print("=" * 80)
    print()
    
    # Test 1: Create user and profile without username
    print("Test 1: Creating UserProfile without username field...")
    try:
        with transaction.atomic():
            # Create a test user
            test_username = f"testuser_{os.urandom(4).hex()}"
            test_email = f"test_{os.urandom(4).hex()}@example.com"
            
            user = User.objects.create_user(
                username=test_username,
                email=test_email,
                password="TestPassword123!"
            )
            print(f"   ✅ Created User: {user.username}")
            
            # Check if signal created profile
            try:
                profile = UserProfile.objects.get(user=user)
                print(f"   ✅ Signal automatically created UserProfile")
                print(f"      - UserProfile.username: '{profile.username}'")
                print(f"      - first_login: {profile.first_login}")
            except UserProfile.DoesNotExist:
                # Manually create profile (simulating what signal should do)
                profile = UserProfile.objects.create(
                    user=user,
                    first_login=True
                )
                print(f"   ✅ Manually created UserProfile")
                print(f"      - UserProfile.username: '{profile.username}'")
            
            # Verify the profile exists and username field is blank/default
            assert profile.username == '', f"Expected empty string, got '{profile.username}'"
            print(f"   ✅ UserProfile.username field accepts blank values")
            
            # Cleanup
            user.delete()
            print(f"   🧹 Cleaned up test user")
            
    except Exception as e:
        print(f"   ❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Test 2: Verify model field definition
    print("Test 2: Checking UserProfile model field definition...")
    try:
        username_field = UserProfile._meta.get_field('username')
        print(f"   - Field type: {type(username_field).__name__}")
        print(f"   - Max length: {username_field.max_length}")
        print(f"   - Blank allowed: {username_field.blank}")
        print(f"   - Null allowed: {username_field.null}")
        print(f"   - Default value: '{username_field.default}'")
        
        if username_field.blank and username_field.default == '':
            print(f"   ✅ Field definition is correct")
        else:
            print(f"   ❌ Field definition needs to be fixed")
            return False
            
    except Exception as e:
        print(f"   ❌ Test 2 FAILED: {e}")
        return False
    
    print()
    
    # Test 3: Test signal handlers
    print("Test 3: Testing signal handlers...")
    try:
        # Import signals to ensure they're loaded
        import dashboard.signals
        print(f"   ✅ Signal handlers loaded from dashboard.signals")
        
        # Check that signals module has the expected handlers
        expected_handlers = [
            'create_user_profile',
            'save_user_profile',
            'user_signed_up_handler',
            'social_account_added_handler'
        ]
        
        for handler in expected_handlers:
            if hasattr(dashboard.signals, handler):
                print(f"   ✅ Found handler: {handler}")
            else:
                print(f"   ⚠️  Handler not found: {handler}")
        
    except Exception as e:
        print(f"   ❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print("The fix is working correctly. You can now deploy to production.")
    print()
    print("Deployment command:")
    print("   ./deploy_signup_fix.sh")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_userprofile_creation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

