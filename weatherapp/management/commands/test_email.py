from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import traceback

class Command(BaseCommand):
    help = 'Test email configuration'
    
    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('Testing email configuration...')
        self.stdout.write('='*60)
        self.stdout.write(f'Email Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Email Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'Email Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'Email TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'Email User: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'From Email: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write('='*60)
        
        if not settings.EMAIL_HOST_USER:
            self.stdout.write(self.style.ERROR('✗ EMAIL_HOST_USER is not set!'))
            return
        
        if not settings.EMAIL_HOST_PASSWORD:
            self.stdout.write(self.style.ERROR('✗ EMAIL_HOST_PASSWORD is not set!'))
            return
        
        try:
            self.stdout.write('Sending test email...')
            result = send_mail(
                'Test Email from Climascope',
                'If you receive this, your email configuration is working perfectly!',
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],  # Send to yourself
                fail_silently=False,
            )
            
            if result:
                self.stdout.write(self.style.SUCCESS('✓ Email sent successfully!'))
                self.stdout.write(f'Check your inbox at: {settings.EMAIL_HOST_USER}')
            else:
                self.stdout.write(self.style.ERROR('✗ Email failed to send (no exception but result=0)'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {e}'))
            self.stdout.write('\nFull traceback:')
            traceback.print_exc()
            self.stdout.write('\n' + '='*60)
            self.stdout.write('TROUBLESHOOTING:')
            self.stdout.write('1. Make sure 2FA is enabled on your Gmail account')
            self.stdout.write('2. Generate a new App Password at: https://myaccount.google.com/apppasswords')
            self.stdout.write('3. Update EMAIL_HOST_PASSWORD in your .env file')
            self.stdout.write('4. Restart your Django server')
            self.stdout.write('='*60)