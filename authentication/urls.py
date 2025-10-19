from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset/<uidb64>/<token>/', views.reset_password_view, name='reset_password'),
    path('create-password/', views.create_password_view, name='create_password'),
    path('profile/', views.profile_view, name='profile'),
]
