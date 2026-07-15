from django.core.mail import send_mail
from django.conf import settings
from apps.orders.models import Order # noqa

def send_confirmation_email(order: Order) -> None:
    subject = f"Order #{order.id} placed successfully! | Hop & Barley"

    items_text = ""
    for item in order.items.all():
        items_text += f"{item.quantity}x of {item.product.name} {item.price} $/pc.\n"
    message = (
        f"Hi {order.first_name} {order.middle_name} {order.last_name},\n\n"
        f"Thank you for your order at Hop & Barley!\n"
        f"Your order number is #{order.id}.\n\n"
        f"Order details:\n{items_text}\n"
        f"Total Price: {order.total_price} $\n\n"
        f"Shipping Address: {order.address}\n\n"
        f"We will contact you shortly to confirm shipment."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email, settings.ADMIN_EMAIL],
        fail_silently=False,
    )