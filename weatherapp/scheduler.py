# scheduler.py - Enhanced task scheduler for weather notifications
import schedule
import time
import logging
import os
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weatherproject.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from weatherapp.email_service import WeatherNotificationService
from weatherapp.models import UserProfile, FavoriteCity

logger = logging.getLogger(__name__)

class WeatherTaskScheduler:
    """Enhanced scheduler for weather-related tasks with better monitoring"""
    
    def __init__(self):
        self.notification_service = WeatherNotificationService()
        self.last_health_check = None
        logger.info("Weather Task Scheduler initialized")
    
    def run_weather_alerts_check(self):
        """Run weather alerts check for all users"""
        try:
            start_time = datetime.now()
            logger.info("Starting scheduled weather alerts check")
            
            # Use the management command for better logging
            call_command('send_weather_alerts')
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Weather alerts check completed in {duration:.2f} seconds")
            
            print(f"✅ Weather alerts check completed at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error running weather alerts check: {e}")
            print(f"❌ Weather alerts check failed: {e}")
    
    def run_daily_summaries(self):
        """Run daily weather summaries for users who enabled them"""
        try:
            start_time = datetime.now()
            logger.info("Starting scheduled daily summaries")
            
            # Use the management command
            call_command('send_daily_summaries')
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Daily summaries completed in {duration:.2f} seconds")
            
            print(f"✅ Daily summaries completed at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error running daily summaries: {e}")
            print(f"❌ Daily summaries failed: {e}")
    
    def cleanup_old_data(self):
        """Clean up old weather history and alerts"""
        try:
            start_time = datetime.now()
            logger.info("Starting scheduled data cleanup")
            
            # Use the management command
            call_command('cleanup_old_data')
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Data cleanup completed in {duration:.2f} seconds")
            
            print(f"✅ Data cleanup completed at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
            print(f"❌ Data cleanup failed: {e}")
    
    def health_check(self):
        """Perform system health check"""
        try:
            logger.info("Running health check")
            
            # Check API connectivity
            call_command('check_weather_health')
            
            self.last_health_check = datetime.now()
            print(f"✅ Health check completed at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            print(f"❌ Health check failed: {e}")
    
    def send_test_notifications(self):
        """Send test notifications (for debugging)"""
        try:
            # Get a test user
            test_users = User.objects.filter(
                userprofile__is_email_verified=True,
                userprofile__email_notifications=True,
                is_superuser=True
            )[:1]
            
            if test_users.exists():
                user = test_users.first()
                success = self.notification_service.send_daily_weather_summary(user)
                if success:
                    print(f"✅ Test notification sent to {user.email}")
                else:
                    print(f"❌ Test notification failed for {user.email}")
            else:
                print("⚠️  No eligible test users found")
                
        except Exception as e:
            logger.error(f"Test notification failed: {e}")
            print(f"❌ Test notification failed: {e}")
    
    def get_system_stats(self):
        """Print current system statistics"""
        try:
            total_users = User.objects.count()
            verified_users = User.objects.filter(userprofile__is_email_verified=True).count()
            active_users = User.objects.filter(
                userprofile__is_deactivated=False,
                userprofile__email_notifications=True
            ).count()
            total_favorites = FavoriteCity.objects.count()
            
            print(f"\n📊 System Statistics:")
            print(f"   Total Users: {total_users}")
            print(f"   Verified Users: {verified_users}")
            print(f"   Active Users: {active_users}")
            print(f"   Total Favorite Cities: {total_favorites}")
            print(f"   Last Health Check: {self.last_health_check or 'Never'}")
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            print(f"❌ Error getting stats: {e}")
    
    def setup_schedule(self):
        """Setup the scheduled tasks with better timing"""
        # Weather alerts every 2 hours during active times
        schedule.every().hour.at(":00").do(self.run_weather_alerts_check).tag('alerts')
        
        # Daily summaries at 7 AM local time
        schedule.every().day.at("07:00").do(self.run_daily_summaries).tag('summaries')
        
        # Cleanup at 2 AM daily
        schedule.every().day.at("02:00").do(self.cleanup_old_data).tag('cleanup')
        
        # Health check every 6 hours
        schedule.every(6).hours.do(self.health_check).tag('health')
        
        # System stats every 30 minutes during development
        if os.getenv('DJANGO_ENV') == 'development':
            schedule.every(30).minutes.do(self.get_system_stats).tag('stats')
        
        logger.info("Scheduled tasks configured:")
        logger.info("- Weather alerts: Every hour")
        logger.info("- Daily summaries: Daily at 7:00 AM")
        logger.info("- Data cleanup: Daily at 2:00 AM")
        logger.info("- Health check: Every 6 hours")
        
        print("\n" + "="*60)
        print("🌤️  CLIMASCOPE WEATHER TASK SCHEDULER")
        print("="*60)
        print("Scheduled Tasks:")
        print("  ⏰ Weather Alerts: Every hour")
        print("  📧 Daily Summaries: Daily at 7:00 AM")
        print("  🗑️  Data Cleanup: Daily at 2:00 AM")
        print("  ❤️  Health Check: Every 6 hours")
        print("="*60)
    
    def run_scheduler(self):
        """Run the scheduler continuously with monitoring"""
        self.setup_schedule()
        
        print(f"Scheduler started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Press Ctrl+C to stop\n")
        
        # Run initial health check
        self.health_check()
        
        # Show initial stats
        self.get_system_stats()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🛑 Scheduler stopped by user")
            logger.info("Scheduler stopped by user")
            
            # Print final stats
            print("\n📊 Final Statistics:")
            self.get_system_stats()

def main():
    """Main function to start the scheduler"""
    scheduler = WeatherTaskScheduler()
    scheduler.run_scheduler()

if __name__ == "__main__":
    main()