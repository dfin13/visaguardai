import time
from django.shortcuts import render, redirect
from django.urls import reverse

from django.contrib.auth.decorators import login_required
import math
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
def clear_analysis_session(request):
    keys_to_clear = [
        'twitter_analysis',
        'instagram_analysis',
        'linkedin_analysis',
        'facebook_analysis',
        # add other session keys as needed
    ]
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]
    return redirect(reverse('dashboard:dashboard'))
from .models import AnalysisSession, AnalysisResult
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import stripe
from .scraper.instagram import analyze_instagram_posts
from .models import Config
from .models import UserProfile
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password, ValidationError as PasswordValidationError
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
import os

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .scraper.t import analyze_twitter_profile
from .scraper.facebook import analyze_facebook_posts
facebook_analysis= [ {
    "post": "Several of Fox Newsâ€™s most prominent on-air news personalities made clear their desire to help President Trump shortly before and after the 2020 presidential election, according to a tranche of court documents released in a $2.7 billion defamation lawsuit against Fox Corporation filed by Smartmatic, a voting technology company.", 
    "analysis": {
      "Facebook": {
        "content_reinforcement": {
          "status": "caution",
          "recommendation": "something",
          "reason": "Content involves political and legal matters, which are not positive or low-risk."
        },
        "content_suppression": {
          "status": "warning",
          "recommendation": "Avoid political topics.",
          "reason": "Discusses political figures, elections, and legal actions."
        },
        "content_flag": {
          "status": "caution",
          "recommendation": "Review for controversy.",
          "reason": "References election disputes, potentially controversial."
        },
        "risk_score": 4
      }
    }
  },
  {
    "post": "What's next for the Ukraine peace talks? The White House said that Russia's Vladimir Putin has agreed to meet with Ukraine's Volodymyr Zelensky â€” something Putin has not confirmed.",
    "analysis": {
      "Facebook": {
        "content_reinforcement": {
          "status": "caution",
          "recommendation": "f",
          "reason": "Content focuses on political conflict and is not low-risk."
        },
        "content_suppression": {
          "status": "warning",
          "recommendation": "Avoid political topics.",
          "reason": "Discusses geopolitical conflict and unconfirmed diplomatic actions."
        },
        "content_flag": {
          "status": "caution",
          "recommendation": "Review for sensitivity.",
          "reason": "Involves ongoing geopolitical tensions."
        },
        "risk_score": 4
      }
    }
  },
  {
    "post": "The leaders of Germany, France, and Britain decided they would all accompany Volodymyr Zelensky, the president of Ukraine, to Washington for a summit with President Trump about peace talks with Russia. So would the leaders of Italy, Finland, the European Union and NATO. They flew in on separate planes. But with Trump, they spoke in one voice.",
    "analysis": {
      "Facebook": {
        "content_reinforcement": {
          "status": "caution",
          "recommendation": "something",
          "reason": "Political summit discussions are not low-risk."
        },
        "content_suppression": {
          "status": "warning",
          "recommendation": "Avoid political topics.",
          "reason": "Focuses on international political coordination."
        },
        "content_flag": {
          "status": "caution",
          "recommendation": "Review for sensitivity.",
          "reason": "References ongoing geopolitical negotiations."
        },
        "risk_score": 4
      }
    }
  },
  {
    "post": "No matter what Americans think of their politics, the U.S. still operates in the open. When the most powerful politician and the richest businessman fell out, the public got the full spectacle: barbed posts on social media and sniping in speeches. China is the opposite. The country still doesnâ€™t know why former President Hu Jintao was removed from the 2022 Communist Party congress, or what really happened when former Premier Li Keqiang died in 2023.",
    "analysis": {
      "Facebook": {
        "content_reinforcement": {
          "status": "caution",
          "recommendation": "something",
          "reason": "Content compares political systems, not low-risk."
        },
        "content_suppression": {
          "status": "warning",
          "recommendation": "Avoid political topics.",
          "reason": "Discusses political transparency and historical leadership changes."
        },
        "content_flag": {
          "status": "warning",
          "recommendation": "Recommend removing it.",
          "reason": "Culturally sensitive content about Chinese political affairs."
        },
        "risk_score": 5
      }
    }
  },
  {
    "post": "The White House said that Russiaâ€™s Vladimir Putin has agreed to meet with Ukraineâ€™s Volodymyr Zelensky â€” something Putin has not confirmed.",
    "analysis": {
      "Facebook": {
        "content_reinforcement": {
          "status": "caution",
          "recommendation": "something",
          "reason": "Content focuses on geopolitical conflict."
        },
        "content_suppression": {
          "status": "warning",
          "recommendation": "Avoid political topics.",
          "reason": "Discusses unconfirmed diplomatic developments."
        },
        "content_flag": {
          "status": "caution",
          "recommendation": "Review for sensitivity.",
          "reason": "Involves ongoing geopolitical tensions."
        },
        "risk_score": 4
      }
    }
  }
]
@csrf_exempt
@require_http_methods(["GET"])
def check_analysis_progress(request):
    """Check the current progress of analysis with detailed stages"""
    # Check authentication first and return JSON error if not authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        from django.core.cache import cache
        
        # Check cache for analysis results
        user_profile = request.user.userprofile
        instagram_username = user_profile.instagram
        linkedin_username = user_profile.linkedin
        twitter_username = user_profile.twitter  # Now stored in database
        facebook_username = user_profile.facebook

        instagram_result = cache.get(f'instagram_analysis_{request.user.id}')
        linkedin_result = cache.get(f'linkedin_analysis_{request.user.id}')
        twitter_result = cache.get(f'twitter_analysis_{request.user.id}')
        facebook_result = cache.get(f'facebook_analysis_{request.user.id}')

        # Check for detailed progress stages
        current_stage = cache.get(f'analysis_stage_{request.user.id}', 'starting')
        stage_progress = cache.get(f'stage_progress_{request.user.id}', 0)

        instagram_done = (not instagram_username) or (instagram_result is not None)
        linkedin_done = (not linkedin_username) or (linkedin_result is not None)
        twitter_done = (not twitter_username) or (twitter_result is not None)
        facebook_done = (not facebook_username) or (facebook_result is not None)

        # Determine overall progress and message based on detailed stages
        if instagram_done and linkedin_done and twitter_done and facebook_done:
            # Debug: Log what's being copied from cache to session
            print(f"🔄 Copying analysis results from cache to session:")
            print(f"   Instagram: {len(instagram_result) if isinstance(instagram_result, list) else 'Not a list'}")
            print(f"   LinkedIn: {len(linkedin_result) if isinstance(linkedin_result, list) else 'Not a list'}")
            print(f"   Twitter: {len(twitter_result) if isinstance(twitter_result, list) else 'Not a list'}")
            print(f"   Facebook: {len(facebook_result) if isinstance(facebook_result, list) else 'Not a list'}")
            
            request.session['instagram_analysis'] = instagram_result
            request.session['linkedin_analysis'] = linkedin_result
            request.session['twitter_analysis'] = twitter_result
            request.session['facebook_analysis'] = facebook_result
            request.session.modified = True  # Force session save
            
            # Debug: Verify session was updated
            print(f"✅ Session updated:")
            print(f"   Instagram in session: {len(request.session.get('instagram_analysis', [])) if isinstance(request.session.get('instagram_analysis'), list) else 'Not a list'}")
            print(f"   LinkedIn in session: {len(request.session.get('linkedin_analysis', [])) if isinstance(request.session.get('linkedin_analysis'), list) else 'Not a list'}")
            print(f"   Twitter in session: {len(request.session.get('twitter_analysis', [])) if isinstance(request.session.get('twitter_analysis'), list) else 'Not a list'}")
            print(f"   Facebook in session: {len(request.session.get('facebook_analysis', [])) if isinstance(request.session.get('facebook_analysis'), list) else 'Not a list'}")
            
            # Clear cache
            cache.delete(f'instagram_analysis_{request.user.id}')
            cache.delete(f'linkedin_analysis_{request.user.id}')
            cache.delete(f'twitter_analysis_{request.user.id}')
            cache.delete(f'facebook_analysis_{request.user.id}')
            cache.delete(f'analysis_stage_{request.user.id}')
            cache.delete(f'stage_progress_{request.user.id}')
            status = 'complete'
            message = 'Analysis complete!'
            progress = 100
        else:
            # Detailed stage-based progress
            if current_stage == 'starting':
                status = 'starting'
                message = 'Starting analysis...'
                progress = 5
            elif current_stage == 'linkedin_processing':
                status = 'linkedin_processing'
                message = 'LinkedIn analysis in progress...'
                progress = 10 + stage_progress
            elif current_stage == 'background_processing':
                status = 'background_processing'
                message = 'Processing additional platforms...'
                progress = 30 + stage_progress
            elif current_stage == 'facebook_analysis':
                status = 'facebook_analysis'
                message = 'Facebook analysis in progress...'
                progress = 40 + stage_progress
            elif current_stage == 'blueprint_scanning':
                status = 'blueprint_scanning'
                message = 'Blueprint scanning...'
                progress = 55 + stage_progress
            elif current_stage == 'post_scanning':
                status = 'post_scanning'
                message = 'Post scanning...'
                progress = 70 + stage_progress
            elif current_stage == 'comment_scanning':
                status = 'comment_scanning'
                message = 'Comment scanning...'
                progress = 85 + stage_progress
            elif instagram_done and linkedin_done and twitter_done and not facebook_done:
                status = 'facebook_processing'
                message = 'Analyzing Facebook posts...'
                progress = 90
            elif instagram_done and linkedin_done and not twitter_done:
                status = 'twitter_processing'
                message = 'Analyzing Twitter posts...'
                progress = 75
            elif instagram_done and not linkedin_done:
                status = 'linkedin_processing'
                message = 'Analyzing LinkedIn profile...'
                progress = 50
            else:
                status = 'instagram_processing'
                message = 'Analyzing Instagram posts...'
                progress = 25

        return JsonResponse({
            'status': status,
            'message': message,
            'progress': progress,
            'current_stage': current_stage,
            'instagram_done': instagram_done,
            'linkedin_done': linkedin_done,
            'twitter_done': twitter_done,
            'facebook_done': facebook_done
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

import threading

def process_analysis_async(user_id, instagram_username, linkedin_username, twitter_username, facebook_username=None):
    """Process analysis in background thread, always returns results (real or dummy) for each platform."""
    print(f"\n{'='*80}")
    print(f"🔍 BACKGROUND ANALYSIS STARTED")
    print(f"   User ID: {user_id}")
    print(f"   Instagram: {instagram_username or 'None'}")
    print(f"   LinkedIn: {linkedin_username or 'None'}")
    print(f"   Twitter: {twitter_username or 'None'}")
    print(f"   Facebook: {facebook_username or 'None'}")
    print(f"{'='*80}\n")
    
    from .utils import analyze_all_platforms
    try:
        analyze_all_platforms(user_id, instagram_username, linkedin_username, twitter_username, facebook_username)
        print(f"\n✅ Background analysis completed for user {user_id}\n")
    except Exception as e:
        import traceback
        print(f"\n❌ Unified background analysis failed: {e}")
        print(f"Traceback:\n{traceback.format_exc()}\n")



@csrf_exempt
@require_http_methods(["POST"])
@login_required
def validate_accounts(request):
    """
    Pre-scrape validation endpoint to check if accounts exist and are public.
    Can validate either:
    1. All connected accounts from user profile (default)
    2. A specific username passed in request body (validate_only mode)
    """
    try:
        import json
        
        # Check if this is a single-username validation request
        request_data = {}
        if request.body:
            try:
                request_data = json.loads(request.body)
            except:
                pass
        
        validate_only = request_data.get('validate_only', False)
        
        if validate_only:
            # Validate specific username from request
            platform = request_data.get('platform')
            username = request_data.get('username')
            
            print(f"🔍 [VALIDATION REQUEST] Platform: {platform}, Username: {username}")
            
            if not platform or not username:
                print(f"❌ [VALIDATION] Missing platform or username")
                return JsonResponse({
                    'success': False,
                    'error': 'Platform and username required for validation'
                }, status=400)
            
            print(f"🔍 Validating single account: {platform} - {username}")
            
            # Import specific validator
            from .validators import (
                validate_instagram_account,
                validate_linkedin_account,
                validate_twitter_account,
                validate_facebook_account
            )
            
            validators = {
                'instagram': validate_instagram_account,
                'linkedin': validate_linkedin_account,
                'twitter': validate_twitter_account,
                'facebook': validate_facebook_account
            }
            
            if platform not in validators:
                return JsonResponse({
                    'success': False,
                    'error': f'Unknown platform: {platform}'
                }, status=400)
            
            # Run validation
            is_valid, message = validators[platform](username)
            
            print(f"📊 [VALIDATION RESULT] Platform: {platform}, Valid: {is_valid}, Message: {message}")
            
            return JsonResponse({
                'success': True,
                'all_valid': is_valid,
                'results': {
                    platform: {
                        'valid': is_valid,
                        'message': message
                    }
                }
            })
        
        else:
            # Validate all connected accounts from user profile
            user_profile = UserProfile.objects.get(user=request.user)
            
            instagram_username = user_profile.instagram
            linkedin_username = user_profile.linkedin
            twitter_username = user_profile.twitter
            facebook_username = user_profile.facebook
            
            # Import validation function
            from .validators import validate_all_accounts
            
            print(f"🔍 Validating all accounts for user {request.user.username}")
            print(f"   Instagram: {instagram_username or 'None'}")
            print(f"   LinkedIn: {linkedin_username or 'None'}")
            print(f"   Twitter: {twitter_username or 'None'}")
            print(f"   Facebook: {facebook_username or 'None'}")
            
            # Run validation (lightweight 1-post test scrapes)
            all_valid, results = validate_all_accounts(
                instagram_username=instagram_username,
                linkedin_username=linkedin_username,
                twitter_username=twitter_username,
                facebook_username=facebook_username
            )
            
            return JsonResponse({
                'success': True,
                'all_valid': all_valid,
                'results': results
            })
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_analysis(request):
    print(f"\n{'='*80}")
    print(f"🚀 START_ANALYSIS REQUEST RECEIVED")
    print(f"   User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    print(f"   Method: {request.method}")
    print(f"{'='*80}\n")
    
    # Check authentication first and return JSON error if not authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        instagram_username = user_profile.instagram
        linkedin_username = user_profile.linkedin
        twitter_username = user_profile.twitter  # Now stored in database
        facebook_username = user_profile.facebook
        
        # Only start analysis if at least one username is present
        if not instagram_username and not linkedin_username and not twitter_username and not facebook_username:
            return JsonResponse({'success': False, 'error': 'Please connect at least one social account before starting analysis.'})

        # Reset payment status for new analysis (pay-per-analysis model)
        request.session['current_analysis_paid'] = False
        
        # Create unique run ID to prevent cache collisions
        import uuid
        run_id = str(uuid.uuid4())[:8]  # Short unique ID
        request.session['analysis_run_id'] = run_id
        request.session['analysis_timestamp'] = time.time()
        print(f"🆔 New analysis run ID: {run_id}")
        
        # Clear any existing analysis data from session
        request.session.pop('instagram_analysis', None)
        request.session.pop('linkedin_analysis', None)
        request.session.pop('twitter_analysis', None)
        request.session.pop('facebook_analysis', None)
        
        # Set analysis state flags
        request.session['analysis_started'] = True
        request.session['analysis_complete'] = False
        
        # Clear ALL cached analysis data for this user
        from django.core.cache import cache
        cache.delete(f'instagram_analysis_{request.user.id}')
        cache.delete(f'linkedin_analysis_{request.user.id}')
        cache.delete(f'twitter_analysis_{request.user.id}')
        cache.delete(f'facebook_analysis_{request.user.id}')
        print(f"🗑️ Cleared all cached analysis data for user {request.user.id}")
        
        # Set initial analysis stage
        cache.set(f'analysis_stage_{request.user.id}', 'starting', timeout=60*60)
        cache.set(f'stage_progress_{request.user.id}', 0, timeout=60*60)
        
        # Start background processing for other platforms
        thread = threading.Thread(
            target=process_analysis_async, 
            args=(request.user.id, instagram_username, linkedin_username, twitter_username, facebook_username)
        )
        thread.daemon = False  # Changed from True - allow thread to complete even after response
        thread.start()
            
        return JsonResponse({'success': True, 'message': 'Analysis started successfully'})
        
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User profile not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
@login_required
def dashboard(request):
    tweet_analysis = request.session.get('tweet_analysis')    
    if request.session.get('instagram_analysis') is not None:
        analysis_timestamp = request.session.get('analysis_timestamp', 0)
        current_time = time.time()
        # Expire analysis after 24 hours (86400 seconds) or if no timestamp
        if current_time - analysis_timestamp > 86400 or analysis_timestamp == 0:
            request.session.pop('instagram_analysis', None)
            request.session.pop('linkedin_analysis', None)
            request.session.pop('current_analysis_paid', None)
            request.session.pop('analysis_timestamp', None)
            instagram_analysis = None
            linkedin_analysis = None
        else:
            instagram_analysis = request.session.get('instagram_analysis')
    else:
        instagram_analysis = None

    if request.session.get('linkedin_analysis') is not None:
        analysis_timestamp = request.session.get('analysis_timestamp', 0)
        current_time = time.time()
        if current_time - analysis_timestamp > 86400 or analysis_timestamp == 0:
            linkedin_analysis = None
        else:
            linkedin_analysis = request.session.get('linkedin_analysis')
    else:
        linkedin_analysis = None
    
    twitter_analysis = request.session.get('twitter_analysis')
    twitter_loading = False
    
    # Get user profile for Twitter username
    twitter_username = None
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        twitter_username = user_profile.twitter  # Now stored in database
    except Exception as e:
        pass

    if request.method == 'POST':
        try:

            # Get form data
            username = request.POST.get('user-name', '').strip()
            country = request.POST.get('user-country', '').strip()
            university = request.POST.get('user-university', '').strip()

            # Create new analysis session (payment gating is now per-analysis)
            if username:
                AnalysisSession.objects.create(
                    user=request.user,
                    profile_username=username,
                    payment_completed=False
                )
            
            # Validate required fields
            if not username:
                messages.error(request, 'Username is required.')
                return render(request, 'dashboard/dashboard.html', {
                    'user': request.user,
                    'user_email': request.user.email,
                    'is_authenticated': request.user.is_authenticated,
                })
            
            if not country:
                messages.error(request, 'Country is required.')
                return render(request, 'dashboard/dashboard.html', {
                    'user': request.user,
                    'user_email': request.user.email,
                    'is_authenticated': request.user.is_authenticated,
                })
            
            # Check if user profile already exists
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                # Update existing profile
                user_profile.username = username
                user_profile.country = country
                user_profile.university = university  # Note: typo in model field name
                user_profile.save()
                messages.success(request, 'Profile updated successfully!')
            except UserProfile.DoesNotExist:
                # Create new profile and assign to user_profile
                user_profile = UserProfile.objects.create(
                    user=request.user,
                    username=username,
                    country=country,
                    university=university,  # Note: typo in model field name
                )
                messages.success(request, 'Profile created successfully!')
                
        except Exception as e:
            messages.error(request, f'Error saving profile: {str(e)}')
        
        # Redirect to dashboard without payment_success parameter to reset payment status
        return redirect('dashboard:dashboard')
    
    # Get existing profile data to populate form
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        profile_data = {
            'username': user_profile.username,
            'country': user_profile.country,
            'university': user_profile.university,  # Note: typo in model field name
            'profile_picture': user_profile.profile_picture if user_profile.profile_picture else None,
            'updated_at': user_profile.updated_at if user_profile.updated_at else None,
        }
        # Get social media accounts
        social_accounts = {
            'instagram': user_profile.instagram,
            'facebook': user_profile.facebook,
            'twitter': user_profile.twitter,  # Now stored in database
            'linkedin': user_profile.linkedin
        }
        # Use per-analysis payment status (pay-per-analysis model)
        current_analysis_paid = request.session.get('current_analysis_paid', False)
        # Check if this is a payment success redirect
        user_profile_exists = True
        payment_success_redirect = request.GET.get('payment_success') == '1'
        if payment_success_redirect:
            # Mark current analysis as paid
            request.session['current_analysis_paid'] = True
            current_analysis_paid = True
        # If there's analysis data but payment_success in URL, it means user ran new analysis
        # after payment - we should ignore the payment_success parameter and use session value
        if instagram_analysis is not None and payment_success_redirect:
            # Check if this is actually a new analysis (session was reset to False)
            session_payment_status = request.session.get('current_analysis_paid', False)
            if not session_payment_status:
                # This is a new analysis after payment, ignore URL parameter
                current_analysis_paid = False
        payment_completed = current_analysis_paid
    except UserProfile.DoesNotExist:
        user_profile = None
        user_profile_exists = False
        profile_data = {
            'username': '',
            'country': '',
            'university': '',
        }
        social_accounts = {
            'instagram': None,
            'facebook': None,
            'twitter': user_profile.twitter,  # Now stored in database
            'linkedin': None
        }
        current_analysis_paid = False
        payment_completed = False

    if request.GET.get('clear_session') == '1':
        request.session.flush()
        return redirect('/dashboard/')
    
    
    payment_completed = current_analysis_paid

    context = {
        'user': request.user,
    }
    # Get social media accounts
    # Only use user_profile if it exists
    if user_profile:
        social_accounts = {
            'instagram': user_profile.instagram,
            'facebook': user_profile.facebook,
            'twitter': user_profile.twitter,  # Now stored in database
            'linkedin': user_profile.linkedin
        }
    else:
        social_accounts = {
            'instagram': None,
            'facebook': None,
            'twitter': user_profile.twitter,  # Now stored in database
            'linkedin': None
        }

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        profile_data = {
            'username': user_profile.username,
            'country': user_profile.country,
            'university': user_profile.university,
            'profile_picture': user_profile.profile_picture,
        }
    except UserProfile.DoesNotExist:
        profile_data = {
            'username': '',
            'country': '',
            'university': '',
        }
        social_accounts = {
            'instagram': None,
            'facebook': None,
            'twitter': user_profile.twitter,  # Now stored in database
            'linkedin': None
        }

# Check for session clear parameter (for testing)
    if request.GET.get('clear_session') == '1':
        request.session.flush()
        return redirect('/dashboard/')

    current_analysis_paid = request.session.get('current_analysis_paid', False)

    payment_success_redirect = request.GET.get('payment_success') == '1'
    if payment_success_redirect:
        request.session['current_analysis_paid'] = True
        current_analysis_paid = True

    if instagram_analysis is not None and payment_success_redirect:
        session_payment_status = request.session.get('current_analysis_paid', False)
        if not session_payment_status:
            current_analysis_paid = False
    # if not payment_success_redirect and request.method == 'GET':
    #     # Clear all analysis-related session data on direct dashboard visits
    #     request.session.pop('instagram_analysis', None)
    #     request.session.pop('linkedin_analysis', None)
    #     request.session.pop('current_analysis_paid', None)
    #     request.session.pop('analysis_timestamp', None)
    #     instagram_analysis = None
    #     linkedin_analysis = None
    #     current_analysis_paid = False
    payment_completed = current_analysis_paid

    instagram_loading = bool(request.session.get('analysis_started', False)) and not bool(instagram_analysis)
    # Show analysis results if ANY platform is done, not just all
    analysis_complete = (
        (request.session.get('instagram_analysis') is not None and len(request.session.get('instagram_analysis')) > 0)
        or (request.session.get('linkedin_analysis') is not None and len(request.session.get('linkedin_analysis')) > 0)
        or (twitter_analysis is not None and twitter_analysis != [] and not twitter_loading)
        or (request.session.get('facebook_analysis') is not None and len(request.session.get('facebook_analysis')) > 0)
    )
    
    # Calculate preview stats for blurred preview section
    preview_stats = {
        'total_posts': 0,
        'platforms_analyzed': 0,
        'risk_level': 'none',  # 'none', 'moderate', 'high'
        'risk_icon': '',
        'risk_text': '',
        'risk_color': ''
    }
    
    try:
        if analysis_complete:
            # Count posts per platform (with safe defaults)
            instagram_count = 0
            linkedin_count = 0
            twitter_count = 0
            facebook_count = 0
            
            try:
                instagram_analysis_data = request.session.get('instagram_analysis', [])
                instagram_count = len(instagram_analysis_data) if isinstance(instagram_analysis_data, list) else 0
            except:
                pass
            
            try:
                linkedin_analysis_data = request.session.get('linkedin_analysis', [])
                linkedin_count = len(linkedin_analysis_data) if isinstance(linkedin_analysis_data, list) else 0
            except:
                pass
            
            try:
                twitter_count = len(twitter_analysis) if twitter_analysis and isinstance(twitter_analysis, list) else 0
            except:
                pass
            
            try:
                facebook_analysis_data = request.session.get('facebook_analysis', [])
                facebook_count = len(facebook_analysis_data) if isinstance(facebook_analysis_data, list) else 0
            except:
                pass
            
            preview_stats['total_posts'] = instagram_count + linkedin_count + twitter_count + facebook_count
            
            # Debug logging for post counts
            print(f"📊 Post counts per platform:")
            print(f"   Instagram: {instagram_count}")
            print(f"   LinkedIn: {linkedin_count}")
            print(f"   Twitter: {twitter_count}")
            print(f"   Facebook: {facebook_count}")
            print(f"   TOTAL: {preview_stats['total_posts']}")
            
            # Count platforms analyzed (all connected platforms that returned results)
            platforms_with_results = []
            if instagram_count > 0:
                platforms_with_results.append('Instagram')
            if linkedin_count > 0:
                platforms_with_results.append('LinkedIn')
            if twitter_count > 0:
                platforms_with_results.append('Twitter/X')
            if facebook_count > 0:
                platforms_with_results.append('Facebook')
            
            preview_stats['platforms_analyzed'] = len(platforms_with_results)
            print(f"   Platforms with results: {platforms_with_results}")
            
            # Determine risk level based on highest risk score across all platforms
            max_risk_score = 0
            all_risk_scores = []
            
            # Instagram
            try:
                for post in request.session.get('instagram_analysis', []):
                    if isinstance(post, dict) and 'analysis' in post and 'Instagram' in post['analysis']:
                        score = post['analysis']['Instagram'].get('risk_score', 0)
                        if score is not None and score >= 0:
                            all_risk_scores.append(score)
                            if score > max_risk_score:
                                max_risk_score = score
            except Exception as e:
                print(f"⚠️  Error reading Instagram risk scores: {e}")
            
            # LinkedIn
            try:
                for post in request.session.get('linkedin_analysis', []):
                    if isinstance(post, dict) and 'analysis' in post and 'LinkedIn' in post['analysis']:
                        score = post['analysis']['LinkedIn'].get('risk_score', 0)
                        if score is not None and score >= 0:
                            all_risk_scores.append(score)
                            if score > max_risk_score:
                                max_risk_score = score
            except Exception as e:
                print(f"⚠️  Error reading LinkedIn risk scores: {e}")
            
            # Twitter
            try:
                if twitter_analysis and isinstance(twitter_analysis, list):
                    for post in twitter_analysis:
                        if isinstance(post, dict) and 'analysis' in post and 'Twitter' in post['analysis']:
                            score = post['analysis']['Twitter'].get('risk_score', 0)
                            if score is not None and score >= 0:
                                all_risk_scores.append(score)
                                if score > max_risk_score:
                                    max_risk_score = score
            except Exception as e:
                print(f"⚠️  Error reading Twitter risk scores: {e}")
            
            # Facebook
            try:
                for post in request.session.get('facebook_analysis', []):
                    if isinstance(post, dict) and 'analysis' in post and 'Facebook' in post['analysis']:
                        score = post['analysis']['Facebook'].get('risk_score', 0)
                        if score is not None and score >= 0:
                            all_risk_scores.append(score)
                            if score > max_risk_score:
                                max_risk_score = score
            except Exception as e:
                print(f"⚠️  Error reading Facebook risk scores: {e}")
            
            # Debug: Log risk scores found
            print(f"🎯 Risk Score Analysis:")
            print(f"   All scores found: {all_risk_scores}")
            print(f"   Max risk score: {max_risk_score}")
            print(f"   Avg risk score: {sum(all_risk_scores) / len(all_risk_scores) if all_risk_scores else 0:.1f}")
            
            # Set risk level and display info (based on max risk score)
            # Thresholds: <4 = low (green), 4-6 = moderate (yellow), >=7 = high (red)
            if max_risk_score >= 7:
                preview_stats['risk_level'] = 'high'
                preview_stats['risk_icon'] = 'fa-exclamation-triangle'
                preview_stats['risk_text'] = 'High Risk Detected'
                preview_stats['risk_color'] = 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400'
            elif max_risk_score >= 4:
                preview_stats['risk_level'] = 'moderate'
                preview_stats['risk_icon'] = 'fa-flag'
                preview_stats['risk_text'] = 'Risk Detected'
                preview_stats['risk_color'] = 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-600 dark:text-yellow-400'
            else:
                # Low risk - show green badge
                preview_stats['risk_level'] = 'low'
                preview_stats['risk_icon'] = 'fa-check-circle'
                preview_stats['risk_text'] = 'Low Risk'
                preview_stats['risk_color'] = 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-600 dark:text-green-400'
            
            print(f"   Risk Classification: {preview_stats['risk_level'].upper()} ({preview_stats['risk_text']})")
    except Exception as e:
        print(f"⚠️  Preview stats calculation error (non-critical): {e}")
        # Use safe defaults on error
    

    config = Config.objects.first()  # Always fetch latest config
    # Always provide a non-empty Stripe publishable key for Stripe.js
    if config:
        if config.live and config.STRIPE_PUBLISHABLE_KEY_LIVE:
            stripe_publishable_key = config.STRIPE_PUBLISHABLE_KEY_LIVE
        elif not config.live and config.STRIPE_PUBLISHABLE_KEY_TEST:
            stripe_publishable_key = config.STRIPE_PUBLISHABLE_KEY_TEST
        else:
            stripe_publishable_key = 'pk_test_placeholder'  # fallback test key or show error
    else:
        stripe_publishable_key = 'pk_test_placeholder'  # fallback test key or show error
    # DEBUG: Log template context for troubleshooting
    print(f"\n{'='*80}")
    print(f"🔍 DASHBOARD TEMPLATE CONTEXT DEBUG")
    print(f"{'='*80}")
    print(f"  analysis_complete: {analysis_complete}")
    print(f"  payment_completed: {payment_completed}")
    print(f"  preview_stats: {preview_stats}")
    print(f"  twitter_analysis: {len(request.session.get('twitter_analysis', [])) if isinstance(request.session.get('twitter_analysis'), list) else 'Not a list'}")
    print(f"  Should show blurred preview: {analysis_complete and not payment_completed}")
    print(f"{'='*80}\n")
    
    context = {
        'user': request.user,
        'user_email': request.user.email,
        'is_authenticated': request.user.is_authenticated,
        'profile_data': profile_data,
        'social_accounts': social_accounts,
        'stripe_publishable_key': stripe_publishable_key,
        'payment_completed': payment_completed,
        'analysis_complete': analysis_complete,
        'instagram_analysis': request.session.get('instagram_analysis'),
        'linkedin_analysis': request.session.get('linkedin_analysis'),
        'twitter_analysis': request.session.get("twitter_analysis"),
        'twitter_loading': twitter_loading,
        'instagram_loading': instagram_loading,
        'price': config.price_dollars if config else 0,
        'price_cents': config.Price if config else 0,
        'facebook_analysis': request.session.get('facebook_analysis'),
        'profile': UserProfile.objects.get(user=request.user),
        'preview_stats': preview_stats,
    }

    return render(request, 'dashboard/dashboard.html', context)

# views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def disable_first_login(request):
    if request.method == "POST":
        profile = request.user.userprofile
        profile.first_login = False
        profile.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

@login_required
def debug_endpoints(request):
    """Debug view to test if endpoints are working correctly"""
    import json
    from django.http import JsonResponse
    
    debug_info = {
        'user_authenticated': request.user.is_authenticated,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'request_method': request.method,
        'request_path': request.path,
        'server_name': request.META.get('SERVER_NAME', 'Unknown'),
        'http_host': request.META.get('HTTP_HOST', 'Unknown'),
        'csrf_token_present': 'csrftoken' in request.COOKIES,
        'session_key': request.session.session_key,
        'content_type': request.content_type,
        'headers': dict(request.headers),
    }
    
    try:
        user_profile = request.user.userprofile
        debug_info['profile_exists'] = True
        debug_info['social_accounts'] = {
            'instagram': user_profile.instagram,
            'facebook': user_profile.facebook, 
            'twitter': user_profile.twitter,  # Now stored in database
            'linkedin': user_profile.linkedin
        }
    except:
        debug_info['profile_exists'] = False
        debug_info['social_accounts'] = None
    
    return JsonResponse({
        'success': True,
        'message': 'Debug endpoint working correctly',
        'debug_info': debug_info
    })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def disconnect_social_account(request):
    """AJAX endpoint to disconnect a social account for the current user."""
    try:
        data = json.loads(request.body)
        platform = data.get('platform')
        if platform not in ['instagram', 'facebook', 'twitter', 'linkedin']:
            return JsonResponse({'success': False, 'error': 'Invalid platform'})
        
        # All platforms now use database storage
        user_profile = UserProfile.objects.get(user=request.user)
        setattr(user_profile, platform, None)
        # Also update the {platform}_connected flag
        setattr(user_profile, f'{platform}_connected', False)
        user_profile.save()
        return JsonResponse({'success': True})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_social_accounts(request):
    """Get user's connected social media accounts"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        accounts = {
            'instagram': user_profile.instagram,
            'facebook': user_profile.facebook,
            'twitter': user_profile.twitter,  # Now stored in database
            'linkedin': user_profile.linkedin
        }
        return JsonResponse({
            'success': True,
            'accounts': accounts
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': True,
            'accounts': {
                'instagram': None,
                'facebook': None,
                'twitter': None,
                'linkedin': None
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error retrieving accounts: {str(e)}'
        })

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def connect_social_account(request):
    """AJAX endpoint to connect a social account for the current user."""
    try:
        data = json.loads(request.body)
        platform = data.get('platform')
        username = data.get('username')
        if platform not in ['instagram', 'facebook', 'twitter', 'linkedin']:
            return JsonResponse({'success': False, 'message': 'Invalid platform'})
        if not username:
            return JsonResponse({'success': False, 'message': 'Username is required'})
        
        # All platforms now use database storage
        user_profile = UserProfile.objects.get(user=request.user)
        setattr(user_profile, platform, username)
        # Also update the {platform}_connected flag
        setattr(user_profile, f'{platform}_connected', True)
        user_profile.save()
        
        platform_name = 'X (Twitter)' if platform == 'twitter' else platform.title()
        return JsonResponse({'success': True, 'message': f'{platform_name} account connected successfully!'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
@login_required
def result_view(request):
    # Enforce payment check before showing results
    if not request.session.get('current_analysis_paid', False):
        return redirect(reverse('dashboard:dashboard'))

    from django.core.cache import cache
    user_id = request.user.id

    # Helper to fetch from cache and set in session if missing
    def get_or_set_analysis(platform):
        session_key = f'{platform}_analysis'
        analysis = request.session.get(session_key)
        if analysis is None:
            cache_key = f'{platform}_analysis_{user_id}'
            analysis = cache.get(cache_key)
            if analysis is not None:
                request.session[session_key] = analysis
        return analysis
    
    # Helper to fetch profile summaries from cache
    def get_profile_summary(platform):
        cache_key = f'{platform}_profile_{user_id}'
        return cache.get(cache_key)

    twitter_analysis = get_or_set_analysis('twitter')
    if twitter_analysis is None:
        twitter_analysis = []
    print(twitter_analysis)

    instagram_analysis = get_or_set_analysis('instagram')
    if instagram_analysis is None:
        instagram_analysis = []
    print('DEBUG: instagram_analysis from session:', request.session.get('instagram_analysis'))
    from django.core.cache import cache as debug_cache
    print('DEBUG: instagram_analysis from cache:', debug_cache.get(f'instagram_analysis_{user_id}'))
    print('DEBUG: instagram_analysis final value:', instagram_analysis)
    
    # Log first result for verification
    if instagram_analysis and isinstance(instagram_analysis, list) and len(instagram_analysis) > 0:
        first_item = instagram_analysis[0]
        print(f"\n{'='*80}")
        print(f"📊 INSTAGRAM FIRST POST AI ANALYSIS PREVIEW (first 200 chars):")
        print(f"{'='*80}")
        if 'analysis' in first_item and 'Instagram' in first_item['analysis']:
            analysis_preview = json.dumps(first_item['analysis']['Instagram'], indent=2)[:200]
            print(f"{analysis_preview}...")
        print(f"{'='*80}\n")

    linkedin_analysis = get_or_set_analysis('linkedin')
    if linkedin_analysis is None:
        linkedin_analysis = []
    print('DEBUG: linkedin_analysis from session:', request.session.get('linkedin_analysis'))
    print('DEBUG: linkedin_analysis final value:', linkedin_analysis)
    
    # Log first result for verification
    if linkedin_analysis and isinstance(linkedin_analysis, dict) and 'linkedin' in linkedin_analysis:
        posts = linkedin_analysis['linkedin']
        if posts and isinstance(posts, list) and len(posts) > 0:
            first_item = posts[0]
            print(f"\n{'='*80}")
            print(f"📊 LINKEDIN FIRST POST AI ANALYSIS PREVIEW (first 200 chars):")
            print(f"{'='*80}")
            if 'analysis' in first_item and 'LinkedIn' in first_item['analysis']:
                analysis_preview = json.dumps(first_item['analysis']['LinkedIn'], indent=2)[:200]
                print(f"{analysis_preview}...")
            print(f"{'='*80}\n")

    facebook_analysis = get_or_set_analysis('facebook')
    print(facebook_analysis)
    if facebook_analysis is None:
        facebook_analysis = []

    # If data is coming as a string (JSON), parse it
    if isinstance(twitter_analysis, str):
        # Handle markdown-wrapped JSON
        clean_data = None
        if twitter_analysis:
            if twitter_analysis.startswith("```json") or twitter_analysis.startswith("``` json"):
                clean_data = twitter_analysis.strip("`")  # remove leading/trailing backticks
                clean_data = clean_data.replace("json", "", 1).strip()  # remove 'json' right after ```
            else:
                clean_data = twitter_analysis.strip()
        
        if clean_data is None:
            twitter_analysis = []
        else:
            twitter_analysis = clean_data
        try:
            twitter_analysis = json.loads(twitter_analysis)
            # If it's a dict with a 'Twitter' key, extract the list
            if isinstance(twitter_analysis, dict) and 'Twitter' in twitter_analysis:
                twitter_analysis = twitter_analysis['Twitter']
        except json.JSONDecodeError:
            twitter_analysis = []
    
    if not isinstance(twitter_analysis, list):
        twitter_analysis = [twitter_analysis]
    
    # Sort all platforms chronologically (most recent → oldest)
    def sort_posts_chronologically(posts):
        """Sort posts by created_at timestamp, most recent first."""
        if not posts or not isinstance(posts, list):
            return posts
        
        def get_timestamp(post):
            """Extract timestamp from post, handling various field names and formats."""
            if not isinstance(post, dict):
                return 0
            
            # Try different timestamp field names
            timestamp_str = (
                post.get('created_at') or 
                post.get('timestamp') or 
                post.get('created_time') or 
                post.get('date') or 
                post.get('postedAt') or
                ''
            )
            
            if not timestamp_str:
                return 0
            
            try:
                from dateutil import parser
                dt = parser.parse(timestamp_str)
                return dt.timestamp()
            except:
                return 0
        
        return sorted(posts, key=get_timestamp, reverse=True)
    
    # Apply chronological sorting to all platforms
    instagram_analysis = sort_posts_chronologically(instagram_analysis)
    facebook_analysis = sort_posts_chronologically(facebook_analysis)
    twitter_analysis = sort_posts_chronologically(twitter_analysis)
    linkedin_analysis = sort_posts_chronologically(linkedin_analysis)
    
    # Calculate stats
    safe_count = 0
    caution_count = 0
    warning_count = 0
    for item in twitter_analysis:
        try:
            # Correct data structure: item['analysis']['Twitter']
            if isinstance(item, dict) and 'analysis' in item and 'Twitter' in item['analysis']:
                risk_score = item['analysis']['Twitter'].get('risk_score', 0)
                if risk_score == 0:
                    safe_count += 1
                elif 1 <= risk_score <= 2:
                    caution_count += 1
                elif risk_score >= 3:
                    warning_count += 1
        except (KeyError, TypeError):
            continue
    
    # Fetch profile summaries
    instagram_profile = get_profile_summary('instagram')
    linkedin_profile = get_profile_summary('linkedin')
    twitter_profile = get_profile_summary('twitter')
    facebook_profile = get_profile_summary('facebook')
    
    context = {
        'twitter_analyses': twitter_analysis,
        'safe_count': safe_count,
        'caution_count': caution_count,
        'warning_count': warning_count,
        'instagram_analysis': instagram_analysis,
        'instagram_profile': instagram_profile,
        'linkedin_analysis': linkedin_analysis,
        'linkedin_profile': linkedin_profile,
        'facebook_analysis': facebook_analysis,
        'facebook_profile': facebook_profile,
        'twitter_profile': twitter_profile,
      }
    return render(request, 'dashboard/result.html', context) 

# PDF export view for dashboard results
@login_required
def export_pdf_view(request):
    from django.core.cache import cache
    from datetime import datetime
    
    user_id = request.user.id
    user_profile = request.user.userprofile
    
    def get_or_set_analysis(platform):
        session_key = f'{platform}_analysis'
        analysis = request.session.get(session_key)
        if analysis is None:
            cache_key = f'{platform}_analysis_{user_id}'
            analysis = cache.get(cache_key)
            if analysis is not None:
                request.session[session_key] = analysis
        return analysis
    
    twitter_analysis = get_or_set_analysis('twitter')
    instagram_analysis = get_or_set_analysis('instagram')
    linkedin_analysis = get_or_set_analysis('linkedin')
    facebook_analysis = get_or_set_analysis('facebook')
    
    # Calculate overall risk score
    total_risk = 0
    platform_count = 0
    
    if instagram_analysis:
        platform_count += 1
    if linkedin_analysis:
        platform_count += 1
    if twitter_analysis:
        platform_count += 1
    if facebook_analysis:
        platform_count += 1
    
    context = {
        'user': request.user,
        'report_date': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        'instagram_username': user_profile.instagram or 'Not connected',
        'linkedin_username': user_profile.linkedin or 'Not connected',
        # 'twitter_username': 'Not connected',  # twitter field removed from model
        'facebook_username': user_profile.facebook or 'Not connected',
        'twitter_analyses': twitter_analysis,
        'instagram_analysis': instagram_analysis,
        'linkedin_analysis': linkedin_analysis,
        'facebook_analysis': facebook_analysis,
        'platform_count': platform_count,
    }
    
    html_string = render_to_string('dashboard/pdf_report.html', context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="VisaGuardAI_Report_{request.user.username}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    pisa_status = pisa.CreatePDF(
        html_string, dest=response
    )
    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)
    return response

@login_required
def change_password(request):
    if request.method == 'POST':
        user = request.user
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_new_password = request.POST.get('confirm_new_password', '').strip()
        context = {}

        # Check current password
        if not user.check_password(current_password):
            context['pw_change_error'] = 'Current password is incorrect.'
        elif new_password != confirm_new_password:
            context['pw_change_error'] = 'New passwords do not match.'
        else:
            try:
                validate_password(new_password, user)
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Prevent logout after password change
                context['pw_change_success'] = 'Password changed successfully.'
            except PasswordValidationError as e:
                context['pw_change_error'] = ' '.join(e.messages)
            except Exception as e:
                context['pw_change_error'] = 'Error updating password: {}'.format(str(e))

        # Render settings page with feedback
        # Re-populate context as in setting_view
        try:
            user_profile = UserProfile.objects.get(user=user)
            profile_data = {
                'username': user_profile.username,
                'country': user_profile.country,
                'university': user_profile.university,
                'profile_picture': user_profile.profile_picture,
            }
            social_accounts = {
                'instagram': user_profile.instagram,
                'facebook': user_profile.facebook,
                'twitter': user_profile.twitter,  # Now stored in database
                'linkedin': user_profile.linkedin,
            }
            full_name = f"{user.first_name} {user.last_name}".strip()
        except UserProfile.DoesNotExist:
            profile_data = {'username': '', 'country': '', 'university': '', 'profile_picture': None}
            social_accounts = {'instagram': None, 'facebook': None, 'twitter': request.session.get('twitter_username'), 'linkedin': None}
            full_name = ''
        context.update({
            'user': user,
            'profile_data': profile_data,
            'social_accounts': social_accounts,
            'full_name': full_name,
        })
        return render(request, 'dashboard/settings.html', context)

@login_required
def setting_view(request):
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username', '').strip()
            country = request.POST.get('country', '').strip()
            university = request.POST.get('university', '').strip()
            full_name = request.POST.get('fullName', '').strip()
            
            instagram_username = request.POST.get('instagramUsername', '').strip()
            facebook_username = request.POST.get('facebookUsername', '').strip()
            twitter_username = request.POST.get('twitterUsername', '').strip()
            linkedin_username = request.POST.get('linkedinUsername', '').strip()
            
            # Profile image
            profile_image = request.FILES.get('profile_image')
            
            # Validate image size (max 2MB)
            if profile_image and profile_image.size > 2 * 1024 * 1024:
                messages.error(request, "Image size must be less than 2MB.")
                raise ValueError('Image size exceeds 2MB')
            
            # Validate required fields
            if not username:
                messages.error(request, 'Username is required.')
                return redirect('dashboard:setting')
            
            if not country:
                messages.error(request, 'Country is required.')
                return redirect('dashboard:setting')
            
            # Get or create user profile
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                # Update existing profile
                user_profile.username = username
                user_profile.country = country
                user_profile.university = university
                
                # Update social media accounts
                user_profile.instagram = instagram_username if instagram_username else None
                user_profile.facebook = facebook_username if facebook_username else None
                # user_profile.twitter removed - field no longer exists in model
                user_profile.linkedin = linkedin_username if linkedin_username else None
                
                # Update profile image if provided
                if profile_image:
                    user_profile.profile_picture = profile_image
                
                user_profile.save()
                messages.success(request, 'Settings updated successfully!')
                
            except UserProfile.DoesNotExist:
                # Create new profile
                user_profile = UserProfile.objects.create(
                    user=request.user,
                    username=username,
                    country=country,
                    university=university,
                    instagram=instagram_username if instagram_username else None,
                    facebook=facebook_username if facebook_username else None,
                    twitter=twitter_username if twitter_username else None,
                    linkedin=linkedin_username if linkedin_username else None,
                    profile_picture=profile_image if profile_image else None,
                )
                messages.success(request, 'Profile created successfully!')
            
            # Update user's first_name and last_name if full_name is provided
            if full_name:
                name_parts = full_name.split(' ', 1)
                request.user.first_name = name_parts[0]
                request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                request.user.save()
                
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
        
        return redirect('dashboard:setting')
    
    # GET request - populate form with existing data
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        profile_data = {
            'username': user_profile.username,
            'country': user_profile.country,
            'university': user_profile.university,
            'profile_picture': user_profile.profile_picture,
        }
        # Get social media accounts
        social_accounts = {
            'instagram': user_profile.instagram,
            'facebook': user_profile.facebook,
            # 'twitter': None,  # twitter field removed from model
            'linkedin': user_profile.linkedin,
        }
    except UserProfile.DoesNotExist:
        profile_data = {
            'username': request.user.username or '',
            'country': '',
            'university': '',
            'profile_picture': None,
        }
        social_accounts = {
            'instagram': None,
            'facebook': None,
            'twitter': None,
            'linkedin': None,
        }
    
    # Get full name from User model
    full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    
    context = {
        'user': request.user,
        'user_email': request.user.email,
        'is_authenticated': request.user.is_authenticated,
        'profile_data': profile_data,
        'social_accounts': social_accounts,
        'full_name': full_name,
    }
    
    return render(request, 'dashboard/settings.html', context)
@login_required
def payment_view(request):
    config = Config.objects.first()
    if not config:
        return JsonResponse({'error': 'System configuration not found. Please contact administrator.'}, status=500)
    
    stripe.api_key = config.STRIPE_SECRET_KEY_LIVE if config.live else config.STRIPE_SECRET_KEY_TEST
    if request.method == 'POST':
        try:
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Visa Application Analysis',
                        },
                        'unit_amount': config.Price,  # $15.00 in cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri('/dashboard/payment-success/'),
                cancel_url=request.build_absolute_uri('/dashboard/payment-cancel/'),
                customer_email=request.user.email,  # Pre-populate user's email
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)})

    context = {
        'stripe_public_key': config.STRIPE_PUBLISHABLE_KEY_LIVE if config.live else config.STRIPE_PUBLISHABLE_KEY_TEST,
        'user': request.user
    }
    return render(request, 'payment.html', context)

# @login_required
# def payment_success(request):
#     profile = request.user.userprofile
#     profile.payment_completed = True
#     profile.save()
#     return redirect(reverse('index:dashboard') + '?payment_success=1&show_results=1')


@login_required
def payment_success(request):
    profile = request.user.userprofile
    profile.payment_completed = True
    profile.save()
    request.session['current_analysis_paid'] = True
    messages.success(request, "Payment successful! Your full analysis is now available.")
    return redirect(reverse('dashboard:result'))

@login_required
def payment_cancel(request):
    return redirect(reverse('dashboard:dashboard'))




@login_required
@csrf_exempt
@require_http_methods(["POST"])
def reset_payment_status(request):
    """AJAX endpoint to reset payment_completed to False for new analysis."""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.payment_completed = False
        user_profile.save()
        return JsonResponse({'success': True})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def data_deletion_view(request):
    """View for data deletion confirmation page"""
    return render(request, 'dashboard/data_deletion.html')


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def confirm_data_deletion(request):
    """
    Handle data deletion confirmation with password verification.
    Includes option for full account deletion vs data-only deletion.
    """
    try:
        if not request.body:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid request data'
            }, status=400)
        
        data = json.loads(request.body)
        
        # Validate required fields
        password = data.get('password', '').strip()
        delete_account = data.get('delete_account', False)  # True for full account, False for data only
        confirmation = data.get('confirmation', '').strip()
        
        if not password:
            return JsonResponse({
                'success': False,
                'error': 'Password is required'
            })
        
        if confirmation.lower() not in ['yes', 'delete', 'confirm']:
            return JsonResponse({
                'success': False,
                'error': 'Please type "YES" to confirm deletion'
            })
        
        # Verify password
        user = authenticate(username=request.user.username, password=password)
        if not user or user != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Incorrect password'
            })
        
        # Perform deletion in a transaction for safety
        with transaction.atomic():
            deleted_data = []
            
            if delete_account:
                # Full account deletion - this will cascade delete related data
                username = user.username
                email = user.email
                
                # Delete user (this cascades to UserProfile, AnalysisSession, AnalysisResult)
                user.delete()
                
                deleted_data.append(f"Full account deleted for {username} ({email})")
                
                # Log deletion for audit purposes
                print(f"🔴 FULL ACCOUNT DELETION: {username} ({email}) at {timezone.now()}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Account and all data deleted successfully',
                    'redirect_url': '/auth/login/',
                    'full_deletion': True
                })
            
            else:
                # Data-only deletion - keep account but remove analysis data
                username = user.username
                
                # Delete UserProfile data
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    
                    # Clear social media usernames
                    user_profile.instagram = None
                    user_profile.linkedin = None
                    user_profile.twitter = None
                    user_profile.facebook = None
                    user_profile.tiktok = None
                    user_profile.instagram_connected = False
                    user_profile.linkedin_connected = False
                    user_profile.twitter_connected = False
                    user_profile.facebook_connected = False
                    user_profile.tiktok_connected = False
                    
                    # Clear optional data
                    user_profile.country = None
                    user_profile.university = None
                    
                    # Delete profile picture file
                    if user_profile.profile_picture:
                        try:
                            if os.path.isfile(user_profile.profile_picture.path):
                                os.remove(user_profile.profile_picture.path)
                        except Exception as e:
                            print(f"Could not delete profile picture: {e}")
                        user_profile.profile_picture = None
                    
                    user_profile.save()
                    deleted_data.append("User profile data cleared")
                    
                except UserProfile.DoesNotExist:
                    pass
                
                # Delete AnalysisResults
                analysis_results = AnalysisResult.objects.filter(user=user)
                result_count = analysis_results.count()
                analysis_results.delete()
                if result_count > 0:
                    deleted_data.append(f"{result_count} analysis result(s) deleted")
                
                # Delete AnalysisSessions
                analysis_sessions = AnalysisSession.objects.filter(user=user)
                session_count = analysis_sessions.count()
                analysis_sessions.delete()
                if session_count > 0:
                    deleted_data.append(f"{session_count} analysis session(s) deleted")
                
                # Clear session data (if still active)
                for key in list(request.session.keys()):
                    if 'analysis' in key.lower() or 'social' in key.lower():
                        del request.session[key]
                
                deleted_data.append("Session data cleared")
                
                # Log deletion for audit purposes
                print(f"🟡 DATA DELETION: {username} at {timezone.now()}, removed: {', '.join(deleted_data)}")
                
                return JsonResponse({
                    'success': True,
                    'message': f'Your data has been deleted: {", ".join(deleted_data)}',
                    'deleted_items': deleted_data,
                    'full_deletion': False
                })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        print(f"Error during data deletion: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred during deletion. Please try again or contact support.'
        }, status=500)