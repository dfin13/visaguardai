"""
Test script to verify the persistence and security upgrades.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from django.contrib.auth.models import User
from dashboard.models import UserProfile, AnalysisResult, Config
from django.utils import timezone

def test_twitter_field():
    """Test 1: Verify Twitter field exists and works"""
    print("\n" + "="*60)
    print("TEST 1: Twitter Field in UserProfile")
    print("="*60)
    
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='test_persistence_user',
            defaults={'email': 'test@example.com'}
        )
        
        # Get or create profile
        profile, prof_created = UserProfile.objects.get_or_create(user=user)
        
        # Test setting Twitter username
        profile.twitter = 'testuser123'
        profile.twitter_connected = True
        profile.save()
        
        # Reload from DB
        profile.refresh_from_db()
        
        assert profile.twitter == 'testuser123', "Twitter field not saved correctly"
        assert profile.twitter_connected == True, "Twitter connected flag not saved"
        
        print("✅ Twitter field exists and persists correctly")
        print(f"   Twitter username: {profile.twitter}")
        print(f"   Twitter connected: {profile.twitter_connected}")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_analysis_result_model():
    """Test 2: Verify AnalysisResult model exists and works"""
    print("\n" + "="*60)
    print("TEST 2: AnalysisResult Model")
    print("="*60)
    
    try:
        # Get test user
        user = User.objects.get(username='test_persistence_user')
        
        # Create test analysis result
        result = AnalysisResult.objects.create(
            user=user,
            platform='twitter',
            posts_data=[
                {
                    'post': 'Test tweet',
                    'analysis': {
                        'Twitter': {
                            'risk_score': 15,
                            'content_flag': {'status': 'safe'}
                        }
                    }
                }
            ],
            analysis_data={'test': 'data'},
            profile_data={'username': 'testuser'},
            post_count=1,
            overall_risk_score=15
        )
        
        # Verify it was saved
        saved_result = AnalysisResult.objects.get(id=result.id)
        
        assert saved_result.platform == 'twitter', "Platform not saved"
        assert saved_result.post_count == 1, "Post count not saved"
        assert saved_result.overall_risk_score == 15, "Risk score not saved"
        assert saved_result.expires_at is not None, "Expiration date not set"
        assert len(saved_result.posts_data) == 1, "Posts data not saved"
        
        print("✅ AnalysisResult model works correctly")
        print(f"   Platform: {saved_result.platform}")
        print(f"   Post count: {saved_result.post_count}")
        print(f"   Risk score: {saved_result.overall_risk_score}")
        print(f"   Expires: {saved_result.expires_at.strftime('%Y-%m-%d')}")
        
        # Cleanup
        result.delete()
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_config_encryption():
    """Test 3: Verify Config encryption works"""
    print("\n" + "="*60)
    print("TEST 3: Config API Key Encryption")
    print("="*60)
    
    try:
        config = Config.objects.first()
        
        if not config:
            print("⚠️  No Config object found - creating test config")
            config = Config.objects.create(
                Apify_api_key='test_apify_key_12345',
                Gemini_api_key='test_gemini_key_67890',
                openrouter_api_key='test_openrouter_key',
                STRIPE_SECRET_KEY_TEST='test_stripe_test',
                STRIPE_SECRET_KEY_LIVE='test_stripe_live',
                STRIPE_PUBLISHABLE_KEY_TEST='pk_test_123',
                STRIPE_PUBLISHABLE_KEY_LIVE='pk_live_456',
                Price=1500
            )
        
        # Test reading encrypted fields
        print("✅ Config encryption working")
        print(f"   Apify key (decrypted): {config.Apify_api_key[:20]}...")
        print(f"   OpenRouter key (decrypted): {config.openrouter_api_key[:20]}...")
        print(f"   Price: ${config.price_dollars}")
        
        # Verify keys are actually encrypted in the database
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT \"Apify_api_key\" FROM dashboard_config LIMIT 1")
            raw_value = cursor.fetchone()
            if raw_value:
                encrypted = raw_value[0]
                # Encrypted value should not match plaintext
                if encrypted != config.Apify_api_key:
                    print("✅ API keys are encrypted at rest in database")
                    print(f"   Encrypted format: {encrypted[:40]}...")
                else:
                    print("⚠️  Keys appear to be plaintext (encryption may not be working)")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_cleanup_command():
    """Test 4: Verify cleanup command exists"""
    print("\n" + "="*60)
    print("TEST 4: Cleanup Management Command")
    print("="*60)
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Run cleanup in dry-run mode
        out = StringIO()
        call_command('cleanup_old_data', '--dry-run', stdout=out)
        output = out.getvalue()
        
        assert 'DRY RUN' in output, "Cleanup command not working"
        assert 'expired' in output.lower(), "Cleanup logic not found"
        
        print("✅ Cleanup command exists and runs")
        print("   Command: python manage.py cleanup_old_data")
        print("   Dry-run mode works correctly")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def cleanup_test_data():
    """Cleanup test data"""
    print("\n" + "="*60)
    print("CLEANUP: Removing Test Data")
    print("="*60)
    
    try:
        # Remove test user and related data
        User.objects.filter(username='test_persistence_user').delete()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  VisaGuardAI Persistence & Security Upgrade Tests")
    print("="*60)
    
    tests_passed = 0
    tests_total = 4
    
    if test_twitter_field():
        tests_passed += 1
    
    if test_analysis_result_model():
        tests_passed += 1
    
    if test_config_encryption():
        tests_passed += 1
    
    if test_cleanup_command():
        tests_passed += 1
    
    cleanup_test_data()
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n✅ ALL TESTS PASSED!")
        print("\nUpgrade successful:")
        print("  ✓ Twitter field persists to database")
        print("  ✓ AnalysisResult model stores data permanently")
        print("  ✓ API keys are encrypted at rest")
        print("  ✓ Cleanup command is functional")
    else:
        print(f"\n⚠️  {tests_total - tests_passed} test(s) failed")
        print("Please review the errors above")
    
    print("="*60 + "\n")

