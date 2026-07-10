from __future__ import annotations
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.conf import settings
from decimal import Decimal
from apps.products.models import Product  # type: ignore[import-not-found]
from django.db.models import F

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
    total_price: models.DecimalField[float, float] = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=Decimal('0.00'))
    shipping_address: models.CharField[str, str] = models.CharField(max_length=255)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id} - {self.user.email}'

    def update_total_price(self):
        agr_result = self.items.aggregate(total_sum=models.Sum(F('quantity') * F('price')))
        total = agr_result['total_sum'] or Decimal('0.00')
        self.total_price = total
        self.save(update_fields=["total_price", "updated_at"])

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')  # type: ignore[var-annotated]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # type: ignore[var-annotated]
    quantity: models.PositiveIntegerField[int, int] = models.PositiveIntegerField(default=1)
    price: models.DecimalField[float, float] = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)])

    def __str__(self):
        return f'{self.order.id} - {self.product.name} {self.quantity}x'

    def save(self, *args, **kwargs):
        # checking for stock on product
        with transaction.atomic():

            # if created
            if not self.pk:
                if self.product.stock < self.quantity:
                    raise ValidationError(
                        f"Not enough stock for {self.product.name}. "
                        f"Available: {self.product.stock}, Requested: {self.quantity}."
                    )
                self.product.stock -= self.quantity
                self.product.save(update_fields=["stock"])
            # if updated
            else:
                old_item = OrderItem.objects.get(pk=self.pk)
                stock_difference = self.quantity - old_item.quantity
                if self.product.stock < stock_difference:
                    raise ValidationError(
                        f"Not enough stock for {self.product.name}. "
                        f"Available: {self.product.stock}, Requested: {stock_difference}."
                    )
                self.product.stock -= stock_difference
                self.product.save(update_fields=["stock"])

        super().save(*args, **kwargs)
        self.order.update_total_price()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self.product.stock += self.quantity
            self.product.save(update_fields=["stock"])
            super().delete(*args, **kwargs)
            self.order.update_total_price()