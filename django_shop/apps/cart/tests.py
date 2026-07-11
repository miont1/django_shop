from decimal import Decimal

import pytest
from django.http import HttpRequest
from .cart import Cart
from apps.products.models import Product


@pytest.fixture()
def request_with_session(client) -> HttpRequest:
    """Fixture using Django's test client session."""
    request = HttpRequest()
    request.session = client.session
    return request

@pytest.fixture()
def product(request) -> Product:
    """Fixture using Django's test client session."""
    return Product.objects.create(name="product", slug="product", price=100, stock=3)


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
        assert cart.get_total_price() == Decimal(200.0)
