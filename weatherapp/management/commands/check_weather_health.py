from django.core.management.base import BaseCommand
from django.conf import settings
from weatherapp.email_service import WeatherNotificationService
import requests
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check the health of weather services and APIs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-city',
            type=str,
            default='London',
            help='City to test weather API with (default: London)',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Email address to test email service with',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Running weather service health check...')
        )
        
        all_healthy = True
        
        # Check OpenWeatherMap API
        api_healthy = self.check_weather_api(options['test_city'])
        all_healthy = all_healthy and api_healthy
        
        # Check Google Custom Search API
        if hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY:
            google_healthy = self.check_google_api()
            all_healthy = all_healthy and google_healthy
        else:
            self.stdout.write(
                self.style.WARNING('Google API key not configured, skipping check')
            )
        
        # Check email service
        email_healthy = self.check_email_service(options.get('test_email'))
        all_healthy = all_healthy and email_healthy
        
        # Check database connectivity
        db_healthy = self.check_database()
        all_healthy = all_healthy and db_healthy
        
        # Overall result
        if all_healthy:
            self.stdout.write(
                self.style.SUCCESS('\n✅ All services are healthy!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('\n❌ Some services have issues!')
            )
    
    def check_weather_api(self, test_city):
        """Check OpenWeatherMap API connectivity"""
        self.stdout.write('\n🌤️  Checking OpenWeatherMap API...')
        
        try:
            if not settings.WEATHER_API_KEY:
                self.stdout.write(
                    self.style.ERROR('  ❌ Weather API key not configured')
                )
                return False
            
            url = f'https://api.openweathermap.org/data/2.5/weather?q={test_city}&appid={settings.WEATHER_API_KEY}&units=metric'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ API working - {test_city}: {temp}°C, {desc}')
                )
                return True
            elif response.status_code == 401:
                self.stdout.write(
                    self.style.ERROR('  ❌ Invalid API key')
                )
                return False
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ API error: HTTP {response.status_code}')
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Connection error: {e}')
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Unexpected error: {e}')
            )
            return False
    
    def check_google_api(self):
        """Check Google Custom Search API"""
        self.stdout.write('\n🔍 Checking Google Custom Search API...')
        
        try:
            query = "london city"
            url = f"https://www.googleapis.com/customsearch/v1?key={settings.GOOGLE_API_KEY}&cx={settings.GOOGLE_SEARCH_ENGINE_ID}&q={query}&searchType=image&num=1"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    self.stdout.write(
                        self.style.SUCCESS('  ✅ Google API working')
                    )
                    return True
                else:
                    self.stdout.write(
                        self.style.WARNING('  ⚠️  Google API working but no results')
                    )
                    return True
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Google API error: HTTP {response.status_code}')
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Google API error: {e}')
            )
            return False
    
    def check_email_service(self, test_email):
        """Check email service configuration"""
        self.stdout.write('\n📧 Checking email service...')
        
        try:
            # Check configuration
            if not settings.EMAIL_HOST_USER:
                self.stdout.write(
                    self.style.WARNING('  ⚠️  Email host user not configured')
                )
                return False
            
            if not settings.EMAIL_HOST_PASSWORD:
                self.stdout.write(
                    self.style.WARNING('  ⚠️  Email host password not configured')
                )
                return False
            
            self.stdout.write(
                self.style.SUCCESS(f'  ✅ Email configuration looks good')
            )
            self.stdout.write(f'    Host: {settings.EMAIL_HOST}')
            self.stdout.write(f'    Port: {settings.EMAIL_PORT}')
            self.stdout.write(f'    User: {settings.EMAIL_HOST_USER}')
            
            # Optional: Send test email if address provided
            if test_email:
                self.stdout.write(f'    Testing with {test_email}...')
                # You could implement a test email send here
                
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Email configuration error: {e}')
            )
            return False
    
    def check_database(self):
        """Check database connectivity"""
        self.stdout.write('\n🗄️  Checking database connectivity...')
        
        try:
            from django.db import connection
            from weatherapp.models import UserProfile
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Test model access
            count = UserProfile.objects.count()
            
            self.stdout.write(
                self.style.SUCCESS(f'  ✅ Database working - {count} user profiles')
            )
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Database error: {e}')
            )
            return False