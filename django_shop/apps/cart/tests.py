from decimal import Decimal

import pytest
from django.http import HttpRequest
from .cart import Cart
from apps.products.models import Product

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
class TestCartView:
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
