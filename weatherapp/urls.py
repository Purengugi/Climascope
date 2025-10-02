from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.landing_page, name='landing'),
    path('home/', views.home, name='home'),
    
    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Email verification
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # User profile and account management
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('delete-avatar/', views.delete_avatar, name='delete_avatar'),
    path('settings/', views.settings_view, name='settings'),
    
    # Account management
    path('deactivate-account/', views.deactivate_account, name='deactivate_account'),
    path('delete-account/', views.delete_account, name='delete_account'),
    
    # Weather functionality
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('update-alert-settings/', views.update_alert_settings, name='update_alert_settings'),
    
    # Location weather
    path('location-weather/', views.get_location_weather, name='location_weather'),

    # Testing
    path('test-notifications/', views.test_notifications, name='test_notifications'),
    
    # Legal pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('contact-us/', views.contact_us, name='contact_us'),
]