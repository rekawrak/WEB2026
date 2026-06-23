import uuid
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from tickets.models import Comment, Ticket, TicketHistory, UserProfile, UserSettings


class Command(BaseCommand):
    help = "Заполняет портал тестовыми пользователями и заявками"

    def handle(self, *args, **options):
        Ticket.objects.all().delete()
        for u in User.objects.filter(username__in=['admin_user', 'moder_user', 'ivan', 'anna']):
            u.delete()

        def make_user(username, first, last, role, dept, password='demo1234'):
            u = User.objects.create_user(username, f'{username}@corp.ru', password,
                                         first_name=first, last_name=last)
            profile, _ = UserProfile.objects.get_or_create(user=u)
            profile.role = role
            profile.department = dept
            profile.api_token = uuid.uuid4().hex
            profile.save()
            UserSettings.objects.get_or_create(user=u)
            return u

        admin = make_user('admin_user', 'Алексей', 'Сидоров', UserProfile.Role.ADMIN, 'ИТ')
        moder = make_user('moder_user', 'Марина', 'Козлова', UserProfile.Role.MODERATOR, 'Служба поддержки')
        ivan = make_user('ivan', 'Иван', 'Петров', UserProfile.Role.USER, 'Бухгалтерия')
        anna = make_user('anna', 'Анна', 'Смирнова', UserProfile.Role.USER, 'Кадры')

        tickets_data = [
            (ivan, 'Не работает принтер', 'Принтер в комнате 302 выдаёт ошибку...', 'it', 'high', 'in_progress'),
            (ivan, 'Нужен доступ к 1С', 'Прошу предоставить доступ к модулю бухгалтерии.', 'it', 'medium', 'new'),
            (anna, 'Оформление отпуска', 'Прошу оформить отпуск с 15.07 по 28.07.', 'hr', 'low', 'resolved'),
            (anna, 'Компенсация расходов', 'Прошу компенсировать командировочные расходы.', 'finance', 'medium', 'pending'),
            (ivan, 'Сломался монитор', 'Монитор не включается. Требуется замена.', 'it', 'critical', 'new'),
        ]

        for author, title, desc, stype, prio, status in tickets_data:
            t = Ticket.objects.create(
                author=author, title=title, description=desc,
                service_type=stype, priority=prio, status=status,
            )
            if status != 'new':
                TicketHistory.objects.create(
                    ticket=t, changed_by=moder,
                    field_name='status', old_value='new', new_value=status,
                )
            Comment.objects.create(
                ticket=t, author=moder,
                text='Заявка принята в обработку, уточняем детали.',
                is_internal=False,
            )
            if status in ('in_progress', 'resolved'):
                Comment.objects.create(
                    ticket=t, author=moder,
                    text='[Внутренний] Назначен исполнитель.',
                    is_internal=True,
                )

        self.stdout.write(self.style.SUCCESS(
            f"Создано 4 пользователя (admin_user/moder_user/ivan/anna), пароль: demo1234\n"
            f"Создано {Ticket.objects.count()} заявок."
        ))
