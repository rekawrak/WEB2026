from django.urls import path
from .views import book_list, cart_list

urlpatterns = [
    path("", book_list, name="book_list"),
    path("carts/", cart_list, name="cart_list"),
]