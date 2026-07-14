from django.dispatch import receiver
from django.db.models.signals import post_save
from .services import send_confirmation_email
from django.db import transaction

from .models import Order

@receiver(post_save, sender=Order)
def send_order_confirmation_email(sender, instance, created, **kwargs) -> None:
    if created:
        try:
            transaction.on_commit(lambda: send_confirmation_email(instance))
        except Exception as e:
            print(f'Error sending confirmation email: {e}')
            