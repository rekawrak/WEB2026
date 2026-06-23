from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import AuditLog, Comment, Ticket, TicketHistory, UserProfile, UserSettings

admin.site.site_header = 'Корпоративный портал заявок'


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fields = ('role', 'department', 'phone', 'api_token')
    readonly_fields = ('api_token',)


class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    can_delete = False
    verbose_name_plural = 'Настройки'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserSettingsInline)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'status', 'priority', 'service_type', 'created_at')
    list_filter = ('status', 'priority', 'service_type')
    search_fields = ('title', 'description', 'author__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal',)


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'changed_by', 'field_name', 'old_value', 'new_value', 'changed_at')
    readonly_fields = ('ticket', 'changed_by', 'field_name', 'old_value', 'new_value', 'changed_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'request_id', 'user', 'ip_address', 'method', 'path', 'status_code', 'response_time_ms')
    list_filter = ('method', 'status_code')
    search_fields = ('request_id', 'path', 'user__username', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = [f.name for f in AuditLog._meta.fields]
