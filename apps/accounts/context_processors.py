from django.conf import settings
from django.utils import timezone

from .utils import get_primary_role


def user_roles(request):
    if request.user.is_authenticated:
        roles_list = list(request.user.roles.values_list('nombre', flat=True))
        return {
            'user_roles': roles_list,
            'primary_role': get_primary_role(roles_list),
        }
    return {'user_roles': [], 'primary_role': None}


def session_expiry(request):
    if not request.user.is_authenticated:
        return {}
    last_login = request.user.last_login
    if last_login and timezone.is_aware(last_login):
        elapsed = (timezone.now() - last_login).total_seconds()
        remaining = max(0, settings.SESSION_COOKIE_AGE - elapsed)
        return {'session_remaining_seconds': int(remaining)}
    return {}
