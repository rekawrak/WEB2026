from django.urls import path

from . import api_views, views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/create/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:pk>/edit/', views.ticket_edit, name='ticket_edit'),
    path('moderator/', views.moderator_panel, name='moderator_panel'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/token/', views.generate_token, name='generate_token'),
    path('api/tickets/', api_views.api_tickets, name='api_tickets'),
    path('api/tickets/<int:pk>/', api_views.api_ticket_detail, name='api_ticket_detail'),
    path('api/audit/', api_views.api_audit, name='api_audit'),
]
