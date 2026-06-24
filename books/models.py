from django.core.validators import MinValueValidator
from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Customer(models.Model):
    first_name = models.CharField("Имя", max_length=100)
    last_name = models.CharField("Фамилия", max_length=100)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    registered_at = models.DateTimeField("Дата регистрации", auto_now_add=True)

    class Meta:
        verbose_name = "Покупатель"
        verbose_name_plural = "Покупатели"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Cart(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активна"
        COMPLETED = "completed", "Завершена"
        CANCELLED = "cancelled", "Отменена"

    customer = models.ForeignKey(
        Customer,
        verbose_name="Покупатель",
        related_name="carts",
        on_delete=models.CASCADE,
    )
    books = models.ManyToManyField(
        Book,
        verbose_name="Книги",
        related_name="carts",
        through="CartItem",
        blank=True,
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Корзина №{self.pk} ({self.customer})"

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum((item.subtotal for item in self.items.all()), start=0)

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        verbose_name="Корзина",
        related_name="items",
        on_delete=models.CASCADE,
    )
    book = models.ForeignKey(
        Book,
        verbose_name="Книга",
        related_name="cart_items",
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveSmallIntegerField(
        "Количество",
        default=1,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = "Позиция корзины"
        verbose_name_plural = "Позиции корзины"
        unique_together = ("cart", "book")
        ordering = ["id"]

    def __str__(self):
        return f"{self.book} * {self.quantity}"

    @property
    def subtotal(self):
        return self.book.price * self.quantity