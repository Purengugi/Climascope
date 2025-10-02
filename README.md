# Climascope

A full-stack weather application built with Django that provides real-time weather data, forecasting, and personalized alerts.

## Features

- Real-time weather data for any location
- 5-day weather forecasts
- User authentication and profiles
- Favorite cities management
- Temperature analytics and charts
- Customizable weather alerts
- Email notifications
- Responsive design

## Tech Stack

- **Backend**: Django 3.1.6, Python 3.13
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **APIs**: OpenWeatherMap API, Google Custom Search API
- **Database**: SQLite (dev) / PostgreSQL (prod)

## Installation

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run server: `python manage.py runserver`

Visit http://127.0.0.1:8000/

## API Keys Required

- OpenWeatherMap API
- Google Custom Search API

## Usage

1. Register at `/signup/`
2. Login at `/login/`
3. Search weather at `/weather/`
4. View analytics at `/dashboard/`
