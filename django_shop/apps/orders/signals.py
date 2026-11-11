import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order
from .services import send_confirmation_email

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def send_order_confirmation_email(sender, instance, created, **kwargs) -> None:
    if created:
        def _send_email():
            try:
                send_confirmation_email(instance)
            except Exception as e:
                logger.error(f'Error sending confirmation email for order #{instance.id}: {e}')

        transaction.on_commit(_send_email)
            