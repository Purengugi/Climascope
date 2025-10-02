Climascope
A full-stack weather application built with Django that provides real-time weather data, forecasting, and personalized alerts.
Features

Real-time weather data for any location
5-day weather forecasts
User authentication and profiles
Favorite cities management
Temperature analytics and charts
Customizable weather alerts
Email notifications
Responsive design

Tech Stack

Backend: Django 3.1.6, Python 3.13
Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
APIs: OpenWeatherMap API, Google Custom Search API
Database: SQLite (dev) / PostgreSQL (prod)

Installation

Clone the repository

bashgit clone https://github.com/yourusername/climascope.git
cd climascope

Create virtual environment

bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies

bashpip install -r requirements.txt

Set up environment variables
Create a .env file with:

WEATHER_API_KEY=your_openweathermap_key
GOOGLE_API_KEY=your_google_key
SEARCH_ENGINE_ID=your_search_engine_id
SECRET_KEY=your_django_secret_key

Run migrations

bashpython manage.py migrate

Create superuser

bashpython manage.py createsuperuser

Run the server

bashpython manage.py runserver

Visit http://127.0.0.1:8000/

Usage

Register for an account at /signup/
Log in at /login/
Search for weather at /weather/
View analytics at /dashboard/
Manage settings at /settings/

API Keys
Get your API keys from:

OpenWeatherMap: https://openweathermap.org/api
Google Custom Search: https://console.cloud.google.com/

Configuration
Edit weatherproject/settings.py for email configuration:
pythonEMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
Key Models

UserProfile: User settings and preferences
FavoriteCity: Saved locations
WeatherHistory: Search history
WeatherAlert: Notification system

Deployment
For production:

Set DEBUG = False
Configure ALLOWED_HOSTS
Use PostgreSQL database
Set up static files with collectstatic
Use Gunicorn + Nginx

Contributing

Fork the repository
Create a feature branch
Commit your changes
Push to the branch
Open a Pull Request
