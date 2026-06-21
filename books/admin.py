from django.contrib import admin
from django.db.models import Count

from .models import Book, Cart, Customer

admin.site.site_header = "Администрирование"
admin.site.site_title = "Админ-панель каталога книг"
admin.site.index_title = "Управление каталогом"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "genre", "year", "price", "is_available", "created_at")
    list_filter = ("genre", "is_available", "year")
    search_fields = ("title", "author", "genre")
    ordering = ("-created_at",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "registered_at", "carts_count")
    search_fields = ("first_name", "last_name", "email", "phone")
    list_filter = ("registered_at",)
    ordering = ("last_name", "first_name")

    @admin.display(description="Корзин")
    def carts_count(self, obj):
        return obj.carts.count()


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "status",
        "items_count",
        "total_price_display",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "id",
        "customer__first_name",
        "customer__last_name",
        "customer__email",
        "books__title",
    )
    filter_horizontal = ("books",)
    autocomplete_fields = ("customer",)
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("customer").annotate(
            items_total=Count("books", distinct=True)
        )

    @admin.display(description="Кол-во книг", ordering="items_total")
    def items_count(self, obj):
        return obj.items_total

    @admin.display(description="Сумма")
    def total_price_display(self, obj):
        return f"{obj.total_price} ₽"
