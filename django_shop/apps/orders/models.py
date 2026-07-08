from django.db import models
from django.conf import settings

from apps.products.models import Product  # type: ignore[import-not-found]

User = settings.AUTH_USER_MODEL

class Order(models.Model):

    class Status(models.TextChoices):
        pending = ("PENDING", "Pending")
        paid = ("PAID", "Paid")
        shipped = ("SHIPPED", "Shipped")
        delivered = ("DELIVERED", "Delivered")
        cancelled = ("CANCELLED", "Cancelled")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')   # type: ignore[var-annotated]
    status: models.CharField[str, str] = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.pending,
    )
    total_price: models.DecimalField[float, float] = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address: models.CharField[str, str] = models.CharField(max_length=255)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id} - {self.user.email}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # type: ignore[var-annotated]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # type: ignore[var-annotated]
    quantity: models.PositiveIntegerField[int, int] = models.PositiveIntegerField(default=1)
    price: models.DecimalField[float, float] = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.order.id} - {self.product.name} {self.quantity}x'