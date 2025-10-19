from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from django.urls import reverse

# Import for handling Google Allauth accounts
try:
    from allauth.account.models import EmailAddress
    ALLAUTH_AVAILABLE = True
except ImportError:
    ALLAUTH_AVAILABLE = False

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('auth:login')
    return render(request, 'auth/login.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            login(request, user)
            return redirect('dashboard:dashboard')
    return render(request, 'auth/signup.html')

def logout_view(request):
    logout(request)
    return redirect('auth:login')

def forgot_password_view(request):
    message = None
    message_type = None
    
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            message = 'Please enter your email address.'
            message_type = 'error'
        else:
            user = None
            account_type = None
            
            # First, try to find a regular Django User account
            try:
                user = User.objects.get(email__iexact=email)
                
                # Check if this Django user is actually an OAuth user
                if ALLAUTH_AVAILABLE:
                    try:
                        from allauth.socialaccount.models import SocialAccount
                        if SocialAccount.objects.filter(user=user).exists():
                            account_type = 'allauth'
                            print(f"Found Django user with social account for {email}")
                        else:
                            account_type = 'django'
                            print(f"Found regular Django user for {email}")
                    except:
                        account_type = 'django'
                        print(f"Found Django user for {email}")
                else:
                    account_type = 'django'
                    print(f"Found Django user for {email}")
            except User.DoesNotExist:
                # If no Django user, check if it's a Google Allauth account
                if ALLAUTH_AVAILABLE:
                    try:
                        # Try both verified and unverified email addresses
                        email_addr = EmailAddress.objects.filter(email__iexact=email).first()
                        if email_addr:
                            user = email_addr.user
                            account_type = 'allauth'
                            print(f"Found Allauth user for {email}")
                    except Exception as e:
                        print(f"Error checking Allauth: {e}")
                
                # Also check if user exists but has social accounts (another way to detect OAuth)
                if not user:
                    try:
                        from allauth.socialaccount.models import SocialAccount
                        social_user = SocialAccount.objects.filter(user__email__iexact=email).first()
                        if social_user:
                            user = social_user.user
                            account_type = 'allauth'
                            print(f"Found social account user for {email}")
                    except Exception as e:
                        print(f"Error checking social accounts: {e}")
            
            if user and account_type == 'django':
                # Handle regular Django User accounts - allow password reset
                try:
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    reset_url = request.build_absolute_uri(
                        reverse('auth:reset_password', kwargs={'uidb64': uid, 'token': token})
                    )
                    subject = 'Password Reset Request - VisaGuardAI'
                    email_message = render_to_string('auth/password_reset_email.txt', {
                        'user': user,
                        'reset_url': reset_url,
                        'site_name': 'VisaGuardAI',
                    })
                    
                    # Check if email service is properly configured before attempting to send
                    if not settings.EMAIL_HOST_PASSWORD:
                        print("No EMAIL_HOST_PASSWORD configured - skipping email send")
                        message = 'Password reset is temporarily unavailable due to email service configuration. Please contact support for assistance.'
                        message_type = 'error'
                    else:
                        try:
                            send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, [email])
                            message = f'A password reset link has been sent to {email}. Please check your email and follow the instructions.'
                            message_type = 'success'
                            print(f"Password reset email sent successfully to {email}")
                        except Exception as e:
                            print(f"Email sending error: {e}")
                            # Better error message for email issues
                            if 'authentication' in str(e).lower() or '530' in str(e):
                                message = 'Unable to send password reset email due to email service configuration. Please contact support for assistance.'
                            else:
                                message = 'There was a temporary issue sending the password reset email. Please try again in a few minutes or contact support.'
                            message_type = 'error'
                except Exception as e:
                    print(f"Password reset error: {e}")
                    message = 'Unable to generate password reset link. Please contact support.'
                    message_type = 'error'
                    
            elif user and account_type == 'allauth':
                # Handle Google Allauth accounts - redirect to create password page
                import hashlib
                token = hashlib.sha256(f"{email}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
                return redirect(f"{reverse('auth:create_password')}?email={email}&token={token}")
            else:
                # Don't reveal that email doesn't exist for security
                message = 'If an account with that email exists, a password reset link has been sent.'
                message_type = 'info'
    
    # Only render the template if we didn't redirect
    return render(request, 'auth/forgot_password.html', {'message': message, 'message_type': message_type})

def reset_password_view(request, uidb64, token):
    message = None
    message_type = None
    
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password', '').strip()
            confirm = request.POST.get('confirm_password', '').strip()
            
            if not password:
                message = 'Please enter a password.'
                message_type = 'error'
            elif len(password) < 8:
                message = 'Password must be at least 8 characters long.'
                message_type = 'error'
            elif password != confirm:
                message = 'Passwords do not match.'
                message_type = 'error'
            else:
                try:
                    from django.contrib.auth.password_validation import validate_password
                    validate_password(password, user)
                    user.set_password(password)
                    user.save()
                    messages.success(request, 'Your password has been reset successfully. You can now log in.')
                    return redirect('auth:login')
                except Exception as e:
                    message = f'Password validation failed: {", ".join(e.messages) if hasattr(e, "messages") else str(e)}'
                    message_type = 'error'
        
        return render(request, 'auth/reset_password.html', {
            'validlink': True, 
            'message': message, 
            'message_type': message_type
        })
    else:
        return render(request, 'auth/reset_password.html', {
            'validlink': False, 
            'message': 'The reset link is invalid or has expired.',
            'message_type': 'error'
        })

def create_password_view(request):
    """Create a password for Google OAuth users"""
    message = None
    message_type = None
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        token = request.POST.get('token', '').strip()
        
        if not all([email, password, confirm_password, token]):
            message = 'All fields are required.'
            message_type = 'error'
        elif password != confirm_password:
            message = 'Passwords do not match.'
            message_type = 'error'
        elif len(password) < 8:
            message = 'Password must be at least 8 characters long.'
            message_type = 'error'
        else:
            try:
                # Verify the user exists and has a Google account
                user = User.objects.get(email__iexact=email)
                
                # Check if this is actually a Google OAuth user
                if ALLAUTH_AVAILABLE:
                    try:
                        from allauth.socialaccount.models import SocialAccount
                        if not SocialAccount.objects.filter(user=user).exists():
                            message = 'Invalid request. This account is not eligible for password creation.'
                            message_type = 'error'
                        else:
                            # Validate the token (we'll use a simple email-based token for now)
                            import hashlib
                            expected_token = hashlib.sha256(f"{email}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
                            if token != expected_token:
                                message = 'Invalid token. Please try the forgot password process again.'
                                message_type = 'error'
                            else:
                                # Set the password
                                from django.contrib.auth.password_validation import validate_password
                                validate_password(password, user)
                                user.set_password(password)
                                user.save()
                                
                                # Redirect to login with success message
                                messages.success(request, 'Password created successfully! You can now log in with your email and password or continue using Google Sign-In.')
                                return redirect('auth:login')
                    except Exception as e:
                        print(f"Error checking social account: {e}")
                        message = 'Unable to verify account type. Please contact support.'
                        message_type = 'error'
                else:
                    message = 'Invalid request. Please contact support.'
                    message_type = 'error'
            except User.DoesNotExist:
                message = 'Account not found. Please contact support.'
                message_type = 'error'
            except Exception as e:
                print(f"Password creation error: {e}")
                if hasattr(e, 'messages'):
                    message = f'Password validation failed: {", ".join(e.messages)}'
                else:
                    message = 'Unable to create password. Please try again or contact support.'
                message_type = 'error'
    
    # For GET requests, get the email and token from query parameters or session
    elif request.method == 'GET':
        email = request.GET.get('email', '')
        token = request.GET.get('token', '')
    else:
        email = ''
        token = ''
    
    context = {
        'email': email,
        'token': token,
        'message': message,
        'message_type': message_type
    }
    
    return render(request, 'auth/create_password.html', context)

def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('auth:login')  # Use namespaced URL
    return render(request, 'setting.html')