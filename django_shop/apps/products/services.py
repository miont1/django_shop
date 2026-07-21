from django.contrib.auth import get_user_model
from apps.orders.models import Order, OrderItem # noqa
from .models import Product, Review

User = get_user_model()

def has_user_reviewed_product(user: User, product: Product) -> bool:
    return Review.objects.filter(user=user, product=product).exists()

def has_user_purchased_product(user: User, product: Product) -> bool:
    return Order.objects.filter(user=user, items__product=product, status__in=Order.PAID_STATUS_CHOICES).exists()

def check_user_for_review_eligible(user: User, product: Product) -> bool:
    if has_user_reviewed_product(user, product):
        return False
    return has_user_purchased_product(user, product)