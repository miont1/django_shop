import logging

import stripe
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.cart.cart import Cart  # type: ignore[import-not-found]

from .forms import OrderForm
from .models import Order
from .services import (
    cancel_order,
    create_stripe_checkout_session,
    handle_stripe_webhook_event,
    make_order,
    verify_stripe_checkout_session,
)

logger = logging.getLogger(__name__)


def _get_authorized_order(request: HttpRequest, order_id: int) -> Order:
    """Return an order if the current user or session is authorized to access it."""
    order = get_object_or_404(Order, id=order_id)
    can_view = False

    if request.user.is_authenticated:
        if order.user == request.user or order.email == request.user.email:
            can_view = True
            if order.user is None and order.email == request.user.email:
                order.user = request.user
                order.save(update_fields=['user'])

    session_orders = request.session.get('placed_orders', [])
    if order_id in session_orders:
        can_view = True

    if not can_view:
        raise PermissionDenied("You do not have permission to view this order.")

    return order


def order_create(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)

    if not cart:
        return redirect('products:product_list')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                order = make_order(user=request.user, order_data=form.cleaned_data, cart=cart)
            except ValueError as e:
                form.add_error(None, str(e))
            else:
                # Store in session so they can view the success/cancel/retry pages
                placed_orders = request.session.get('placed_orders', [])
                placed_orders.append(order.id)
                request.session['placed_orders'] = placed_orders

                if order.payment_method == Order.PaymentMethod.CARD:
                    try:
                        session = create_stripe_checkout_session(order, request)
                        return redirect(session.url)
                    except (stripe.StripeError, ValueError) as e:
                        logger.exception("Failed to create Stripe checkout session for order #%s: %s", order.id, e)
                        messages.error(request, "Could not start online payment. Please try paying again below.")
                        return redirect('orders:payment_cancel', order_id=order.id)

                return redirect('orders:success', order_id=order.id)
    else:
        initial = {}
        if request.user.is_authenticated:
            user = request.user
            address_val = user.address or ""
            if user.city and user.city.lower() not in address_val.lower():
                address_val = f"{user.city}, {address_val}".strip(", ")

            initial = {
                'first_name': user.first_name or "",
                'middle_name': user.middle_name or "",
                'last_name': user.last_name or "",
                'email': user.email or "",
                'phone': user.phone or "",
                'address': address_val,
            }
        form = OrderForm(initial=initial)

    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


def order_success(request: HttpRequest, order_id: int) -> HttpResponse:
    order = _get_authorized_order(request, order_id)

    if order.payment_method == Order.PaymentMethod.CARD and order.status == Order.Status.pending:
        session_id = request.GET.get('session_id') or order.stripe_session_id
        if session_id:
            try:
                if verify_stripe_checkout_session(order, session_id):
                    order.refresh_from_db()
            except stripe.StripeError as e:
                logger.warning("Failed to verify Stripe session %s for order #%s: %s", session_id, order.id, e)

    return render(request, 'orders/order_success.html', {'order': order})


def order_payment_cancel(request: HttpRequest, order_id: int) -> HttpResponse:
    order = _get_authorized_order(request, order_id)
    if order.status != Order.Status.pending:
        return redirect('orders:success', order_id=order.id)
    return render(request, 'orders/payment_cancel.html', {'order': order})


def order_payment_retry(request: HttpRequest, order_id: int) -> HttpResponse:
    order = _get_authorized_order(request, order_id)
    if order.payment_method != Order.PaymentMethod.CARD or order.status != Order.Status.pending:
        return redirect('orders:success', order_id=order.id)

    try:
        session = create_stripe_checkout_session(order, request)
        return redirect(session.url)
    except (stripe.StripeError, ValueError) as e:
        logger.exception("Failed to retry Stripe payment for order #%s: %s", order.id, e)
        messages.error(request, "Could not connect to payment provider. Please try again.")
        return redirect('orders:payment_cancel', order_id=order.id)


@require_POST
def order_cancel(request: HttpRequest, order_id: int) -> HttpResponse:
    order = _get_authorized_order(request, order_id)
    if cancel_order(order.id, expire_stripe_session=True):
        messages.success(request, f"Order #{order.id} has been cancelled.")
    else:
        messages.info(request, f"Order #{order.id} cannot be cancelled in its current status.")
    return redirect('orders:success', order_id=order.id)


@csrf_exempt
@require_POST
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET is not configured.")
        return HttpResponse(status=500)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.warning("Invalid Stripe webhook payload.")
        return HttpResponse(status=400)
    except stripe.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature.")
        return HttpResponse(status=400)

    handle_stripe_webhook_event(event)
    return HttpResponse(status=200)
