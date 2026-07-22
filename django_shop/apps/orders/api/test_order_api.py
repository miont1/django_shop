from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem
from apps.products.models import Product

User = get_user_model()


@pytest.fixture()
def client():
    return APIClient()


@pytest.fixture()
def user():
    return User.objects.create_user(email='orderapi@example.com', password='Password123!')


@pytest.fixture()
def product():
    return Product.objects.create(name='Cascade Hops', price=Decimal('25.00'), stock=15)


@pytest.mark.django_db
class TestOrderAPI:
    def test_create_order_empty_cart_fails(self, client, user):
        client.force_authenticate(user=user)
        url = reverse('order_api-list')
        payload = {
            'first_name': 'John',
            'middle_name': 'Doe',
            'last_name': 'Smith',
            'email': 'orderapi@example.com',
            'phone': '+380991234567',
            'address': 'Kyiv, Main St 1'
        }
        response = client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data or 'non_field_errors' in response.data

    def test_create_order_invalid_phone_fails(self, client, user, product):
        client.force_authenticate(user=user)
        cart_url = reverse('cart_api-list')
        client.post(cart_url, {'product_id': product.id, 'quantity': 1})

        url = reverse('order_api-list')
        payload = {
            'first_name': 'John',
            'middle_name': 'Doe',
            'last_name': 'Smith',
            'email': 'orderapi@example.com',
            'phone': '12345',  # Invalid phone format
            'address': 'Kyiv, Main St 1'
        }
        response = client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'phone' in response.data

    def test_create_order_success(self, client, user, product):
        client.force_authenticate(user=user)
        cart_url = reverse('cart_api-list')
        client.post(cart_url, {'product_id': product.id, 'quantity': 2})

        url = reverse('order_api-list')
        payload = {
            'first_name': 'John',
            'middle_name': 'Doe',
            'last_name': 'Smith',
            'email': 'orderapi@example.com',
            'phone': '+380991234567',
            'address': 'Kyiv, Main St 1'
        }
        response = client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['total_price'] == '50.00'
        assert Order.objects.filter(user=user, email='orderapi@example.com').exists()

    def test_create_order_anonymous_guest_checkout(self, client, product):
        cart_url = reverse('cart_api-list')
        client.post(cart_url, {'product_id': product.id, 'quantity': 1})

        url = reverse('order_api-list')
        payload = {
            'first_name': 'Guest',
            'middle_name': 'User',
            'last_name': 'Buyer',
            'email': 'guest@example.com',
            'phone': '+380991112233',
            'address': 'Lviv, Main St 10'
        }
        response = client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['total_price'] == '25.00'
        
        order = Order.objects.get(email='guest@example.com')
        assert order.user is None
        assert order.first_name == 'Guest'

    def test_list_user_orders(self, client, user):
        Order.objects.create(
            user=user,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email=user.email,
            phone='+380991234567',
            address='Kyiv',
            total_price=Decimal('50.00')
        )
        client.force_authenticate(user=user)
        url = reverse('order_api-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        results = data['results'] if 'results' in data else data
        assert len(results) == 1
        assert results[0]['first_name'] == 'John'

    def test_retrieve_order_detail(self, client, user):
        order = Order.objects.create(
            user=user,
            first_name='John',
            middle_name='Doe',
            last_name='Smith',
            email=user.email,
            phone='+380991234567',
            address='Kyiv',
            total_price=Decimal('50.00')
        )
        client.force_authenticate(user=user)
        url = reverse('order_api-detail', kwargs={'pk': order.id})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == order.id
        assert data['email'] == user.email
