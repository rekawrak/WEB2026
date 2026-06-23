import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField('Роль', max_length=20, choices=Role.choices, default=Role.USER)
    department = models.CharField('Отдел', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=30, blank=True)
    api_token = models.CharField('API-токен', max_length=64, blank=True, unique=True, null=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'

    def is_moderator_or_admin(self):
        return self.role in (self.Role.MODERATOR, self.Role.ADMIN)

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def generate_token(self):
        self.api_token = uuid.uuid4().hex + uuid.uuid4().hex
        self.save()
        return self.api_token


class UserSettings(models.Model):
    class Theme(models.TextChoices):
        LIGHT = 'light', 'Светлая'
        DARK = 'dark', 'Тёмная'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    notifications_enabled = models.BooleanField('Email-уведомления', default=True)
    theme = models.CharField('Тема', max_length=10, choices=Theme.choices, default=Theme.LIGHT)

    class Meta:
        verbose_name = 'Настройки пользователя'
        verbose_name_plural = 'Настройки пользователей'

    def __str__(self):
        return f'Настройки {self.user.username}'


class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'В работе'
        PENDING = 'pending', 'Ожидает ответа'
        RESOLVED = 'resolved', 'Решена'
        REJECTED = 'rejected', 'Отклонена'

    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        MEDIUM = 'medium', 'Средний'
        HIGH = 'high', 'Высокий'
        CRITICAL = 'critical', 'Критический'

    class ServiceType(models.TextChoices):
        IT = 'it', 'ИТ-поддержка'
        HR = 'hr', 'Кадры'
        FINANCE = 'finance', 'Финансы'
        ADMIN = 'admin', 'Административный'
        OTHER = 'other', 'Прочее'

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets', verbose_name='Автор')
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tickets', verbose_name='Назначен'
    )
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')
    service_type = models.CharField('Тип сервиса', max_length=20, choices=ServiceType.choices, default=ServiceType.IT)
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default=Status.NEW)
    priority = models.CharField('Приоритет', max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    attachment = models.FileField('Прикреплённый файл', upload_to='tickets/', blank=True, null=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.pk} {self.title}'

    def can_edit(self, user):
        if user.profile.is_moderator_or_admin():
            return True
        return user == self.author and self.status == self.Status.NEW

    def can_change_status(self, user):
        return user.profile.is_moderator_or_admin()

    USER_ALLOWED_STATUS_TRANSITIONS = {
        Status.NEW: [Status.REJECTED],
    }


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments', verbose_name='Заявка')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name='Автор')
    text = models.TextField('Текст')
    is_internal = models.BooleanField('Внутренний (только для модераторов)', default=False)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']

    def __str__(self):
        return f'Комментарий к #{self.ticket_id} от {self.author.username}'


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history', verbose_name='Заявка')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Кто изменил')
    field_name = models.CharField('Поле', max_length=50)
    old_value = models.TextField('Было', blank=True)
    new_value = models.TextField('Стало', blank=True)
    changed_at = models.DateTimeField('Время изменения', auto_now_add=True)

    class Meta:
        verbose_name = 'История изменения'
        verbose_name_plural = 'История изменений'
        ordering = ['-changed_at']

    def __str__(self):
        return f'#{self.ticket_id}: {self.field_name} изменено {self.changed_at:%d.%m.%Y %H:%M}'


class AuditLog(models.Model):
    request_id = models.CharField('Request ID', max_length=36, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    ip_address = models.GenericIPAddressField('IP-адрес', null=True, blank=True)
    user_agent = models.TextField('User-Agent', blank=True)
    method = models.CharField('Метод', max_length=10)
    path = models.CharField('Путь', max_length=500)
    status_code = models.PositiveSmallIntegerField('Код ответа', null=True, blank=True)
    response_time_ms = models.PositiveIntegerField('Время ответа (мс)', null=True, blank=True)
    timestamp = models.DateTimeField('Время', default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'Аудит-лог'
        verbose_name_plural = 'Аудит-лог'
        ordering = ['-timestamp']

    def __str__(self):
        return f'[{self.timestamp:%d.%m.%Y %H:%M}] {self.method} {self.path} → {self.status_code}'
