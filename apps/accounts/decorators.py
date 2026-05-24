from functools import wraps

from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                return redirect('accounts:login')
            user_roles = set(
                request.user.roles.values_list('nombre', flat=True)
            )
            if not user_roles.intersection(roles):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class RoleRequiredMixin:
    roles_requeridos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('accounts:login')
        user_roles = set(
            request.user.roles.values_list('nombre', flat=True)
        )
        if not user_roles.intersection(self.roles_requeridos):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
