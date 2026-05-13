from django.shortcuts import render
from .models import Book


def book_list(request):
    books = Book.objects.all()

    context = {
        "books": books
    }

    return render(request, "books/book_list.html", context)