from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from weatherapp.models import WeatherHistory, WeatherAlert, EmailNotification, WeatherForecast
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up old weather data and notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--history-days',
            type=int,
            default=90,
            help='Days to keep weather history (default: 90)',
        )
        parser.add_argument(
            '--alerts-days',
            type=int,
            default=30,
            help='Days to keep sent alerts (default: 30)',
        )
        parser.add_argument(
            '--notifications-days',
            type=int,
            default=60,
            help='Days to keep email notifications (default: 60)',
        )
        parser.add_argument(
            '--forecast-hours',
            type=int,
            default=24,
            help='Hours to keep old forecast data (default: 24)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting data cleanup...')
        )
        
        total_deleted = 0
        
        # Clean up weather history
        history_deleted = self.cleanup_weather_history(
            options['history_days'], options['dry_run']
        )
        total_deleted += history_deleted
        
        # Clean up alerts
        alerts_deleted = self.cleanup_weather_alerts(
            options['alerts_days'], options['dry_run']
        )
        total_deleted += alerts_deleted
        
        # Clean up email notifications
        notifications_deleted = self.cleanup_email_notifications(
            options['notifications_days'], options['dry_run']
        )
        total_deleted += notifications_deleted
        
        # Clean up old forecasts
        forecasts_deleted = self.cleanup_forecasts(
            options['forecast_hours'], options['dry_run']
        )
        total_deleted += forecasts_deleted
        
        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'Would delete {total_deleted} total records')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {total_deleted} total records')
            )
    
    def cleanup_weather_history(self, days, dry_run=False):
        """Clean up old weather history records"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        old_records = WeatherHistory.objects.filter(searched_at__lt=cutoff_date)
        count = old_records.count()
        
        if count > 0:
            if dry_run:
                self.stdout.write(f'Would delete {count} weather history records older than {days} days')
            else:
                old_records.delete()
                self.stdout.write(f'Deleted {count} weather history records older than {days} days')
                logger.info(f'Cleanup: Deleted {count} weather history records')
        else:
            self.stdout.write('No old weather history records to delete')
        
        return count
    
    def cleanup_weather_alerts(self, days, dry_run=False):
        """Clean up old sent weather alerts"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        old_alerts = WeatherAlert.objects.filter(
            created_at__lt=cutoff_date,
            is_sent=True
        )
        count = old_alerts.count()
        
        if count > 0:
            if dry_run:
                self.stdout.write(f'Would delete {count} sent alerts older than {days} days')
            else:
                old_alerts.delete()
                self.stdout.write(f'Deleted {count} sent alerts older than {days} days')
                logger.info(f'Cleanup: Deleted {count} weather alerts')
        else:
            self.stdout.write('No old weather alerts to delete')
        
        return count
    
    def cleanup_email_notifications(self, days, dry_run=False):
        """Clean up old email notification records"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        old_notifications = EmailNotification.objects.filter(
            created_at__lt=cutoff_date,
            is_sent=True
        )
        count = old_notifications.count()
        
        if count > 0:
            if dry_run:
                self.stdout.write(f'Would delete {count} email notifications older than {days} days')
            else:
                old_notifications.delete()
                self.stdout.write(f'Deleted {count} email notifications older than {days} days')
                logger.info(f'Cleanup: Deleted {count} email notifications')
        else:
            self.stdout.write('No old email notifications to delete')
        
        return count
    
    def cleanup_forecasts(self, hours, dry_run=False):
        """Clean up old forecast data"""
        cutoff_date = timezone.now() - timedelta(hours=hours)
        
        old_forecasts = WeatherForecast.objects.filter(last_updated__lt=cutoff_date)
        count = old_forecasts.count()
        
        if count > 0:
            if dry_run:
                self.stdout.write(f'Would delete {count} forecast records older than {hours} hours')
            else:
                old_forecasts.delete()
                self.stdout.write(f'Deleted {count} forecast records older than {hours} hours')
                logger.info(f'Cleanup: Deleted {count} forecast records')
        else:
            self.stdout.write('No old forecast data to delete')
        
        return count