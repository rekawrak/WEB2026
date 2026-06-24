import random

from django.core.management.base import BaseCommand

from books.models import Book, Cart, CartItem, Customer


class Command(BaseCommand):
    help = "Заполняет базу покупателями, корзинами и позициями корзин (требует уже созданных книг)"

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

        def fill_cart(cart, n_books):
            chosen = random.sample(books, k=min(len(books), n_books))
            for book in chosen:
                CartItem.objects.create(cart=cart, book=book, quantity=random.randint(1, 3))

        for i, customer in enumerate(customers):
            cart = Cart.objects.create(customer=customer, status=statuses[i % len(statuses)])
            fill_cart(cart, random.randint(1, 4))

        extra_cart = Cart.objects.create(customer=customers[0], status=Cart.Status.ACTIVE)
        fill_cart(extra_cart, 2)

        self.stdout.write(self.style.SUCCESS(
            f"Создано: {len(customers)} покупателей, {Cart.objects.count()} корзин."
        ))
