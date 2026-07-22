from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order
from .services import send_confirmation_email


@receiver(post_save, sender=Order)
def send_order_confirmation_email(sender, instance, created, **kwargs) -> None:
    if created:
        try:
            transaction.on_commit(lambda: send_confirmation_email(instance))
        except Exception as e:
            print(f'Error sending confirmation email: {e}')
            