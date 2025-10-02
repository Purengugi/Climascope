from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from smtplib import SMTPAuthenticationError, SMTPException
import requests
import logging
from .models import WeatherAlert, EmailNotification, UserProfile, FavoriteCity

logger = logging.getLogger(__name__)

class WeatherNotificationService:
    """Service for handling weather-related notifications and alerts"""
    
    def __init__(self):
        self.weather_api_key = settings.WEATHER_API_KEY
        
    def can_send_notification(self, user):
        """Check if user can receive notifications"""
        try:
            profile = UserProfile.objects.get(user=user)
            return (profile.email_notifications and 
                   not profile.is_deactivated and 
                   profile.is_email_verified)
        except UserProfile.DoesNotExist:
            return False
    
    def send_email_verification(self, user, request=None):
        """Send email verification to new user"""
        try:
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            if profile.is_email_verified:
                print(f"✓ Email already verified for {user.email}")
                return True
                
            token = profile.generate_verification_token()
            profile.save()
            
            print(f"Generated verification token for {user.email}: {token}")
            
            if request:
                verification_url = request.build_absolute_uri(
                    reverse('verify_email', kwargs={'token': str(token)})
                )
            else:
                verification_url = f"{settings.SITE_URL}/verify-email/{token}/"
            
            subject = "Verify Your Email - Climascope"
            
            html_content = render_to_string('weatherapp/emails/email_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'token': token
            })
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            EmailNotification.objects.create(
                user=user,
                subject=subject,
                message=text_content,
                email_type='email_verification',
                is_sent=True,
                sent_at=timezone.now()
            )
            
            print(f"✓ Verification email sent successfully to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending verification email to {user.email}: {e}")
            print(f"Verification email error: {e}")
            return False
    
    def send_welcome_email(self, user):
        """Send welcome email to verified users"""
        try:
            if not self.can_send_notification(user):
                return False
                
            subject = "Welcome to Climascope!"
            
            html_content = render_to_string('weatherapp/emails/welcome_email.html', {
                'user': user,
            })
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            EmailNotification.objects.create(
                user=user,
                subject=subject,
                message=text_content,
                email_type='welcome',
                is_sent=True,
                sent_at=timezone.now()
            )
            
            logger.info(f"Welcome email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {e}")
            print(f"Welcome email error: {e}")
            return False
    
    def get_weather_data(self, city):
        """Fetch current weather data for a city using OpenWeatherMap API"""
        try:
            url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data for {city}: {e}")
            return None

    def send_daily_weather_summary(self, user):
        """Send daily weather summary for user's favorite cities"""
        try:
            profile = UserProfile.objects.get(user=user)
            if not profile.daily_summary or not self.can_send_notification(user):
                logger.info(f"Daily summary disabled for user {user.username}")
                return False
                
            favorite_cities = FavoriteCity.objects.filter(user=user)[:5]
            
            if not favorite_cities:
                logger.info(f"No favorite cities for user {user.username}")
                return False
            
            weather_data = []
            for city in favorite_cities:
                weather = self.get_weather_data(city.city_name)
                if weather and 'main' in weather:
                    weather_data.append({
                        'city': city.city_name,
                        'country': city.country,
                        'temperature': round(weather['main']['temp']),
                        'description': weather['weather'][0]['description'],
                        'icon': weather['weather'][0]['icon'],
                        'humidity': weather['main']['humidity'],
                        'feels_like': round(weather['main']['feels_like'])
                    })
            
            if weather_data:
                subject = f"🌤️ Daily Weather Summary - {timezone.now().strftime('%B %d, %Y')}"
                
                html_content = render_to_string('weatherapp/emails/daily_summary.html', {
                    'user': user,
                    'weather_data': weather_data,
                    'date': timezone.now()
                })
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
                
                EmailNotification.objects.create(
                    user=user,
                    subject=subject,
                    message=text_content,
                    email_type='daily_summary',
                    is_sent=True,
                    sent_at=timezone.now()
                )
                
                logger.info(f"Daily weather summary sent to {user.email}")
                return True
            else:
                logger.warning(f"No weather data available for user {user.username}'s favorite cities")
                return False
                
        except Exception as e:
            logger.error(f"Error sending daily weather summary to {user.email}: {e}")
            print(f"Daily summary error: {e}")
            return False
    
    def send_weather_alert_email(self, alert):
        """Send weather alert email"""
        try:
            user = alert.user
            
            if not self.can_send_notification(user):
                logger.info(f"Notifications disabled for user {user.username}")
                return False
                
            subject = f"🌤️ Weather Alert for {alert.city_name}"
            
            if alert.alert_type == 'severe':
                subject = f"🚨 URGENT: {subject}"
            
            html_content = render_to_string('weatherapp/emails/weather_alert.html', {
                'user': user,
                'alert': alert,
                'city_name': alert.city_name,
                'is_urgent': alert.alert_type == 'severe'
            })
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            alert.is_sent = True
            alert.sent_at = timezone.now()
            alert.save()
            
            EmailNotification.objects.create(
                user=user,
                subject=subject,
                message=text_content,
                email_type='weather_alert',
                is_sent=True,
                sent_at=timezone.now()
            )
            
            logger.info(f"Weather alert email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending weather alert email to {alert.user.email}: {e}")
            print(f"Weather alert error: {e}")
            return False

    def create_temperature_alert(self, user, city_name, temperature, alert_type):
        """Create and send temperature alert"""
        if not self.can_send_notification(user):
            return
            
        temp_type = "high" if alert_type == "high" else "low"
        threshold = "above" if alert_type == "high" else "below"
        
        message = f"Temperature alert for {city_name}: {temperature}°C - {threshold} your threshold"
        
        alert = WeatherAlert.objects.create(
            user=user,
            city_name=city_name,
            alert_type=f'temperature_{temp_type}',
            message=message,
            temperature=temperature
        )
        
        self.send_weather_alert_email(alert)
    
    def create_rain_alert(self, user, city_name, description):
        """Create and send rain alert"""
        if not self.can_send_notification(user):
            return
            
        message = f"Rain alert for {city_name}: {description.title()}"
        
        alert = WeatherAlert.objects.create(
            user=user,
            city_name=city_name,
            alert_type='rain',
            message=message,
            weather_condition=description
        )
        
        self.send_weather_alert_email(alert)
    
    def create_severe_weather_alert(self, user, city_name, description):
        """Create and send severe weather alert"""
        if not self.can_send_notification(user):
            return
            
        message = f"⚠️ SEVERE WEATHER ALERT for {city_name}: {description.title()}"
        
        alert = WeatherAlert.objects.create(
            user=user,
            city_name=city_name,
            alert_type='severe',
            message=message,
            weather_condition=description
        )
        
        self.send_weather_alert_email(alert)
    
    def check_weather_alerts_for_user(self, user):
        """Check weather conditions for all user's favorite cities"""
        if not self.can_send_notification(user):
            return
        
        favorite_cities = FavoriteCity.objects.filter(user=user)
        
        for city in favorite_cities:
            weather_data = self.get_weather_data(city.city_name)
            if weather_data and 'main' in weather_data:
                self.check_weather_conditions_for_alerts(user, city, weather_data)
    
    def check_weather_conditions_for_alerts(self, user, favorite_city, weather_data):
        """Check weather conditions and create alerts if thresholds are met"""
        try:
            temperature = weather_data['main']['temp']
            description = weather_data['weather'][0]['description'].lower()
            
            if (favorite_city.temperature_threshold_high and 
                temperature > favorite_city.temperature_threshold_high):
                self.create_temperature_alert(user, favorite_city.city_name, temperature, 'high')
            
            if (favorite_city.temperature_threshold_low and 
                temperature < favorite_city.temperature_threshold_low):
                self.create_temperature_alert(user, favorite_city.city_name, temperature, 'low')
            
            if favorite_city.notify_rain and 'rain' in description:
                self.create_rain_alert(user, favorite_city.city_name, description)
            
            if (favorite_city.notify_extreme_weather and 
                any(condition in description for condition in ['storm', 'thunder', 'severe', 'tornado', 'hurricane'])):
                self.create_severe_weather_alert(user, favorite_city.city_name, description)
                
        except Exception as e:
            logger.error(f"Error checking weather conditions for alerts: {e}")
    
    def send_account_notification(self, user, notification_type, extra_context=None):
        """Send account-related notifications"""
        try:
            subject_map = {
                'account_deactivated': 'Account Deactivated - Climascope',
                'account_reactivated': 'Welcome Back - Climascope',
                'account_deleted': 'Account Deleted - Climascope',
                'profile_updated': 'Profile Updated - Climascope',
                'password_changed': 'Password Changed - Climascope'
            }
            
            context = {
                'user': user,
                'notification_type': notification_type,
                'date': timezone.now()
            }
            
            if extra_context:
                context.update(extra_context)
            
            subject = subject_map.get(notification_type, 'Notification from Climascope')
            
            if notification_type in ['account_deactivated', 'account_deleted']:
                template_name = f'weatherapp/emails/{notification_type}.html'
            else:
                template_name = 'weatherapp/emails/account_notification.html'
            
            try:
                html_content = render_to_string(template_name, context)
            except:
                html_content = render_to_string('weatherapp/emails/account_notification.html', context)
            
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            EmailNotification.objects.create(
                user=user,
                subject=subject,
                message=text_content,
                email_type=notification_type,
                is_sent=True,
                sent_at=timezone.now()
            )
            
            logger.info(f"Account notification ({notification_type}) sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Error sending account notification: {e}")
            print(f"Account notification error: {e}")