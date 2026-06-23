import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import login_required_custom, moderator_required
from .forms import (
    CommentForm, LoginForm, StatusChangeForm,
    TicketEditForm, TicketFilterForm, TicketForm, UserSettingsForm,
)
from .models import AuditLog, Comment, Ticket, TicketHistory, UserProfile, UserSettings

logger = logging.getLogger('tickets')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('ticket_list')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        logger.info('Пользователь %s вошёл в систему', user.username)
        return redirect('ticket_list')
    return render(request, 'tickets/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logger.info('Пользователь %s вышел из системы', request.user.username)
        logout(request)
    return redirect('login')


@login_required_custom
def ticket_list(request):
    profile = request.user.profile
    if profile.is_moderator_or_admin():
        qs = Ticket.objects.select_related('author', 'assigned_to').all()
    else:
        qs = Ticket.objects.select_related('author').filter(author=request.user)

    filter_form = TicketFilterForm(request.GET)
    if filter_form.is_valid():
        d = filter_form.cleaned_data
        if d.get('status'):
            qs = qs.filter(status=d['status'])
        if d.get('priority'):
            qs = qs.filter(priority=d['priority'])
        if d.get('service_type'):
            qs = qs.filter(service_type=d['service_type'])
        if d.get('search'):
            qs = qs.filter(title__icontains=d['search'])

    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'tickets/list.html', {
        'page': page,
        'filter_form': filter_form,
        'profile': profile,
    })


@login_required_custom
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related('author', 'assigned_to'), pk=pk)
    profile = request.user.profile

    if not profile.is_moderator_or_admin() and ticket.author != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    comments = ticket.comments.select_related('author').all()
    if not profile.is_moderator_or_admin():
        comments = comments.filter(is_internal=False)

    comment_form = CommentForm()
    status_form = StatusChangeForm(initial={'status': ticket.status})

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'comment':
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.ticket = ticket
                comment.author = request.user
                if not profile.is_moderator_or_admin():
                    comment.is_internal = False
                comment.save()
                logger.info('Комментарий к заявке #%d от %s', ticket.pk, request.user.username)
                messages.success(request, 'Комментарий добавлен.')
                return redirect('ticket_detail', pk=pk)

        elif action == 'status' and ticket.can_change_status(request.user):
            status_form = StatusChangeForm(request.POST)
            if status_form.is_valid():
                old_status = ticket.status
                new_status = status_form.cleaned_data['status']
                with transaction.atomic():
                    TicketHistory.objects.create(
                        ticket=ticket,
                        changed_by=request.user,
                        field_name='status',
                        old_value=old_status,
                        new_value=new_status,
                    )
                    ticket.status = new_status
                    ticket.save()
                    if status_form.cleaned_data.get('comment'):
                        Comment.objects.create(
                            ticket=ticket,
                            author=request.user,
                            text=status_form.cleaned_data['comment'],
                            is_internal=True,
                        )
                logger.info('Статус заявки #%d изменён %s → %s', ticket.pk, old_status, new_status)
                messages.success(request, f'Статус изменён: {ticket.get_status_display()}')
                return redirect('ticket_detail', pk=pk)

    history = ticket.history.select_related('changed_by').all()
    return render(request, 'tickets/detail.html', {
        'ticket': ticket,
        'comments': comments,
        'comment_form': comment_form,
        'status_form': status_form,
        'history': history,
        'profile': profile,
    })


@login_required_custom
def ticket_create(request):
    form = TicketForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.author = request.user
        ticket.save()
        logger.info('Создана заявка #%d пользователем %s', ticket.pk, request.user.username)
        messages.success(request, f'Заявка #{ticket.pk} создана.')
        return redirect('ticket_detail', pk=ticket.pk)
    return render(request, 'tickets/create.html', {'form': form})


@login_required_custom
def ticket_edit(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not ticket.can_edit(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    form = TicketEditForm(request.POST or None, request.FILES or None, instance=ticket)
    if request.method == 'POST' and form.is_valid():
        changed = form.changed_data
        with transaction.atomic():
            for field in changed:
                TicketHistory.objects.create(
                    ticket=ticket,
                    changed_by=request.user,
                    field_name=field,
                    old_value=str(getattr(ticket, field, '')),
                    new_value=str(form.cleaned_data.get(field, '')),
                )
            form.save()
        logger.info('Заявка #%d отредактирована %s', ticket.pk, request.user.username)
        messages.success(request, 'Заявка обновлена.')
        return redirect('ticket_detail', pk=ticket.pk)
    return render(request, 'tickets/edit.html', {'form': form, 'ticket': ticket})


@moderator_required
def moderator_panel(request):
    stats = {
        'total': Ticket.objects.count(),
        'new': Ticket.objects.filter(status='new').count(),
        'in_progress': Ticket.objects.filter(status='in_progress').count(),
        'resolved': Ticket.objects.filter(status='resolved').count(),
        'rejected': Ticket.objects.filter(status='rejected').count(),
    }
    recent_tickets = Ticket.objects.select_related('author').order_by('-created_at')[:10]
    recent_audit = AuditLog.objects.select_related('user').order_by('-timestamp')[:20]

    users = User.objects.select_related('profile').all()

    return render(request, 'tickets/moderator.html', {
        'stats': stats,
        'recent_tickets': recent_tickets,
        'recent_audit': recent_audit,
        'users': users,
        'profile': request.user.profile,
    })


@login_required_custom
def settings_view(request):
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    form = UserSettingsForm(request.POST or None, instance=settings_obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Настройки сохранены.')
        return redirect('settings')
    token = request.user.profile.api_token
    return render(request, 'tickets/settings.html', {
        'form': form,
        'token': token,
        'profile': request.user.profile,
    })


@login_required_custom
def generate_token(request):
    if request.method == 'POST':
        request.user.profile.generate_token()
        messages.success(request, 'API-токен сгенерирован.')
    return redirect('settings')
