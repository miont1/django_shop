from decimal import Decimal
import json

import pytest
from django.http import HttpRequest
from django.urls import reverse
from .cart import Cart
from apps.products.models import Product # noqa

from .cart_exeptions import NotEnoughProductInStock

@pytest.fixture()
def request_with_session(client) -> HttpRequest:
    """Fixture using Django's test client session."""
    request = HttpRequest()
    request.session = client.session
    return request

@pytest.fixture()
def product() -> Product:
    """Fixture of product1."""
    return Product.objects.create(name="product", slug="product", price=100, stock=3)

@pytest.fixture()
def product2() -> Product:
    """Fixture of product2."""
    return Product.objects.create(name="product2", slug="product2", price=50, stock=6)

@pytest.mark.django_db
class TestCartSession:

    def test_default_cart(self, request_with_session):
        cart = Cart(request_with_session)
        assert len(cart) == 0
        assert cart.get_total_price() == Decimal(0.0)

    def test_add_to_cart(self, request_with_session, product):
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        assert len(cart) == 2
        assert cart.cart[str(product.id)]['quantity'] == 2
        assert cart.cart[str(product.id)]['price'] == '100'
        assert cart.get_total_price() == Decimal(200.0)

    def test_iterate_cart(self, request_with_session, product, product2):
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        cart.add(product2, quantity=3)
        cart_copy = []
        for item in cart:
            assert item['has_enough_stock'] is True
            cart_copy.append(item)
        assert len(cart_copy) == 2

        item1 = next(i for i in cart_copy if i['product'] == product)
        item2 = next(i for i in cart_copy if i['product'] == product2)

        assert item1['price'] == Decimal('100.0')
        assert item1['total_price'] == Decimal('200.0')

        assert item2['price'] == Decimal('50.0')
        assert item2['total_price'] == Decimal('150.0')

    def test_no_enough_stock(self, request_with_session, product):
        cart = Cart(request_with_session)
        with pytest.raises(NotEnoughProductInStock):
            cart.add(product, quantity=4)

    def test_clear_cart(self, request_with_session, product):
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        cart.clear()
        assert len(cart) == 0
        assert cart.get_total_price() == Decimal(0.0)

    def test_remove_from_cart(self, request_with_session, product):
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        assert cart.get_total_price() == Decimal(200.0)
        cart.remove(product)
        assert cart.get_total_price() == Decimal(0.0)
        assert len(cart) == 0


@pytest.mark.django_db
class TestCartViews:
    def test_cart_detail_empty(self, client):
        url = reverse('cart:cart_detail')
        response = client.get(url)
        assert response.status_code == 200
        assert "Your cart is empty" in response.content.decode('utf-8')

    def test_cart_add_view(self, client, product):
        url = reverse('cart:cart_add', args=[product.id])
        response = client.post(url, {'quantity': 2, 'override': 'False'})
        assert response.status_code == 302 # Redirect to cart_detail
        
        detail_url = reverse('cart:cart_detail')
        detail_response = client.get(detail_url)
        assert detail_response.status_code == 200
        content = detail_response.content.decode('utf-8')
        assert product.name in content
        assert "$200.00" in content

    def test_cart_remove_view(self, client, product):
        client.post(reverse('cart:cart_add', args=[product.id]), {'quantity': 2})
        
        url = reverse('cart:cart_remove', args=[product.id])
        response = client.post(url)
        assert response.status_code == 302 # Redirect to cart_detail
        
        detail_response = client.get(reverse('cart:cart_detail'))
        assert "Your cart is empty" in detail_response.content.decode('utf-8')

    def test_cart_add_ajax_view(self, client, product):
        url = reverse('cart:cart_add_ajax', args=[product.id])
        response = client.post(
            url, 
            data=json.dumps({'quantity': 2, 'override': True}), 
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['total_price'] == 200.0
        assert data['total_items'] == 2

    def test_cart_add_ajax_out_of_stock(self, client, product):
        url = reverse('cart:cart_add_ajax', args=[product.id])
        response = client.post(
            url, 
            data=json.dumps({'quantity': 10, 'override': True}), 
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert "Not enough stock" in data['error']

    def test_cart_remove_ajax_view(self, client, product):
        client.post(
            reverse('cart:cart_add_ajax', args=[product.id]), 
            data=json.dumps({'quantity': 1, 'override': True}), 
            content_type='application/json'
        )
        url = reverse('cart:cart_remove_ajax', args=[product.id])
        response = client.post(url)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['total_price'] == 0.0
        assert data['total_items'] == 0

