from django.contrib import admin
from django.urls import path

from . import views  # Import views from the current directory
urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path('tos/', views.tos, name='tos'),  # Terms of Service page
]
