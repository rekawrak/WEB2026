from django.shortcuts import render
from .models import Book, Cart


def book_list(request):
    books = Book.objects.all()

    context = {
        "books": books
    }

    return render(request, "books/book_list.html", context)


def cart_list(request):
    carts = (
        Cart.objects.select_related("customer")
        .prefetch_related("items__book")
        .all()
    )

    context = {
        "carts": carts
    }

    return render(request, "books/cart_list.html", context)