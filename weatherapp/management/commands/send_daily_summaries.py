from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from weatherapp.models import UserProfile
from weatherapp.email_service import WeatherNotificationService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send daily weather summaries to users who have enabled them'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Send summary to specific user (username)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without sending emails',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting daily weather summaries...')
        )
        
        email_service = WeatherNotificationService()
        
        if options['user']:
            # Send to specific user
            try:
                user = User.objects.get(username=options['user'])
                self.send_user_summary(user, email_service, options['dry_run'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{options["user"]}" not found')
                )
                return
        else:
            # Send to all eligible users
            users = User.objects.filter(
                userprofile__is_email_verified=True,
                userprofile__email_notifications=True,
                userprofile__daily_summary=True,
                userprofile__is_deactivated=False
            )
            
            summaries_sent = 0
            users_processed = 0
            
            for user in users:
                try:
                    result = self.send_user_summary(user, email_service, options['dry_run'])
                    if result:
                        summaries_sent += 1
                    users_processed += 1
                except Exception as e:
                    logger.error(f"Error sending summary to {user.username}: {e}")
                    self.stdout.write(
                        self.style.WARNING(f'Error processing {user.username}: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Processed {users_processed} users, sent {summaries_sent} summaries'
                )
            )
    
    def send_user_summary(self, user, email_service, dry_run=False):
        """Send daily summary to a specific user"""
        self.stdout.write(f'Processing summary for {user.username}...')
        
        if dry_run:
            self.stdout.write(f'  Would send daily summary to {user.email}')
            return True
        else:
            success = email_service.send_daily_weather_summary(user)
            if success:
                self.stdout.write(f'  Sent daily summary to {user.email}')
                return True
            else:
                self.stdout.write(f'  Failed to send summary to {user.email}')
                return False