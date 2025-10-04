from django.contrib import admin
from django.urls import path

from .import views 
 # Import views from the current directory
app_name = 'dashboard'  # Change namespace to match the template

urlpatterns = [
    path('export-pdf/', views.export_pdf_view, name='export_pdf'),
    path('clear-analysis-session/', views.clear_analysis_session, name='clear_analysis_session'),
    path('', views.dashboard, name='dashboard'),  # Root dashboard URL
    path('results/', views.result_view, name='result'),
    path('settings/', views.setting_view, name='setting'),
    path('change-password/', views.change_password, name='change_password'),
    path("disable-first-login/", views.disable_first_login, name="disable_first_login"),

    # Social media account management
    path('disconnect-social-account/', views.disconnect_social_account, name='disconnect_social_account'),
    path('connect-social-account/', views.connect_social_account, name='connect_social_account'),
    path('get-social-accounts/', views.get_social_accounts, name='get_social_accounts'),
    
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('payment/', views.payment_view, name='payment_view'),
    path('reset-payment-status/', views.reset_payment_status, name='reset_payment_status'),

    path('start-analysis/', views.start_analysis, name='start_analysis'),
    path('check-analysis-progress/', views.check_analysis_progress, name='check_analysis_progress'),
    path('debug-endpoints/', views.debug_endpoints, name='debug_endpoints'),
]