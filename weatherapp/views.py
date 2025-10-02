from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count
from django.conf import settings
from django.urls import reverse
from django.core.paginator import Paginator
import requests
import datetime
import json
import uuid
from .models import UserProfile, FavoriteCity, WeatherHistory, WeatherForecast, WeatherAlert, EmailNotification
from .forms import SignUpForm, UserProfileForm, PasswordChangeForm
from .email_service import WeatherNotificationService
import os

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'weatherapp/landing.html')

def get_weather_data(city):
    """Fetch current weather data for a city using OpenWeatherMap API"""
    try:
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={settings.WEATHER_API_KEY}&units=metric'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_weather_by_coords(lat, lon):
    """Fetch current weather data by coordinates using OpenWeatherMap API"""
    try:
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={settings.WEATHER_API_KEY}&units=metric'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data by coords: {e}")
        return None

def get_forecast_data(city):
    """Get 5-day weather forecast"""
    try:
        url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={settings.WEATHER_API_KEY}&units=metric'
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

def get_city_image(city):
    """Get city background image from Google Custom Search"""
    try:
        query = f"{city} city skyline aerial view"
        url = f"https://www.googleapis.com/customsearch/v1?key={settings.GOOGLE_API_KEY}&cx={settings.GOOGLE_SEARCH_ENGINE_ID}&q={query}&searchType=image&imgSize=xlarge&imgType=photo&fileType=jpg"
        
        response = requests.get(url, timeout=5)
        data = response.json()
        search_items = data.get("items", [])
        
        if search_items:
            for i in [1, 2, 0, 3, 4]:
                if i < len(search_items):
                    image_url = search_items[i]['link']
                    if verify_image_url(image_url):
                        return image_url
        
        query = f"{city} cityscape panorama"
        url = f"https://www.googleapis.com/customsearch/v1?key={settings.GOOGLE_API_KEY}&cx={settings.GOOGLE_SEARCH_ENGINE_ID}&q={query}&searchType=image&imgSize=xlarge"
        response = requests.get(url, timeout=5)
        data = response.json()
        search_items = data.get("items", [])
        
        if search_items:
            image_url = search_items[0]['link']
            if verify_image_url(image_url):
                return image_url
                
    except Exception as e:
        print(f"Error getting city image: {e}")
    
    fallback_images = [
        'https://images.pexels.com/photos/3008509/pexels-photo-3008509.jpeg?auto=compress&cs=tinysrgb&w=1600',
        'https://images.pexels.com/photos/281260/pexels-photo-281260.jpeg?auto=compress&cs=tinysrgb&w=1600',
        'https://images.pexels.com/photos/158163/clouds-cloudscape-daylight-blue-sky-158163.jpeg?auto=compress&cs=tinysrgb&w=1600'
    ]
    return fallback_images[hash(city) % len(fallback_images)]

def verify_image_url(url):
    """Verify if image URL is accessible"""
    try:
        response = requests.head(url, timeout=3)
        return response.status_code == 200 and 'image' in response.headers.get('content-type', '')
    except:
        return False

def get_user_default_location(user):
    """Get user's preferred default location"""
    if user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.is_deactivated:
                return None
        except UserProfile.DoesNotExist:
            pass
        
        favorite_city = FavoriteCity.objects.filter(user=user).order_by('-added_at').first()
        if favorite_city:
            return favorite_city.city_name
        
        recent_search = WeatherHistory.objects.filter(user=user).order_by('-searched_at').first()
        if recent_search:
            return recent_search.city_name
    
    return None

@login_required
def home(request):
    """Enhanced home view with smart default location and notifications"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.is_deactivated:
            messages.error(request, 'Your account is deactivated. Please reactivate to continue.')
            logout(request)
            return redirect('login')
        if not profile.is_email_verified:
            messages.warning(request, 'Please verify your email to receive weather alerts and access all features.')
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=request.user)
    
    exception_occurred = False
    show_location_prompt = False
    city = None
    
    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        
        if lat and lon:
            weather_data = get_weather_by_coords(lat, lon)
            if weather_data and 'main' in weather_data:
                city = weather_data['name']
        elif not city:
            messages.error(request, 'Please enter a city name.')
            city = get_user_default_location(request.user)
    else:
        city = get_user_default_location(request.user)
    
    if not city:
        show_location_prompt = True
        context = {
            'city': 'Welcome to Climascope',
            'temp': '--',
            'description': 'Choose a city or allow location access',
            'icon': '01d',
            'day': datetime.date.today(),
            'feels_like': '--',
            'humidity': '--',
            'pressure': '--',
            'wind_speed': '--',
            'country': '',
            'image_url': 'https://images.pexels.com/photos/281260/pexels-photo-281260.jpeg?auto=compress&cs=tinysrgb&w=1600',
            'daily_forecast': [],
            'exception_occurred': False,
            'show_location_prompt': True,
            'favorite_cities': FavoriteCity.objects.filter(user=request.user)[:6],
            'recent_searches': WeatherHistory.objects.filter(user=request.user)[:5],
            'is_favorite': False
        }
        return render(request, 'weatherapp/index.html', context)
    
    weather_data = get_weather_data(city)
    forecast_data = get_forecast_data(city) if city else None
    
    context = {
        'city': city,
        'temp': 0,
        'description': 'Weather data not available',
        'icon': '01d',
        'day': datetime.date.today(),
        'feels_like': 0,
        'humidity': 0,
        'pressure': 0,
        'wind_speed': 0,
        'country': '',
        'image_url': get_city_image(city),
        'daily_forecast': [],
        'exception_occurred': True,
        'show_location_prompt': False,
        'favorite_cities': FavoriteCity.objects.filter(user=request.user)[:6],
        'recent_searches': WeatherHistory.objects.filter(user=request.user)[:5],
        'is_favorite': False
    }
    
    if weather_data and 'main' in weather_data:
        WeatherHistory.objects.create(
            user=request.user,
            city_name=weather_data['name'],
            country=weather_data['sys'].get('country', ''),
            temperature=weather_data['main']['temp'],
            description=weather_data['weather'][0]['description'],
            icon=weather_data['weather'][0]['icon'],
            humidity=weather_data['main'].get('humidity'),
            pressure=weather_data['main'].get('pressure'),
            wind_speed=weather_data.get('wind', {}).get('speed'),
            feels_like=weather_data['main'].get('feels_like')
        )
        
        city_name = weather_data['name']
        country = weather_data['sys'].get('country', '')
        image_url = get_city_image(f"{city_name} {country}")
        
        daily_forecast = []
        if forecast_data and 'list' in forecast_data:
            for i in range(0, min(40, len(forecast_data['list'])), 8):
                item = forecast_data['list'][i]
                daily_forecast.append({
                    'date': datetime.datetime.fromtimestamp(item['dt']).strftime('%a, %b %d'),
                    'temp_max': round(item['main']['temp_max']),
                    'temp_min': round(item['main']['temp_min']),
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon']
                })
        
        context = {
            'weather_data': weather_data,
            'description': weather_data['weather'][0]['description'],
            'icon': weather_data['weather'][0]['icon'],
            'temp': round(weather_data['main']['temp']),
            'feels_like': round(weather_data['main']['feels_like']),
            'humidity': weather_data['main']['humidity'],
            'pressure': weather_data['main']['pressure'],
            'wind_speed': weather_data.get('wind', {}).get('speed', 0),
            'city': weather_data['name'],
            'country': weather_data['sys'].get('country', ''),
            'day': datetime.date.today(),
            'image_url': image_url,
            'daily_forecast': daily_forecast,
            'exception_occurred': False,
            'show_location_prompt': False,
            'favorite_cities': FavoriteCity.objects.filter(user=request.user)[:6],
            'recent_searches': WeatherHistory.objects.filter(user=request.user)[:5],
            'is_favorite': FavoriteCity.objects.filter(
                user=request.user, city_name=weather_data['name']
            ).exists()
        }
    else:
        context['exception_occurred'] = True
        messages.error(request, f'Weather data for "{city}" not found. Please try again.')
    
    return render(request, 'weatherapp/index.html', context)

def signup_view(request):
    """User registration with email verification - FIXED VERSION"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            
            # Create user profile with email verification
            profile, created = UserProfile.objects.get_or_create(
                user=user, 
                defaults={'is_email_verified': False}
            )
            
            if not created:
                # Profile already exists, ensure it's not verified
                profile.is_email_verified = False
                profile.save()
            
            # Send verification email
            email_service = WeatherNotificationService()
            email_sent = email_service.send_email_verification(user, request)
            
            if email_sent:
                messages.success(request, 'Account created! Please check your email to verify your account.')
                # Log the user in
                user = authenticate(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1']
                )
                if user:
                    login(request, user)
                return redirect('home')
            else:
                messages.warning(request, 'Account created but verification email failed to send. You can resend it from your profile.')
                # Still log the user in
                user = authenticate(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1']
                )
                if user:
                    login(request, user)
                return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    
    return render(request, 'weatherapp/auth/signup.html', {'form': form})

def verify_email(request, token):
    """Email verification view"""
    try:
        profile = UserProfile.objects.get(email_verification_token=token)
        
        if profile.is_verification_token_valid():
            profile.is_email_verified = True
            profile.email_verification_token = None  # Clear the token after use
            profile.save()
            
            # Send welcome email
            email_service = WeatherNotificationService()
            email_service.send_welcome_email(profile.user)
            
            messages.success(request, 'Email verified successfully! Welcome to Climascope!')
        else:
            messages.error(request, 'Verification link has expired. Please request a new one.')
            
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
    
    return redirect('home' if request.user.is_authenticated else 'login')

@login_required
def resend_verification(request):
    """Resend email verification - FIXED VERSION"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.is_email_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('profile')
        
        # Generate new token
        token = profile.generate_verification_token()
        profile.save()
        
        email_service = WeatherNotificationService()
        if email_service.send_email_verification(request.user, request):
            messages.success(request, 'Verification email sent! Please check your inbox and spam folder.')
        else:
            messages.error(request, 'Failed to send verification email. Please try again later.')
            
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user, is_email_verified=False)
        messages.info(request, 'Profile created. Please try resending verification.')
    
    return redirect('profile')

def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.is_deactivated:
                    # Reactivate account
                    profile.is_deactivated = False
                    profile.deactivated_at = None
                    profile.save()
                    messages.success(request, 'Welcome back! Your account has been reactivated.')
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user)
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials.')
    
    return render(request, 'weatherapp/auth/login.html')

@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')

@login_required
def profile_view(request):
    """Enhanced user profile page with avatar management"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.is_deactivated:
        messages.error(request, 'Your account is deactivated.')
        return redirect('login')
    
    if request.method == 'POST':
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
            profile.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('profile')
        
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    total_searches = WeatherHistory.objects.filter(user=request.user).count()
    favorite_count = FavoriteCity.objects.filter(user=request.user).count()
    recent_searches = WeatherHistory.objects.filter(user=request.user)[:10]
    recent_alerts = WeatherAlert.objects.filter(user=request.user)[:5]
    
    context = {
        'form': form,
        'profile': profile,
        'total_searches': total_searches,
        'favorite_count': favorite_count,
        'recent_searches': recent_searches,
        'recent_alerts': recent_alerts
    }
    
    return render(request, 'weatherapp/profile.html', context)

@login_required
@require_http_methods(["POST"])
def upload_avatar(request):
    """Handle avatar upload separately"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
            profile.save()
            messages.success(request, 'Profile picture updated successfully!')
        else:
            messages.error(request, 'No image file selected.')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
    except Exception as e:
        messages.error(request, f'Error uploading profile picture: {str(e)}')
    
    return redirect('profile')

@login_required
def deactivate_account(request):
    """Deactivate user account"""
    if request.method == 'POST':
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.is_deactivated = True
        profile.deactivated_at = timezone.now()
        profile.save()
        
        # Send deactivation email
        email_service = WeatherNotificationService()
        email_service.send_account_notification(request.user, 'account_deactivated')
        
        logout(request)
        messages.success(request, 'Your account has been deactivated. You can reactivate it by logging in again.')
        return redirect('landing')
    
    return render(request, 'weatherapp/auth/deactivate_account.html')

@login_required
def delete_account(request):
    """Permanently delete user account"""
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation', '').strip()
        confirm_deletion = request.POST.get('confirm_deletion')
        confirm_data_loss = request.POST.get('confirm_data_loss')
        
        if (confirmation == 'DELETE' and confirm_deletion and confirm_data_loss):
            user = request.user
            
            # Send deletion email before deleting
            email_service = WeatherNotificationService()
            email_service.send_account_notification(user, 'account_deleted')
            
            logout(request)
            user.delete()
            
            messages.success(request, 'Your account has been permanently deleted. Thank you for using Climascope!')
            return redirect('landing')
        else:
            messages.error(request, 'Please confirm all requirements to delete your account.')
    
    # Get user statistics for the deletion page
    total_searches = WeatherHistory.objects.filter(user=request.user).count()
    favorite_count = FavoriteCity.objects.filter(user=request.user).count()
    total_alerts = WeatherAlert.objects.filter(user=request.user).count()
    
    context = {
        'total_searches': total_searches,
        'favorite_count': favorite_count,
        'total_alerts': total_alerts,
    }
    
    return render(request, 'weatherapp/auth/delete_account.html', context)

@login_required
def settings_view(request):
    """Enhanced settings view with integrated password change"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if profile.is_deactivated:
            messages.error(request, 'Your account is deactivated.')
            return redirect('login')
        
        password_form = PasswordChangeForm(request.user)
        
        if request.method == 'POST':
            if 'profile-form' in request.POST:
                user = request.user
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.username = request.POST.get('username', '')
                user.email = request.POST.get('email', '')
                user.save()
                
                profile.location = request.POST.get('location', '')
                profile.save()
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('settings')
            
            elif 'alert-settings' in request.POST:
                profile.email_notifications = request.POST.get('email_notifications') == 'on'
                profile.weather_alerts = request.POST.get('weather_alerts') == 'on'
                profile.daily_summary = request.POST.get('daily_summary') == 'on'
                profile.severe_weather_alerts = request.POST.get('severe_weather_alerts') == 'on'
                profile.save()
                messages.success(request, "Notification settings updated successfully.")
                return redirect('settings')
                
            elif 'password-form' in request.POST:
                # FIXED PASSWORD CHANGE LOGIC
                password_form = PasswordChangeForm(request.user, request.POST)
                
                if password_form.is_valid():
                    # Save the new password
                    user = password_form.save()
                    
                    # Keep user logged in after password change
                    update_session_auth_hash(request, user)
                    
                    # Send notification email
                    email_service = WeatherNotificationService()
                    email_service.send_account_notification(user, 'password_changed')
                    
                    messages.success(request, 'Your password has been successfully changed!')
                    return redirect('settings')
                else:
                    # Show specific errors
                    for field, errors in password_form.errors.items():
                        for error in errors:
                            messages.error(request, f'{field}: {error}')
        
        context = {
            'profile': profile,
            'password_form': password_form,
        }
        
        return render(request, 'weatherapp/settings.html', context)
        
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('home')

@require_http_methods(['GET'])
def get_location_weather(request):
    """Handle location-based weather requests"""
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    
    if not lat or not lon:
        return JsonResponse({'success': False, 'error': 'Coordinates required'})
    
    weather_data = get_weather_by_coords(lat, lon)
    
    if weather_data and 'main' in weather_data:
        return JsonResponse({
            'success': True,
            'city': weather_data['name']
        })
    else:
        return JsonResponse({'success': False, 'error': 'Unable to get weather for location'})

@login_required
def test_notifications(request):
    """Test notification functionality"""
    if request.method == 'POST':
        notification_type = request.POST.get('notification_type')
        email_service = WeatherNotificationService()
        
        try:
            if notification_type == 'daily_summary':
                success = email_service.send_daily_weather_summary(request.user)
                if success:
                    messages.success(request, 'Daily summary test sent! Check your email.')
                else:
                    messages.warning(request, 'Daily summary not sent. Check if you have favorite cities and email settings.')
                    
            elif notification_type == 'weather_alert':
                alert = WeatherAlert.objects.create(
                    user=request.user,
                    city_name="Test City",
                    alert_type='test',
                    message='This is a test weather alert to verify your notification settings are working correctly.',
                    temperature=25.0,
                    weather_condition='clear sky'
                )
                success = email_service.send_weather_alert_email(alert)
                if success:
                    messages.success(request, 'Weather alert test sent! Check your email.')
                else:
                    messages.error(request, 'Failed to send weather alert. Check email configuration.')
                    
            elif notification_type == 'welcome':
                email_service.send_welcome_email(request.user)
                messages.success(request, 'Welcome email test sent! Check your email.')
            
        except Exception as e:
            messages.error(request, f'Error sending test notification: {str(e)}')
        
        return redirect('settings')
    
    return redirect('settings')
    
@login_required
@require_http_methods(["POST"])
def delete_avatar(request):
    """Delete user's profile picture"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.avatar:
            profile.avatar.delete(save=False)
            profile.avatar = None
            profile.save()
            messages.success(request, 'Profile picture removed successfully!')
        else:
            messages.info(request, 'No profile picture to remove.')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
    except Exception as e:
        messages.error(request, f'Error removing profile picture: {str(e)}')
    
    return redirect('profile')

# Legal pages
def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'weatherapp/legal/privacy_policy.html')

def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'weatherapp/legal/terms_of_service.html')

def contact_us(request):
    """Contact Us page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send the contact form via email
        # For now, we'll just show a success message
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        return redirect('contact_us')
    
    return render(request, 'weatherapp/legal/contact_us.html')

@login_required
def dashboard_view(request):
    """Enhanced user dashboard with analytics and alerts"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.is_deactivated:
        messages.error(request, 'Your account is deactivated.')
        return redirect('login')
    
    favorite_cities = FavoriteCity.objects.filter(user=request.user)
    recent_searches = WeatherHistory.objects.filter(user=request.user)[:10]
    recent_alerts = WeatherAlert.objects.filter(user=request.user).order_by('-created_at')[:5]
    recent_notifications = EmailNotification.objects.filter(user=request.user).order_by('-sent_at')[:5]
    
    # Get weather data for favorite cities
    favorite_weather = []
    for fav in favorite_cities:
        weather = get_weather_data(fav.city_name)
        if weather and 'main' in weather:
            favorite_weather.append({
                'city': fav.city_name,
                'temp': round(weather['main']['temp']),
                'description': weather['weather'][0]['description'],
                'icon': weather['weather'][0]['icon']
            })
    
    # Prepare chart data
    chart_data = []
    for search in recent_searches[:7]:
        chart_data.append({
            'date': search.searched_at.strftime('%m/%d'),
            'time': search.searched_at.strftime('%H:%M'),
            'datetime': search.searched_at.strftime('%m/%d %H:%M'),
            'temperature': search.temperature,
            'city': search.city_name
        })
    
    # Calculate user statistics
    total_searches = WeatherHistory.objects.filter(user=request.user).count()
    total_alerts = WeatherAlert.objects.filter(user=request.user).count()
    total_favorites = favorite_cities.count()
    
    # Get most searched cities
    most_searched_cities = WeatherHistory.objects.filter(user=request.user).values('city_name').annotate(
        search_count=Count('city_name')
    ).order_by('-search_count')[:5]
    
    context = {
        'favorite_weather': favorite_weather,
        'recent_searches': recent_searches,
        'recent_alerts': recent_alerts,
        'recent_notifications': recent_notifications,
        'chart_data': json.dumps(chart_data),
        'total_searches': total_searches,
        'total_alerts': total_alerts,
        'total_favorites': total_favorites,
        'most_searched_cities': most_searched_cities,
        'profile': profile,
    }
    
    return render(request, 'weatherapp/dashboard.html', context)

@login_required
@require_http_methods(["POST"])
def toggle_favorite(request):
    """Add/remove city from favorites with validation"""
    from django.utils.html import escape
    
    # Get and sanitize input
    city_name = request.POST.get('city_name', '').strip()
    city_name = escape(city_name)
    
    # Validate input
    if not city_name or len(city_name) > 100:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid city name'
        })
    
    # Check if account is active
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if profile.is_deactivated:
        return JsonResponse({
            'success': False, 
            'message': 'Account deactivated'
        })
    
    try:
        favorite, created = FavoriteCity.objects.get_or_create(
            user=request.user,
            city_name=city_name,
            defaults={
                'country': escape(request.POST.get('country', '')),
                'temperature_threshold_high': 35.0,
                'temperature_threshold_low': 5.0,
                'notify_rain': True,
                'notify_extreme_weather': True
            }
        )
        
        if not created:
            favorite.delete()
            return JsonResponse({
                'success': True, 
                'action': 'removed', 
                'message': 'Removed from favorites'
            })
        else:
            return JsonResponse({
                'success': True, 
                'action': 'added', 
                'message': 'Added to favorites'
            })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error toggling favorite: {e}")
        return JsonResponse({
            'success': False, 
            'message': 'An error occurred'
        })

@login_required
@require_http_methods(['POST'])
def update_alert_settings(request):
    """Update user's notification preferences."""
    try:
        profile = request.user.userprofile
        profile.email_notifications = request.POST.get('email_notifications') == 'on'
        profile.weather_alerts = request.POST.get('weather_alerts') == 'on'
        profile.daily_summary = request.POST.get('daily_summary') == 'on'
        profile.severe_weather_alerts = request.POST.get('severe_weather_alerts') == 'on'
        profile.save()
        messages.success(request, "Notification settings updated successfully.")
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
    return redirect('settings')