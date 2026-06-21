import random

from django.core.management.base import BaseCommand

from books.models import Book, Cart, Customer


class Command(BaseCommand):
    help = "Заполняет базу покупателями и корзинами (требует уже созданных книг)"

    def handle(self, *args, **options):
        books = list(Book.objects.all())
        if not books:
            self.stdout.write(self.style.ERROR(
                "Сначала выполните: python manage.py seed_books"
            ))
            return

        Cart.objects.all().delete()
        Customer.objects.all().delete()

        customers = [
            Customer.objects.create(
                first_name="Иван", last_name="Петров",
                email="petrov@example.com", phone="+79001112233",
            ),
            Customer.objects.create(
                first_name="Анна", last_name="Смирнова",
                email="smirnova@example.com", phone="+79002223344",
            ),
            Customer.objects.create(
                first_name="Дмитрий", last_name="Кузнецов",
                email="kuznetsov@example.com", phone="+79003334455",
            ),
        ]

        statuses = [Cart.Status.ACTIVE, Cart.Status.COMPLETED, Cart.Status.CANCELLED]
        for i, customer in enumerate(customers):
            cart = Cart.objects.create(customer=customer, status=statuses[i % len(statuses)])
            cart.books.set(random.sample(books, k=min(len(books), random.randint(1, 4))))

        extra_cart = Cart.objects.create(customer=customers[0], status=Cart.Status.ACTIVE)
        extra_cart.books.set(random.sample(books, k=min(len(books), 2)))

        self.stdout.write(self.style.SUCCESS(
            f"Создано: {len(customers)} покупателей, {Cart.objects.count()} корзин."
        ))
