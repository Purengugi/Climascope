from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
import uuid
from datetime import datetime, timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, default=None)
    location = models.CharField(max_length=100, blank=True)

    # Email verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)

    # Notification settings
    email_notifications = models.BooleanField(default=True)
    weather_alerts = models.BooleanField(default=True)
    daily_summary = models.BooleanField(default=False)
    severe_weather_alerts = models.BooleanField(default=True)
    
    # Account status
    is_deactivated = models.BooleanField(default=False)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

    def delete_avatar(self):
        """Helper method to delete avatar"""
        if self.avatar:
            self.avatar.delete(save=False)
            self.avatar = None
            self.save()

    def generate_verification_token(self):
        """Generate a new email verification token"""
        self.email_verification_token = uuid.uuid4()
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token

    def is_verification_token_valid(self):
        """Check if verification token is still valid (24 hours)"""
        if not self.email_verification_sent_at:
            return False
        return timezone.now() < self.email_verification_sent_at + timedelta(hours=24)

class FavoriteCity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    # Alert preferences for this city
    temperature_threshold_high = models.FloatField(null=True, blank=True, default=35.0)
    temperature_threshold_low = models.FloatField(null=True, blank=True, default=5.0)
    notify_rain = models.BooleanField(default=True)
    notify_extreme_weather = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'city_name')
    
    def __str__(self):
        return f"{self.user.username} - {self.city_name}"

class WeatherHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    city_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True)
    temperature = models.FloatField()
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=10)
    humidity = models.IntegerField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    feels_like = models.FloatField(null=True, blank=True)
    searched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-searched_at']
    
    def __str__(self):
        return f"{self.city_name} - {self.searched_at.strftime('%Y-%m-%d %H:%M')}"

class WeatherForecast(models.Model):
    city_name = models.CharField(max_length=100)
    forecast_data = models.TextField()  # JSON string of 5-day forecast
    last_updated = models.DateTimeField(auto_now=True)
    
    def set_forecast_data(self, data):
        self.forecast_data = json.dumps(data)
    
    def get_forecast_data(self):
        return json.loads(self.forecast_data)
    
    def __str__(self):
        return f"{self.city_name} forecast"

class WeatherAlert(models.Model):
    ALERT_TYPES = [
        ('temperature_high', 'High Temperature Alert'),
        ('temperature_low', 'Low Temperature Alert'),
        ('rain', 'Rain Alert'),
        ('storm', 'Storm Alert'),
        ('severe', 'Severe Weather Alert'),
        ('daily_summary', 'Daily Weather Summary'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    temperature = models.FloatField(null=True, blank=True)
    weather_condition = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Alert for {self.user.username} - {self.city_name}"

class EmailNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    email_type = models.CharField(max_length=50)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Email to {self.user.email} - {self.subject}"