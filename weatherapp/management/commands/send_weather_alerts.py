from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from weatherapp.models import UserProfile, FavoriteCity
from weatherapp.email_service import WeatherNotificationService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check weather conditions and send alerts to users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Check alerts for specific user (username)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without sending emails',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting weather alerts check...')
        )
        
        email_service = WeatherNotificationService()
        
        if options['user']:
            # Check specific user
            try:
                user = User.objects.get(username=options['user'])
                self.check_user_alerts(user, email_service, options['dry_run'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{options["user"]}" not found')
                )
                return
        else:
            # Check all users with verified emails and notifications enabled
            users = User.objects.filter(
                userprofile__is_email_verified=True,
                userprofile__email_notifications=True,
                userprofile__weather_alerts=True,
                userprofile__is_deactivated=False
            )
            
            alerts_sent = 0
            users_processed = 0
            
            for user in users:
                try:
                    result = self.check_user_alerts(user, email_service, options['dry_run'])
                    if result:
                        alerts_sent += result
                    users_processed += 1
                except Exception as e:
                    logger.error(f"Error processing alerts for {user.username}: {e}")
                    self.stdout.write(
                        self.style.WARNING(f'Error processing {user.username}: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Processed {users_processed} users, sent {alerts_sent} alerts'
                )
            )
    
    def check_user_alerts(self, user, email_service, dry_run=False):
        """Check alerts for a specific user"""
        alerts_sent = 0
        
        self.stdout.write(f'Checking alerts for {user.username}...')
        
        favorite_cities = FavoriteCity.objects.filter(user=user)
        if not favorite_cities.exists():
            self.stdout.write(f'  No favorite cities for {user.username}')
            return 0
        
        for city in favorite_cities:
            try:
                weather_data = email_service.get_weather_data(city.city_name)
                if weather_data and 'main' in weather_data:
                    alerts_needed = self.analyze_weather_conditions(
                        weather_data, city
                    )
                    
                    for alert_type, message in alerts_needed:
                        if dry_run:
                            self.stdout.write(
                                f'  Would send {alert_type} alert for {city.city_name}: {message}'
                            )
                        else:
                            # Create and send alert
                            if alert_type == 'temperature_high':
                                email_service.create_temperature_alert(
                                    user, city.city_name, weather_data['main']['temp'], 'high'
                                )
                            elif alert_type == 'temperature_low':
                                email_service.create_temperature_alert(
                                    user, city.city_name, weather_data['main']['temp'], 'low'
                                )
                            elif alert_type == 'rain':
                                email_service.create_rain_alert(
                                    user, city.city_name, weather_data['weather'][0]['description']
                                )
                            elif alert_type == 'severe':
                                email_service.create_severe_weather_alert(
                                    user, city.city_name, weather_data['weather'][0]['description']
                                )
                            
                            alerts_sent += 1
                            self.stdout.write(f'  Sent {alert_type} alert for {city.city_name}')
                else:
                    self.stdout.write(f'  No weather data for {city.city_name}')
                    
            except Exception as e:
                logger.error(f"Error checking {city.city_name} for {user.username}: {e}")
                self.stdout.write(
                    self.style.WARNING(f'  Error checking {city.city_name}: {e}')
                )
        
        return alerts_sent
    
    def analyze_weather_conditions(self, weather_data, city):
        """Analyze weather conditions and return needed alerts"""
        alerts_needed = []
        
        temperature = weather_data['main']['temp']
        description = weather_data['weather'][0]['description'].lower()
        
        # Temperature alerts
        if (city.temperature_threshold_high and 
            temperature > city.temperature_threshold_high):
            alerts_needed.append((
                'temperature_high',
                f'High temperature: {temperature}°C (threshold: {city.temperature_threshold_high}°C)'
            ))
        
        if (city.temperature_threshold_low and 
            temperature < city.temperature_threshold_low):
            alerts_needed.append((
                'temperature_low',
                f'Low temperature: {temperature}°C (threshold: {city.temperature_threshold_low}°C)'
            ))
        
        # Rain alerts
        if city.notify_rain and 'rain' in description:
            alerts_needed.append((
                'rain',
                f'Rain expected: {description}'
            ))
        
        # Severe weather alerts
        severe_conditions = ['storm', 'thunder', 'severe', 'tornado', 'hurricane', 'hail']
        if (city.notify_extreme_weather and 
            any(condition in description for condition in severe_conditions)):
            alerts_needed.append((
                'severe',
                f'Severe weather: {description}'
            ))
        
        return alerts_needed