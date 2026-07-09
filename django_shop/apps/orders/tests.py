from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.products.models import Product  # type: ignore[import-not-found]
from apps.orders.models import Order  # type: ignore[import-not-found]
from apps.orders.models import OrderItem # type: ignore[import-not-found]

User = get_user_model()

@pytest.fixture()
def user():
    return User.objects.create_user(email="email@email.com", password="testpass122")

@pytest.fixture()
def product():
    return Product.objects.create(name="product", slug="product", price=100, stock=2)

@pytest.mark.django_db
class TestOrder:
    def test_order_creation(self, user, product):
        order = Order.objects.create(user=user)
        order_item = OrderItem.objects.create(order=order, product=product, price=product.price, quantity=2)
        assert order.user.email == "email@email.com"
        assert order.status == Order.Status.pending
        assert order.items.filter(pk=order_item.id).exists()
        assert order_item.product.price == 100
        order.refresh_from_db()
        assert order.total_price == 200

    def test_product_update_price(self, user, product):
        order = Order.objects.create(user=user)
        order_item = OrderItem.objects.create(order=order, product=product, price=product.price, quantity=2)
        order.refresh_from_db()
        assert order.total_price == Decimal('200.0')
        product.price = Decimal('1000.0')
        product.save()

        order_item.refresh_from_db()
        order.refresh_from_db()

        assert order.total_price == Decimal('200.0')
        assert order_item.price == Decimal('100.0')

    def test_not_enough_stock(self, user, product):
        order = Order.objects.create(user=user)
        with pytest.raises(ValidationError):
            OrderItem.objects.create(order=order, product=product, price=product.price, quantity=3)

    def test_order_item_successful_stock_deduction(self, user, product):
        product.stock = 10
        product.save()

        order = Order.objects.create(user=user)

        order_item = OrderItem.objects.create(order=order, product=product, price=product.price, quantity=3)
        product.refresh_from_db()
        assert product.stock == 7

        order_item.quantity = 5
        order_item.save()

        product.refresh_from_db()
        assert product.stock == 5

        order_item.quantity = 4
        order_item.save()

        product.refresh_from_db()
        assert product.stock == 6

    def test_delete_order_item(self, user, product):
        order = Order.objects.create(user=user)
        order_item = OrderItem.objects.create(order=order, product=product, price=product.price, quantity=1)
        order.refresh_from_db()
        assert order.total_price == Decimal('100.0')
        product.refresh_from_db()
        assert product.stock == 1

        # stock increased and price decreased
        order_item.delete()
        product.refresh_from_db()
        assert product.stock == 2
        order.refresh_from_db()
        assert order.total_price == Decimal('0.0')

    def test_order_item_updated_not_enough_stock(self, user, product):
        order = Order.objects.create(user=user)
        order_item = OrderItem.objects.create(order=order, product=product, price=product.price, quantity=1)
        product.refresh_from_db()
        assert product.stock == 1
        order_item.quantity = 5

        #not enough stock on product
        with pytest.raises(ValidationError):
            order_item.save()


