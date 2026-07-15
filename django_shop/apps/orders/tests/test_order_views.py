from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
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

@pytest.mark.django_db
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

    def test_order_success_view(self, client, user):
        order = Order.objects.create(
            user=user,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email='john@example.com',
            phone='+380991234567',
            address='Kyiv, Main St 1',
            total_price=Decimal('200.00')
        )
        url = reverse('orders:success', args=[order.id])
        response = client.get(url)
        assert response.status_code == 200
        assert 'orders/order_success.html' in [t.name for t in response.templates]
        content = response.content.decode('utf-8')
        assert 'John' in content
        assert str(order.id) in content
