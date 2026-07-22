import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.templatetags.rest_framework import items
from rest_framework.test import APIClient

from apps.products.models import Product  # noqa

from ..cart import Cart


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
        assert items_[product.id]['quantity'] == 1
        assert items_[product2.id]['quantity'] == 2


    def test_partial_update_cart_item(self, client, product):
        url = reverse('cart_api-list')
        response1 = client.post(url, data={'product_id': product.id, 'quantity': 1})
        assert response1.status_code == status.HTTP_201_CREATED

        url = reverse('cart_api-detail', args=[product.id])
        response2 = client.patch(url, data={'product_id': product.id, 'quantity': 2,
                                            'override_quantity': False}, format='json')
        assert response2.status_code == status.HTTP_200_OK, response2.json()

        response2_data = response2.json()
        assert len(response2_data['items']) == 1
        assert response2_data['total_cart_price'] == '300.00'
        assert response2_data['items'][0]['quantity'] == 3

    def test_delete_item_from_cart(self, client, product, product2):
        url = reverse('cart_api-list')
        response1 = client.post(url, data={'product_id': product.id, 'quantity': 1})
        assert response1.status_code == status.HTTP_201_CREATED

        url2 = reverse('cart_api-list')
        response2 = client.post(url2, data={'product_id': product2.id, 'quantity': 2})
        assert response2.status_code == status.HTTP_201_CREATED

        url3 = reverse('cart_api-detail', args=[product.id])
        response3 = client.delete(url3)
        assert response3.status_code == status.HTTP_200_OK

        response3_data = response3.json()
        assert len(response3_data['items']) == 1
        assert response3_data['total_cart_price'] == '100.00'
        assert response3_data['items'][0]['quantity'] == 2
