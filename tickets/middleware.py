import logging
import time
import uuid

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone

from .log_filters import _request_id_local

logger = logging.getLogger('tickets')


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request.request_id = request_id
        _request_id_local.request_id = request_id

        logger.debug('Входящий запрос %s %s', request.method, request.path)

        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response


class AutoUserDetectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            token = request.headers.get('X-API-Token') or request.GET.get('api_token')
            if token:
                try:
                    from tickets.models import UserProfile
                    profile = UserProfile.objects.select_related('user').get(api_token=token)
                    request.user = profile.user
                    request._api_token_auth = True
                except Exception:
                    pass

        return self.get_response(request)


class BusinessHoursMiddleware:
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
    EXCLUDED_PATHS = ('/admin/', '/login/', '/logout/')

    def __init__(self, get_response):
        self.get_response = get_response

    def _is_business_hours(self):
        now = timezone.localtime(timezone.now())
        start = getattr(settings, 'BUSINESS_HOURS_START', 9)
        end = getattr(settings, 'BUSINESS_HOURS_END', 18)
        return now.weekday() < 5 and start <= now.hour < end

    def __call__(self, request):
        if (
            request.method not in self.SAFE_METHODS
            and not any(request.path.startswith(p) for p in self.EXCLUDED_PATHS)
            and request.user.is_authenticated
        ):
            try:
                is_admin = request.user.profile.is_admin()
            except Exception:
                is_admin = request.user.is_superuser

            if not is_admin and not self._is_business_hours():
                now = timezone.localtime(timezone.now())
                start = getattr(settings, 'BUSINESS_HOURS_START', 9)
                end = getattr(settings, 'BUSINESS_HOURS_END', 18)
                if request.path.startswith('/api/') or request.META.get('HTTP_ACCEPT') == 'application/json':
                    return JsonResponse({
                        'error': 'Операция запрещена вне рабочего времени',
                        'allowed_hours': f'{start}:00 – {end}:00 (пн-пт)',
                        'server_time': now.strftime('%d.%m.%Y %H:%M'),
                    }, status=403)
                from django.shortcuts import render
                return render(request, 'tickets/business_hours_block.html', {
                    'allowed_hours': f'{start}:00 – {end}:00',
                    'server_time': now,
                }, status=403)

        return self.get_response(request)


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = getattr(settings, 'RATE_LIMIT_PATHS', {})

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

    def _find_limit(self, path):
        for pattern, limits in self.rate_limits.items():
            if path.startswith(pattern):
                return limits
        return None

    def __call__(self, request):
        limit_config = self._find_limit(request.path)

        if limit_config:
            max_requests, window_seconds = limit_config
            ip = self._get_client_ip(request)
            cache_key = f'ratelimit:{ip}:{request.path}'
            current = cache.get(cache_key, 0)

            if current >= max_requests:
                logger.warning(
                    'Rate limit exceeded: ip=%s path=%s request_id=%s',
                    ip, request.path, getattr(request, 'request_id', '-')
                )
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'Слишком много запросов',
                        'retry_after_seconds': window_seconds,
                    }, status=429)
                from django.shortcuts import render
                return render(request, 'tickets/rate_limit.html', {'window': window_seconds}, status=429)

            if current == 0:
                cache.set(cache_key, 1, window_seconds)
            else:
                cache.incr(cache_key)

        return self.get_response(request)


class AuditMiddleware:
    SKIP_PATHS = ('/static/', '/media/', '/favicon.ico')

    def __init__(self, get_response):
        self.get_response = get_response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def __call__(self, request):
        if any(request.path.startswith(p) for p in self.SKIP_PATHS):
            return self.get_response(request)

        start_time = time.monotonic()
        response = self.get_response(request)
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        try:
            from tickets.models import AuditLog
            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(
                request_id=getattr(request, 'request_id', ''),
                user=user,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                method=request.method,
                path=request.path[:500],
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
            )
            logger.info(
                '%s %s → %s (%dms) user=%s',
                request.method, request.path,
                response.status_code, elapsed_ms,
                user.username if user else 'anonymous',
            )
        except Exception:
            pass

        return response
