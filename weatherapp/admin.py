from django.contrib import admin
from .models import UserProfile, FavoriteCity, WeatherHistory, WeatherForecast

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'email_notifications', 'weather_alerts', 'is_deactivated']
    list_filter = ['email_notifications', 'weather_alerts', 'is_deactivated', 'deactivated_at']
    search_fields = ['user__username', 'user__email', 'location']
    readonly_fields = ['deactivated_at']

@admin.register(FavoriteCity)
class FavoriteCityAdmin(admin.ModelAdmin):
    list_display = ['user', 'city_name', 'country', 'added_at']
    list_filter = ['country', 'added_at']
    search_fields = ['user__username', 'city_name', 'country']

@admin.register(WeatherHistory)
class WeatherHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'city_name', 'temperature', 'description', 'searched_at']
    list_filter = ['searched_at', 'description']
    search_fields = ['user__username', 'city_name', 'description']
    readonly_fields = ['searched_at']

@admin.register(WeatherForecast)
class WeatherForecastAdmin(admin.ModelAdmin):
    list_display = ['city_name', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['city_name']