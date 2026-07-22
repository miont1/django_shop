import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem

from ..models import Product, Review

User = get_user_model()


@pytest.fixture()
def client():
    return APIClient()


@pytest.fixture()
def product():
    return Product.objects.create(name='product name', description='product description', price=1.3, stock=10)


@pytest.fixture()
def user():
    return User.objects.create_user(email='buyer@example.com', password='Password123!')


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


@pytest.mark.django_db
class TestReviewAPI:
    def test_list_reviews(self, client, product, user):
        Review.objects.create(product=product, user=user, rating=5, comment='Awesome beer!')
        url = reverse('product_reviews_api-list', kwargs={'product_pk': product.id})
        
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        results = data['results'] if 'results' in data else data
        assert len(results) == 1
        assert results[0]['rating'] == 5
        assert results[0]['comment'] == 'Awesome beer!'

    def test_create_review_unauthenticated(self, client, product):
        url = reverse('product_reviews_api-list', kwargs={'product_pk': product.id})
        payload = {'product': product.id, 'rating': 5, 'comment': 'Great!'}
        
        response = client.post(url, payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_review_ineligible_not_purchased(self, client, product, user):
        client.force_authenticate(user=user)
        url = reverse('product_reviews_api-list', kwargs={'product_pk': product.id})
        payload = {'product': product.id, 'rating': 5, 'comment': 'I did not buy this'}

        response = client.post(url, payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "You cannot leave a review" in response.data['detail']

    def test_create_review_eligible_success(self, client, product, user):
        # Create a paid order for user with this product
        order = Order.objects.create(
            user=user,
            status=Order.Status.paid,
            first_name='John',
            middle_name='M',
            last_name='Doe',
            email=user.email,
            phone='123456789',
            address='Street 1'
        )
        OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)

        client.force_authenticate(user=user)
        url = reverse('product_reviews_api-list', kwargs={'product_pk': product.id})
        payload = {'product': product.id, 'rating': 5, 'comment': 'Really great product!'}

        response = client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['rating'] == 5
        assert response.data['comment'] == 'Really great product!'
        assert Review.objects.filter(product=product, user=user).exists()

    def test_create_review_already_reviewed(self, client, product, user):
        # Create a paid order and an existing review
        order = Order.objects.create(
            user=user,
            status=Order.Status.paid,
            first_name='John',
            middle_name='M',
            last_name='Doe',
            email=user.email,
            phone='123456789',
            address='Street 1'
        )
        OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
        Review.objects.create(product=product, user=user, rating=4, comment='First review')

        client.force_authenticate(user=user)
        url = reverse('product_reviews_api-list', kwargs={'product_pk': product.id})
        payload = {'product': product.id, 'rating': 5, 'comment': 'Second review attempt'}

        response = client.post(url, payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "You cannot leave a review" in response.data['detail']
