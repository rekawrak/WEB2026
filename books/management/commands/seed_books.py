from django.core.management.base import BaseCommand
from books.models import Book


class Command(BaseCommand):
    help = "Заполняет базу книгами"

    def handle(self, *args, **kwargs):
        Book.objects.all().delete()

        books = [
            ("1984", "George Orwell", "Dystopian", 1949, 990),
            ("Animal Farm", "George Orwell", "Political Satire", 1945, 850),
            ("Brave New World", "Aldous Huxley", "Science Fiction", 1932, 1150),
            ("Fahrenheit 451", "Ray Bradbury", "Science Fiction", 1953, 970),
            ("Dune", "Frank Herbert", "Science Fiction", 1965, 1590),
            ("The Hobbit", "J.R.R. Tolkien", "Fantasy", 1937, 1250),
            ("The Lord of the Rings", "J.R.R. Tolkien", "Fantasy", 1954, 2490),
            ("Harry Potter and the Philosopher Stone", "J.K. Rowling", "Fantasy", 1997, 1290),
            ("The Catcher in the Rye", "J.D. Salinger", "Classic", 1951, 920),
            ("To Kill a Mockingbird", "Harper Lee", "Classic", 1960, 1040),
        ]

        for title, author, genre, year, price in books:
            Book.objects.create(
                title=title,
                author=author,
                genre=genre,
                year=year,
                price=price,
                description=f"{title} description.",
                is_available=True
            )

        self.stdout.write(self.style.SUCCESS(f"Books created: {Book.objects.count()}"))