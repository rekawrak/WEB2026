from django.contrib import admin
from django.db.models import DecimalField, F, Sum
from django.utils.html import format_html

from .models import Book, Cart, CartItem, Customer

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


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    autocomplete_fields = ("book",)
    fields = ("book", "quantity", "subtotal_display")
    readonly_fields = ("subtotal_display",)

    @admin.display(description="Сумма по позиции")
    def subtotal_display(self, obj):
        if obj.pk:
            return f"{obj.subtotal} ₽"
        return "—"


STATUS_COLORS = {
    Cart.Status.ACTIVE: "#16a34a",
    Cart.Status.COMPLETED: "#4b5563",
    Cart.Status.CANCELLED: "#dc2626",
}


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = (CartItemInline,)
    list_display = (
        "id",
        "customer",
        "status_badge",
        "qty_total_display",
        "cost_total_display",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "id",
        "customer__first_name",
        "customer__last_name",
        "customer__email",
        "items__book__title",
    )
    autocomplete_fields = ("customer",)
    date_hierarchy = "created_at"
    fields = ("customer", "status", "created_at", "totals_block")
    readonly_fields = ("created_at", "totals_block")

    class Media:
        css = {"all": ("books/admin/cart_admin.css",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("customer").prefetch_related("items__book").annotate(
            qty_total=Sum("items__quantity"),
            cost_total=Sum(
                F("items__quantity") * F("items__book__price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )

    @admin.display(description="Кол-во единиц", ordering="qty_total")
    def qty_total_display(self, obj):
        return obj.qty_total or 0

    @admin.display(description="Сумма", ordering="cost_total")
    def cost_total_display(self, obj):
        return f"{obj.cost_total or 0} ₽"

    @admin.display(description="Статус")
    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#4b5563")
        css_class = f"cart-row-status cart-row-status-{obj.status}"
        return format_html(
            '<span class="{}" style="background:{}; color:#fff; padding:3px 10px; '
            'border-radius:10px; font-size:12px; font-weight:600;">{}</span>',
            css_class, color, obj.get_status_display(),
        )

    @admin.display(description="Итоги по корзине")
    def totals_block(self, obj):
        if not obj.pk:
            return "Сохраните корзину, чтобы увидеть итоги"
        return format_html(
            '<div style="background:#f3f4f6; border-radius:10px; padding:14px 18px; '
            'display:inline-block; line-height:1.9; font-size:14px;">'
            'Суммарное количество единиц товара: <b>{}</b><br>'
            'Итоговая стоимость корзины: <b>{} ₽</b>'
            '</div>',
            obj.total_quantity, obj.total_price,
        )
