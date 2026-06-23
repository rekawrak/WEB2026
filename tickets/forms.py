from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Comment, Ticket, UserProfile, UserSettings


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input', 'autofocus': True}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'service_type', 'priority', 'attachment')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'service_type': forms.Select(attrs={'class': 'form-input'}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'title': 'Заголовок',
            'description': 'Описание проблемы',
            'service_type': 'Тип сервиса',
            'priority': 'Приоритет',
            'attachment': 'Прикреплённый файл',
        }


class TicketEditForm(TicketForm):
    pass


class StatusChangeForm(forms.Form):
    status = forms.ChoiceField(
        label='Новый статус',
        choices=Ticket.Status.choices,
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    comment = forms.CharField(
        label='Комментарий к смене статуса',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'is_internal')
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'text': 'Комментарий',
            'is_internal': 'Внутренний комментарий (только для модераторов)',
        }


class TicketFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Все статусы')] + list(Ticket.Status.choices)
    PRIORITY_CHOICES = [('', 'Все приоритеты')] + list(Ticket.Priority.choices)
    SERVICE_CHOICES = [('', 'Все сервисы')] + list(Ticket.ServiceType.choices)

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-input'}))
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-input'}))
    service_type = forms.ChoiceField(choices=SERVICE_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-input'}))
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Поиск по заголовку...'}))


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ('notifications_enabled', 'theme')
        widgets = {
            'notifications_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'theme': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'notifications_enabled': 'Email-уведомления',
            'theme': 'Тема оформления',
        }
