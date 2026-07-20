import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.templatetags.rest_framework import items
from rest_framework.test import APIClient

from ..cart import Cart
from apps.products.models import Product # noqa

@pytest.fixture()
def client():
    return APIClient()

@pytest.fixture()
def product() -> Product:
    """Fixture of product1."""
    return Product.objects.create(name="product", slug="product", price=100, stock=3)

@pytest.fixture()
def product2() -> Product:
    """Fixture of product2."""
    return Product.objects.create(name="product2", slug="product2", price=50, stock=6)

@pytest.mark.django_db
class TestCartAPI:
    def test_can_view_empty_cart(self, client, product):
        url = reverse('cart_api-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['items']) == 0
        assert data['total_cart_price'] == '0.00'

    def test_post_item_to_cart(self, client, product, product2):
        url = reverse('cart_api-list')
        response1 = client.post(url, data={'product_id': product.id, 'quantity': 1})
        assert response1.status_code == status.HTTP_201_CREATED

        response2 = client.post(url, data={'product_id': product2.id, 'quantity': 2})
        assert response2.status_code == status.HTTP_201_CREATED

        response2_data = response2.json()
        assert len(response2_data['items']) == 2
        assert response2_data['total_cart_price'] == '200.00'

        items_ = {item['product_id']: item for item in response2_data['items']}
        print(items_)
        assert items_[1]['quantity'] == 1
        assert items_[2]['quantity'] == 2
