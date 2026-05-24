from datetime import timedelta
from django.conf import settings
from django.utils import timezone


def user_roles(request):
    if request.user.is_authenticated:
        return {'user_roles': list(request.user.roles.values_list('nombre', flat=True))}
    return {'user_roles': []}


def session_expiry(request):
    if not request.user.is_authenticated:
        return {}
    login_time = request.session.get('login_time')
    if login_time:
        elapsed = (timezone.now() - login_time).total_seconds()
        remaining = max(0, settings.SESSION_COOKIE_AGE - elapsed)
        return {'session_remaining_seconds': int(remaining)}
    return {}
