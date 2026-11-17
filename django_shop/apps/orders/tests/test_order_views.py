from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import stripe
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

User = get_user_model()


@pytest.fixture()
def user():
    return User.objects.create_user(email="email@email.com", password="testpass122")


@pytest.fixture()
def product():
    return Product.objects.create(name="product", slug="product", price=100, stock=5)


def _create_order_with_item(user, product, **order_kwargs):
    defaults = {
        'user': user,
        'first_name': 'John',
        'middle_name': 'Doe',
        'last_name': 'Smith',
        'email': user.email,
        'phone': '+380991234567',
        'address': 'Kyiv, Main St 1',
        'payment_method': Order.PaymentMethod.CARD,
        'total_price': Decimal('200.00'),
    }
    defaults.update(order_kwargs)
    order = Order.objects.create(**defaults)
    OrderItem.objects.create(order=order, product=product, quantity=2, price=product.price)
    return order


@pytest.mark.django_db(transaction=True)
class TestOrderViews:
    def test_order_create_view_get_empty_cart(self, client):
        url = reverse('orders:order_create')
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse('products:product_list')

    def test_order_create_view_get_with_items(self, client, product):
        cart_add_url = reverse('cart:cart_add', args=[product.id])
        client.post(cart_add_url, {'quantity': 1})

        url = reverse('orders:order_create')
        response = client.get(url)
        assert response.status_code == 200
        assert 'orders/order_create.html' in [t.name for t in response.templates]

    def test_order_create_view_get_authenticated_prefilled(self, client, user, product):
        user.first_name = "Taras"
        user.last_name = "Shevchenko"
        user.middle_name = "Hryhorovych"
        user.phone = "+380501234567"
        user.city = "Kaniv"
        user.address = "Chernecha Hora 1"
        user.save()

        client.force_login(user)
        cart_add_url = reverse('cart:cart_add', args=[product.id])
        client.post(cart_add_url, {'quantity': 1})

        url = reverse('orders:order_create')
        response = client.get(url)
        assert response.status_code == 200
        form = response.context['form']
        assert form.initial['first_name'] == "Taras"
        assert form.initial['last_name'] == "Shevchenko"
        assert form.initial['middle_name'] == "Hryhorovych"
        assert form.initial['email'] == user.email
        assert form.initial['phone'] == "+380501234567"
        assert form.initial['address'] == "Kaniv, Chernecha Hora 1"

    def test_order_create_view_post_cash(self, client, user, product):
        client.force_login(user)

        cart_add_url = reverse('cart:cart_add', args=[product.id])
        client.post(cart_add_url, {'quantity': 2})

        session = client.session
        assert 'cart' in session
        assert str(product.id) in session['cart']

        order_create_url = reverse('orders:order_create')
        post_data = {
            'first_name': 'John',
            'middle_name': 'Doe',
            'last_name': 'Smith',
            'email': 'john@example.com',
            'phone': '+380991234567',
            'address': 'Kyiv, Main St 1',
            'payment_method': Order.PaymentMethod.CASH,
        }
        response = client.post(order_create_url, post_data)

        order = Order.objects.latest('id')
        assert response.status_code == 302
        assert response.url == reverse('orders:success', args=[order.id])

        assert order.user == user
        assert order.payment_method == Order.PaymentMethod.CASH
        assert order.first_name == 'John'
        assert order.phone == '+380991234567'
        assert order.total_price == Decimal('200.00')

        order_item = order.items.first()
        assert order_item.product == product
        assert order_item.quantity == 2
        assert order_item.price == Decimal('100.00')

        new_session = client.session
        assert 'cart' not in new_session or not new_session['cart']

        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert sent_email.subject == f"Order #{order.id} placed successfully! | Hop & Barley"
        assert sent_email.to == [order.email, settings.ADMIN_EMAIL]
        assert 'John' in sent_email.body
        assert 'product' in sent_email.body
        assert '200.00' in sent_email.body

    @patch('apps.orders.services.stripe.checkout.Session.create')
    def test_order_create_view_post_card_redirects_to_stripe(self, mock_session_create, client, user, product, settings):
        settings.STRIPE_SECRET_KEY = 'sk_test_mock'
        mock_session_create.return_value = SimpleNamespace(
            id='cs_test_123',
            url='https://checkout.stripe.com/c/pay/cs_test_123',
        )

        client.force_login(user)
        client.post(reverse('cart:cart_add', args=[product.id]), {'quantity': 2})

        post_data = {
            'first_name': 'John',
            'middle_name': 'Doe',
            'last_name': 'Smith',
            'email': 'john@example.com',
            'phone': '+380991234567',
            'address': 'Kyiv, Main St 1',
            'payment_method': Order.PaymentMethod.CARD,
        }
        response = client.post(reverse('orders:order_create'), post_data)

        order = Order.objects.latest('id')
        assert response.status_code == 302
        assert response.url == 'https://checkout.stripe.com/c/pay/cs_test_123'
        assert order.payment_method == Order.PaymentMethod.CARD
        assert order.status == Order.Status.pending
        assert order.stripe_session_id == 'cs_test_123'

        # Email is deferred until Stripe payment is confirmed
        assert len(mail.outbox) == 0

        mock_session_create.assert_called_once()
        call_kwargs = mock_session_create.call_args.kwargs
        assert call_kwargs['api_key'] == 'sk_test_mock'
        assert call_kwargs['client_reference_id'] == str(order.id)
        assert call_kwargs['metadata'] == {'order_id': str(order.id)}
        assert call_kwargs['line_items'][0]['price_data']['currency'] == 'usd'
        assert call_kwargs['line_items'][0]['price_data']['unit_amount'] == 10000
        assert call_kwargs['line_items'][0]['quantity'] == 2
        assert call_kwargs['success_url'].endswith(
            f"{reverse('orders:success', args=[order.id])}?session_id={{CHECKOUT_SESSION_ID}}"
        )

    @patch('apps.orders.services.stripe.checkout.Session.create')
    def test_order_create_view_post_card_stripe_error_redirects_to_cancel(self, mock_session_create, client, user, product, settings):
        settings.STRIPE_SECRET_KEY = 'sk_test_mock'
        mock_session_create.side_effect = stripe.StripeError("Stripe unavailable")

        client.force_login(user)
        client.post(reverse('cart:cart_add', args=[product.id]), {'quantity': 1})

        post_data = {
            'first_name': 'John',
            'middle_name': 'Doe',
            'last_name': 'Smith',
            'email': 'john@example.com',
            'phone': '+380991234567',
            'address': 'Kyiv, Main St 1',
            'payment_method': Order.PaymentMethod.CARD,
        }
        response = client.post(reverse('orders:order_create'), post_data)

        order = Order.objects.latest('id')
        assert response.status_code == 302
        assert response.url == reverse('orders:payment_cancel', args=[order.id])
        assert order.status == Order.Status.pending
        assert len(mail.outbox) == 0

    def test_order_success_view(self, client, user):
        order = Order.objects.create(
            user=user,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email=user.email,
            phone='+380991234567',
            address='Kyiv, Main St 1',
            total_price=Decimal('200.00'),
        )
        client.force_login(user)
        url = reverse('orders:success', args=[order.id])
        response = client.get(url)
        assert response.status_code == 200
        assert 'orders/order_success.html' in [t.name for t in response.templates]
        content = response.content.decode('utf-8')
        assert 'John' in content
        assert str(order.id) in content
        assert 'Awaiting Payment' in content

    @patch('apps.orders.services.stripe.checkout.Session.retrieve')
    def test_order_success_verifies_stripe_session_and_marks_paid(self, mock_retrieve, client, user, product, settings):
        settings.STRIPE_SECRET_KEY = 'sk_test_mock'
        order = _create_order_with_item(user, product, stripe_session_id='cs_test_paid')
        mock_retrieve.return_value = stripe.checkout.Session.construct_from(
            {
                'id': 'cs_test_paid',
                'payment_status': 'paid',
                'client_reference_id': str(order.id),
                'metadata': {'order_id': str(order.id)},
                'amount_total': 20000,
                'currency': 'usd',
            },
            'sk_test_mock',
        )

        client.force_login(user)
        url = f"{reverse('orders:success', args=[order.id])}?session_id=cs_test_paid"
        response = client.get(url)

        assert response.status_code == 200
        mock_retrieve.assert_called_once_with('cs_test_paid', api_key='sk_test_mock')
        order.refresh_from_db()
        assert order.status == Order.Status.paid
        assert len(mail.outbox) == 1
        assert 'Order Placed Successfully!' in response.content.decode('utf-8')

        # Re-visiting success URL is idempotent and does not duplicate confirmation email
        response_again = client.get(url)
        assert response_again.status_code == 200
        assert len(mail.outbox) == 1

    @patch('apps.orders.services.stripe.checkout.Session.retrieve')
    def test_order_success_rejects_mismatched_session_id(self, mock_retrieve, client, user, product, settings):
        settings.STRIPE_SECRET_KEY = 'sk_test_mock'
        order = _create_order_with_item(user, product, stripe_session_id='cs_test_expected')

        client.force_login(user)
        url = f"{reverse('orders:success', args=[order.id])}?session_id=cs_test_other"
        response = client.get(url)

        assert response.status_code == 200
        mock_retrieve.assert_not_called()
        order.refresh_from_db()
        assert order.status == Order.Status.pending
        assert len(mail.outbox) == 0

    def test_order_payment_cancel_and_retry(self, client, user, product, settings):
        settings.STRIPE_SECRET_KEY = 'sk_test_mock'
        order = _create_order_with_item(user, product, stripe_session_id='cs_old')
        client.force_login(user)

        cancel_response = client.get(reverse('orders:payment_cancel', args=[order.id]))
        assert cancel_response.status_code == 200
        assert 'orders/payment_cancel.html' in [t.name for t in cancel_response.templates]

        with patch('apps.orders.services.stripe.checkout.Session.create') as mock_create:
            mock_create.return_value = SimpleNamespace(
                id='cs_new',
                url='https://checkout.stripe.com/c/pay/cs_new',
            )
            retry_response = client.post(reverse('orders:payment_retry', args=[order.id]))

        assert retry_response.status_code == 302
        assert retry_response.url == 'https://checkout.stripe.com/c/pay/cs_new'
        order.refresh_from_db()
        assert order.stripe_session_id == 'cs_new'

    @patch('apps.orders.services.stripe.checkout.Session.expire')
    def test_order_cancel_post_restores_stock_and_expires_session(self, mock_expire, client, user, product, settings):
        settings.STRIPE_SECRET_KEY = 'sk_test_mock'
        second_product = Product.objects.create(name="malt", slug="malt", price=40, stock=8)
        order = _create_order_with_item(user, product, stripe_session_id='cs_cancel_me')
        OrderItem.objects.create(order=order, product=second_product, quantity=3, price=second_product.price)
        product.refresh_from_db()
        second_product.refresh_from_db()
        assert product.stock == 3
        assert second_product.stock == 5

        client.force_login(user)
        response = client.post(reverse('orders:order_cancel', args=[order.id]))

        assert response.status_code == 302
        assert response.url == reverse('orders:success', args=[order.id])
        mock_expire.assert_called_once_with('cs_cancel_me', api_key='sk_test_mock')
        order.refresh_from_db()
        product.refresh_from_db()
        second_product.refresh_from_db()
        assert order.status == Order.Status.cancelled
        assert product.stock == 5
        assert second_product.stock == 8

    @patch('apps.orders.services.stripe.checkout.Session.expire')
    def test_order_cancel_post_still_cancels_on_stripe_error(self, mock_expire, client, user, product, settings):
        settings.STRIPE_SECRET_KEY = 'sk_test_mock'
        mock_expire.side_effect = stripe.StripeError("Session already expired")
        order = _create_order_with_item(user, product, stripe_session_id='cs_already_exp')

        client.force_login(user)
        response = client.post(reverse('orders:order_cancel', args=[order.id]))

        assert response.status_code == 302
        order.refresh_from_db()
        product.refresh_from_db()
        assert order.status == Order.Status.cancelled
        assert product.stock == 5

    def test_order_cancel_ignores_paid_order(self, client, user, product):
        order = _create_order_with_item(user, product, status=Order.Status.paid)
        client.force_login(user)

        get_response = client.get(reverse('orders:order_cancel', args=[order.id]))
        assert get_response.status_code == 405

        post_response = client.post(reverse('orders:order_cancel', args=[order.id]))
        assert post_response.status_code == 302
        order.refresh_from_db()
        product.refresh_from_db()
        assert order.status == Order.Status.paid
        assert product.stock == 3

    @patch('apps.orders.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_checkout_completed_marks_paid(self, mock_construct, client, user, product, settings):
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        order = _create_order_with_item(user, product, stripe_session_id='cs_test_wh')
        mock_construct.return_value = stripe.Event.construct_from(
            {
                'id': 'evt_test_completed',
                'type': 'checkout.session.completed',
                'data': {
                    'object': {
                        'id': 'cs_test_wh',
                        'payment_status': 'paid',
                        'client_reference_id': str(order.id),
                        'metadata': {'order_id': str(order.id)},
                    }
                },
            },
            'sk_test_mock',
        )

        webhook_url = reverse('orders:stripe_webhook')
        response = client.post(
            webhook_url,
            data=b'{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig_header',
        )
        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == Order.Status.paid
        assert len(mail.outbox) == 1

        # Duplicate webhook event is safely ignored
        response_dup = client.post(
            webhook_url,
            data=b'{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig_header',
        )
        assert response_dup.status_code == 200
        assert len(mail.outbox) == 1

    @patch('apps.orders.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_checkout_expired_cancels_and_restores_stock(self, mock_construct, client, user, product, settings):
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        second_product = Product.objects.create(name="hops", slug="hops", price=50, stock=10)
        order = _create_order_with_item(user, product, stripe_session_id='cs_test_exp')
        OrderItem.objects.create(order=order, product=second_product, quantity=3, price=second_product.price)
        product.refresh_from_db()
        second_product.refresh_from_db()
        assert product.stock == 3
        assert second_product.stock == 7

        mock_construct.return_value = stripe.Event.construct_from(
            {
                'id': 'evt_test_expired',
                'type': 'checkout.session.expired',
                'data': {
                    'object': {
                        'id': 'cs_test_exp',
                        'client_reference_id': str(order.id),
                        'metadata': {'order_id': str(order.id)},
                    }
                },
            },
            'sk_test_mock',
        )

        response = client.post(
            reverse('orders:stripe_webhook'),
            data=b'{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig_header',
        )
        assert response.status_code == 200
        order.refresh_from_db()
        product.refresh_from_db()
        second_product.refresh_from_db()
        assert order.status == Order.Status.cancelled
        assert product.stock == 5
        assert second_product.stock == 10
        assert len(mail.outbox) == 0

    @patch('apps.orders.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_invalid_signature_returns_400(self, mock_construct, client, settings):
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        mock_construct.side_effect = stripe.SignatureVerificationError("Invalid signature", "sig")

        response = client.post(
            reverse('orders:stripe_webhook'),
            data=b'{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='bad_sig',
        )
        assert response.status_code == 400

    def test_stripe_webhook_missing_secret_returns_500(self, client, settings):
        settings.STRIPE_WEBHOOK_SECRET = ''
        response = client.post(
            reverse('orders:stripe_webhook'),
            data=b'{}',
            content_type='application/json',
        )
        assert response.status_code == 500

    def test_order_success_view_unauthorized_anonymous(self, client, user):
        order = Order.objects.create(
            user=user,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email=user.email,
            phone='+380991234567',
            address='Kyiv, Main St 1',
            total_price=Decimal('200.00'),
        )
        url = reverse('orders:success', args=[order.id])
        response = client.get(url)
        assert response.status_code == 403

    def test_order_success_view_different_user(self, client, user):
        other_user = User.objects.create_user(email="other@example.com", password="testpassword123")
        order = Order.objects.create(
            user=user,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email=user.email,
            phone='+380991234567',
            address='Kyiv, Main St 1',
            total_price=Decimal('200.00'),
        )
        client.force_login(other_user)
        url = reverse('orders:success', args=[order.id])
        response = client.get(url)
        assert response.status_code == 403

    def test_order_success_view_matching_email(self, client, user):
        order = Order.objects.create(
            user=None,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email=user.email,
            phone='+380991234567',
            address='Kyiv, Main St 1',
            total_price=Decimal('200.00'),
        )
        client.force_login(user)
        url = reverse('orders:success', args=[order.id])
        response = client.get(url)
        assert response.status_code == 200
        order.refresh_from_db()
        assert order.user == user

    def test_order_success_view_guest_session(self, client):
        order = Order.objects.create(
            user=None,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email='guest@example.com',
            phone='+380991234567',
            address='Kyiv, Main St 1',
            total_price=Decimal('200.00'),
        )
        session = client.session
        session['placed_orders'] = [order.id]
        session.save()
        url = reverse('orders:success', args=[order.id])
        response = client.get(url)
        assert response.status_code == 200
