import logging
from collections import defaultdict
from decimal import Decimal
from typing import Any

import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Case, F, PositiveIntegerField, When
from django.http import HttpRequest
from django.urls import reverse

from apps.cart.cart import Cart  # type: ignore[import-not-found]
from apps.orders.models import Order, OrderItem  # type: ignore[import-not-found]
from apps.products.models import Product  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


def send_confirmation_email(order: Order) -> None:
    subject = f"Order #{order.id} placed successfully! | Hop & Barley"

    items_text = ""
    for item in order.items.select_related("product").all():
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


def schedule_confirmation_email(order: Order) -> None:
    """Schedule confirmation email after the surrounding transaction commits."""
    def _send_email() -> None:
        try:
            send_confirmation_email(order)
        except Exception as e:
            logger.error("Error sending confirmation email for order #%s: %s", order.id, e)

    transaction.on_commit(_send_email)


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


def create_stripe_checkout_session(order: Order, request: HttpRequest) -> Any:
    """Create a Stripe Checkout session for a pending card order and store its ID."""
    if order.payment_method != Order.PaymentMethod.CARD:
        raise ValueError("Stripe Checkout is only supported for card orders.")
    if order.status != Order.Status.pending:
        raise ValueError("Checkout session can only be created for pending orders.")
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("STRIPE_SECRET_KEY is not configured.")

    line_items = [
        {
            "price_data": {
                "currency": "usd",
                "unit_amount": int((Decimal(item.price) * 100).quantize(Decimal("1"))),
                "product_data": {
                    "name": item.product.name,
                },
            },
            "quantity": item.quantity,
        }
        for item in order.items.select_related("product").all()
    ]
    if not line_items:
        raise ValueError("Cannot create a Stripe checkout session for an empty order.")

    success_url = (
        request.build_absolute_uri(reverse("orders:success", args=[order.id]))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = request.build_absolute_uri(reverse("orders:payment_cancel", args=[order.id]))

    session = stripe.checkout.Session.create(
        api_key=settings.STRIPE_SECRET_KEY,
        mode="payment",
        line_items=line_items,  # type: ignore[arg-type]
        customer_email=order.email,
        client_reference_id=str(order.id),
        metadata={"order_id": str(order.id)},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    if not getattr(session, "url", None):
        raise ValueError("Stripe checkout session did not return a redirect URL.")

    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id", "updated_at"])
    return session


def mark_order_as_paid(order_id: int) -> bool:
    """Idempotently transition a pending order to PAID and schedule confirmation email."""
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(pk=order_id).first()
        if not order or order.status != Order.Status.pending:
            return False

        order.status = Order.Status.paid
        order.save(update_fields=["status", "updated_at"])
        schedule_confirmation_email(order)
        return True


def _extract_stripe_order_id(session: Any) -> str | None:
    """Extract order ID from Stripe session's client_reference_id or metadata."""
    client_ref = getattr(session, "client_reference_id", None)
    if client_ref:
        return str(client_ref)
    metadata = getattr(session, "metadata", None)
    order_id = metadata.get("order_id") if isinstance(metadata, dict) else getattr(metadata, "order_id", None)
    return str(order_id) if order_id is not None else None


def verify_stripe_checkout_session(order: Order, session_id: str) -> bool:
    """Retrieve a Stripe session and mark the order as paid if verified."""
    if not settings.STRIPE_SECRET_KEY or not session_id:
        return False
    if order.stripe_session_id and session_id != order.stripe_session_id:
        return False

    session = stripe.checkout.Session.retrieve(
        session_id,
        api_key=settings.STRIPE_SECRET_KEY,
    )

    session_order_id = _extract_stripe_order_id(session)
    if session_order_id and session_order_id != str(order.id):
        return False

    expected_amount_cents = int((Decimal(order.total_price) * 100).quantize(Decimal("1")))
    amount_total = getattr(session, "amount_total", None)
    currency = getattr(session, "currency", None)
    if amount_total is not None and amount_total != expected_amount_cents:
        return False
    if currency is not None and str(currency).lower() != "usd":
        return False

    if getattr(session, "payment_status", None) == "paid":
        return mark_order_as_paid(order.id)

    return False


def cancel_order(order_id: int, expire_stripe_session: bool = False) -> bool:
    """Cancel a pending order, restore reserved stock, and optionally expire its Stripe session."""
    stripe_session_id: str | None = None
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(pk=order_id).first()
        if not order or order.status != Order.Status.pending:
            return False

        qty_by_product: dict[int, int] = defaultdict(int)
        for product_id, quantity in order.items.values_list("product_id", "quantity"):
            qty_by_product[product_id] += quantity

        if qty_by_product:
            Product.objects.filter(pk__in=qty_by_product).update(
                stock=Case(
                    *(
                        When(pk=product_id, then=F("stock") + quantity)
                        for product_id, quantity in qty_by_product.items()
                    ),
                    default=F("stock"),
                    output_field=PositiveIntegerField(),
                )
            )

        order.status = Order.Status.cancelled
        order.save(update_fields=["status", "updated_at"])
        stripe_session_id = order.stripe_session_id

    if expire_stripe_session and stripe_session_id and settings.STRIPE_SECRET_KEY:
        try:
            stripe.checkout.Session.expire(
                stripe_session_id,
                api_key=settings.STRIPE_SECRET_KEY,
            )
        except stripe.StripeError as e:
            logger.warning("Could not expire Stripe session %s for order #%s: %s", stripe_session_id, order_id, e)

    return True


def _resolve_order_from_stripe_session(session_data: Any) -> Order | None:
    session_id = getattr(session_data, "id", None)
    raw_order_id = _extract_stripe_order_id(session_data)

    if raw_order_id is not None:
        try:
            order = Order.objects.filter(pk=int(raw_order_id)).first()
            if order:
                return order
        except (TypeError, ValueError):
            pass

    if session_id:
        return Order.objects.filter(stripe_session_id=session_id).first()
    return None


def handle_stripe_webhook_event(event: Any) -> None:
    """Handle supported Stripe webhook events."""
    event_type = getattr(event, "type", None)
    data = getattr(event, "data", None)
    session_data = getattr(data, "object", None)
    if not session_data:
        return

    if event_type == "checkout.session.completed":
        if getattr(session_data, "payment_status", None) != "paid":
            return
        order = _resolve_order_from_stripe_session(session_data)
        if order:
            mark_order_as_paid(order.id)
    elif event_type == "checkout.session.expired":
        order = _resolve_order_from_stripe_session(session_data)
        if order:
            cancel_order(order.id)
