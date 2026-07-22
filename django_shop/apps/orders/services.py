from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from apps.cart.cart import Cart  # noqa
from apps.orders.models import Order, OrderItem  # noqa


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

def make_order(user, order_data: dict, cart: Cart) -> Order:
    if len(cart) == 0:
        raise ValueError('Cart is empty')

    for item in cart:
        if not item['has_enough_stock']:
            raise ValueError(f'Not enough stock for {item["product"].name}')

    with transaction.atomic():
        order = Order(**order_data)
        if user and user.is_authenticated:
            order.user = user
        order.total_price = cart.get_total_price()
        order.save()

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price'],
            )
        cart.clear()

    return order
