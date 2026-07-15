from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.conf import settings
from apps.cart.cart import Cart
from apps.products.models import Product
from apps.orders.models import Order, OrderItem

User = get_user_model()

@pytest.fixture()
def user():
    return User.objects.create_user(email="email@email.com", password="testpass122")

@pytest.fixture()
def product():
    return Product.objects.create(name="product", slug="product", price=100, stock=5)

@pytest.mark.django_db(transaction=True)
class TestOrderViews:
    def test_order_create_view_get_empty_cart(self, client):
        url = reverse('orders:order_create')
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse('products:product_list')

    def test_order_create_view_get_with_items(self, client, product):
        # Add item to cart first
        cart_add_url = reverse('cart:cart_add', args=[product.id])
        client.post(cart_add_url, {'quantity': 1})

        url = reverse('orders:order_create')
        response = client.get(url)
        assert response.status_code == 200
        assert 'orders/order_create.html' in [t.name for t in response.templates]

    def test_order_create_view_post(self, client, user, product):
        # Log in the user
        client.force_login(user)

        # Add item to cart
        cart_add_url = reverse('cart:cart_add', args=[product.id])
        client.post(cart_add_url, {'quantity': 2})

        # Check cart has items
        session = client.session
        assert 'cart' in session
        assert str(product.id) in session['cart']

        # Post order data
        order_create_url = reverse('orders:order_create')
        post_data = {
            'first_name': 'John',
            'middle_name': 'Doe',
            'last_name': 'Smith',
            'email': 'john@example.com',
            'phone': '+380991234567',
            'address': 'Kyiv, Main St 1',
        }
        response = client.post(order_create_url, post_data)
        
        # Verify redirect to success page
        order = Order.objects.latest('id')
        assert response.status_code == 302
        assert response.url == reverse('orders:success', args=[order.id])

        # Verify order attributes
        assert order.user == user
        assert order.first_name == 'John'
        assert order.phone == '+380991234567'
        assert order.total_price == Decimal('200.00')

        # Verify order items
        order_item = order.items.first()
        assert order_item.product == product
        assert order_item.quantity == 2
        assert order_item.price == Decimal('100.00')

        # Verify cart is empty
        new_session = client.session
        assert 'cart' not in new_session or not new_session['cart']

        # Verify email was sent to customer and admin
        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert sent_email.subject == f"Order #{order.id} placed successfully! | Hop & Barley"
        assert sent_email.to == [order.email, settings.ADMIN_EMAIL]
        assert 'John' in sent_email.body
        assert 'product' in sent_email.body
        assert '200.00' in sent_email.body

    def test_order_success_view(self, client, user):
        order = Order.objects.create(
            user=user,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email=user.email,
            phone='+380991234567',
            address='Kyiv, Main St 1',
            total_price=Decimal('200.00')
        )
        client.force_login(user)
        url = reverse('orders:success', args=[order.id])
        response = client.get(url)
        assert response.status_code == 200
        assert 'orders/order_success.html' in [t.name for t in response.templates]
        content = response.content.decode('utf-8')
        assert 'John' in content
        assert str(order.id) in content

    def test_order_success_view_unauthorized_anonymous(self, client, user):
        order = Order.objects.create(
            user=user,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email=user.email,
            phone='+380991234567',
            address='Kyiv, Main St 1',
            total_price=Decimal('200.00')
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
            total_price=Decimal('200.00')
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
            total_price=Decimal('200.00')
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
            total_price=Decimal('200.00')
        )
        session = client.session
        session['placed_orders'] = [order.id]
        session.save()
        url = reverse('orders:success', args=[order.id])
        response = client.get(url)
        assert response.status_code == 200
