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
            try:
                user = User.objects.get(email__iexact=email)
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
                
                try:
                    send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, [email])
                    message = f'A password reset link has been sent to {email}. Please check your email and follow the instructions.'
                    message_type = 'success'
                except Exception as e:
                    print(f"Email sending error: {e}")
                    message = 'There was an error sending the password reset email. Please try again later or contact support.'
                    message_type = 'error'
                    
            except User.DoesNotExist:
                # Don't reveal that email doesn't exist for security
                message = 'If an account with that email exists, a password reset link has been sent.'
                message_type = 'info'
    
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

def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('auth:login')  # Use namespaced URL
    return render(request, 'setting.html')