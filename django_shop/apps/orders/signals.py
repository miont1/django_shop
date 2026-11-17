from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order
from .services import schedule_confirmation_email


@receiver(post_save, sender=Order)
def send_order_confirmation_email(sender, instance: Order, created: bool, **kwargs) -> None:
    if created and instance.payment_method == Order.PaymentMethod.CASH:
        schedule_confirmation_email(instance)
