import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .decorators import login_required_custom
from .models import AuditLog, Comment, Ticket, TicketHistory

logger = logging.getLogger('tickets')


def _ticket_to_dict(ticket, user):
    profile = user.profile
    return {
        'id': ticket.pk,
        'title': ticket.title,
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'priority': ticket.priority,
        'priority_display': ticket.get_priority_display(),
        'service_type': ticket.service_type,
        'author': ticket.author.get_full_name() or ticket.author.username,
        'assigned_to': (ticket.assigned_to.username if ticket.assigned_to else None),
        'created_at': ticket.created_at.isoformat(),
        'updated_at': ticket.updated_at.isoformat(),
        'can_edit': ticket.can_edit(user),
        'can_change_status': ticket.can_change_status(user),
    }


def _require_auth(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Требуется авторизация'}, status=401)
    return None


@csrf_exempt
def api_tickets(request):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    profile = request.user.profile

    if request.method == 'GET':
        if profile.is_moderator_or_admin():
            qs = Ticket.objects.select_related('author', 'assigned_to').all()
        else:
            qs = Ticket.objects.select_related('author').filter(author=request.user)

        status_filter = request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        data = [_ticket_to_dict(t, request.user) for t in qs[:50]]
        return JsonResponse({'tickets': data, 'count': qs.count()})

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Невалидный JSON'}, status=400)

        required = ('title', 'description', 'service_type')
        missing = [f for f in required if not body.get(f)]
        if missing:
            return JsonResponse({'error': f'Обязательные поля: {", ".join(missing)}'}, status=400)

        ticket = Ticket.objects.create(
            author=request.user,
            title=body['title'],
            description=body['description'],
            service_type=body.get('service_type', 'it'),
            priority=body.get('priority', 'medium'),
        )
        logger.info('API: создана заявка #%d пользователем %s', ticket.pk, request.user.username)
        return JsonResponse({'ticket': _ticket_to_dict(ticket, request.user)}, status=201)

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


@csrf_exempt
def api_ticket_detail(request, pk):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    try:
        ticket = Ticket.objects.select_related('author', 'assigned_to').get(pk=pk)
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Заявка не найдена'}, status=404)

    profile = request.user.profile
    if not profile.is_moderator_or_admin() and ticket.author != request.user:
        return JsonResponse({'error': 'Нет доступа'}, status=403)

    if request.method == 'GET':
        data = _ticket_to_dict(ticket, request.user)
        comments_qs = ticket.comments.select_related('author')
        if not profile.is_moderator_or_admin():
            comments_qs = comments_qs.filter(is_internal=False)
        data['comments'] = [
            {'id': c.pk, 'author': c.author.username, 'text': c.text, 'created_at': c.created_at.isoformat()}
            for c in comments_qs
        ]
        return JsonResponse(data)

    if request.method == 'PATCH':
        if not ticket.can_change_status(request.user):
            return JsonResponse({'error': 'Нет прав для смены статуса'}, status=403)
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Невалидный JSON'}, status=400)

        new_status = body.get('status')
        valid_statuses = [s[0] for s in Ticket.Status.choices]
        if new_status not in valid_statuses:
            return JsonResponse({'error': f'Статус должен быть одним из: {valid_statuses}'}, status=400)

        old_status = ticket.status
        TicketHistory.objects.create(
            ticket=ticket, changed_by=request.user,
            field_name='status', old_value=old_status, new_value=new_status,
        )
        ticket.status = new_status
        ticket.save()
        logger.info('API: статус заявки #%d изменён %s → %s', ticket.pk, old_status, new_status)
        return JsonResponse({'ticket': _ticket_to_dict(ticket, request.user)})

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


def api_audit(request):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    if not request.user.profile.is_admin():
        return JsonResponse({'error': 'Только для администраторов'}, status=403)

    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:100]
    data = [
        {
            'id': log.pk,
            'request_id': log.request_id,
            'user': log.user.username if log.user else None,
            'ip': log.ip_address,
            'method': log.method,
            'path': log.path,
            'status_code': log.status_code,
            'response_time_ms': log.response_time_ms,
            'timestamp': log.timestamp.isoformat(),
        }
        for log in logs
    ]
    return JsonResponse({'logs': data, 'count': AuditLog.objects.count()})
