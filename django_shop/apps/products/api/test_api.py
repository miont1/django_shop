import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ..models import Product

@pytest.fixture()
def client():
    return APIClient()

@pytest.fixture()
def product():
    return Product.objects.create(name='product name', description='product description', price=1.3)

@pytest.mark.django_db
class TestProductAPI:
    def test_list(self, client, product):
        url = reverse('product_api-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == product.name

    def test_retrieve(self, client, product):
        url = reverse('product_api-detail', args=[product.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == product.name
        assert data["description"] == product.description
        assert data["price"] == "1.30"
        assert data["stock"] == 0
