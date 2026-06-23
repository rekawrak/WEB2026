from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                if request.user.profile.role not in roles:
                    raise PermissionDenied
            except AttributeError:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def moderator_required(view_func):
    return role_required('moderator', 'admin')(view_func)


def login_required_custom(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped
