import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from apps.products.models import Product, Category, Review # noqa
from apps.orders.models import Order, OrderItem # noqa
from django.urls import reverse
from django.utils import timezone

User = get_user_model()

@pytest.fixture()
def user():
    return User.objects.create(email='user@a.com', password='password122')

@pytest.fixture()
def category():
    return Category.objects.create(name='test_category')

@pytest.fixture()
def product1(category):
    product = Product.objects.create(name='product name', description='product description', price=1.3)
    product.categories.add(category)
    return product

@pytest.fixture()
def product2():
    return Product.objects.create(name='Grass', description='Grass', price=10.0)

@pytest.fixture()
def product3():
    return Product.objects.create(name='Example', description='Example', price=50.0)

@pytest.mark.django_db
class TestProductViews:
    def test_product_view(self, client, product1):
        url = reverse('products:product_list')
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert product1.name in content
        assert product1.description in content

    def test_product_search(self, client, product1, product2):
        url = reverse('products:product_list')
        filter_data = {
            'q': product2.name,
        }
        response = client.get(url, data=filter_data)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert product1.name not in content
        assert product2.name in content

    def test_product_by_category(self, client, product1, product2, product3, category):
        url = reverse('products:product_list')
        filter_data = {
            'category': category.name,
        }
        response = client.get(url, data=filter_data)
        assert response.status_code == 200

        content = response.content.decode('utf-8')
        assert product1.name in content
        assert product2.name not in content
        assert product3.name not in content

    def test_product_price_filter(self, client, product1, product2, product3):
        url = reverse('products:product_list')
        filter_data = {
            'price_lte': '20',
            'price_gte': '5',
        }
        response = client.get(url, data=filter_data)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert product1.name not in content
        assert product2.name in content
        assert product3.name not in content

    def test_product_sort(self, client, product1, product2, product3):
        url = reverse('products:product_list')
        filter_data = {
            'sort': 'price_asc'
        }
        response = client.get(url, data=filter_data)
        assert response.status_code == 200

        content = response.content.decode('utf-8')

        product1_position = content.find(product1.name)
        assert product1_position != -1
        product2_position = content.find(product2.name)
        assert product2_position != -1
        product3_position = content.find(product3.name)
        assert product3_position != -1

        # product1 (price 1.3) < product2 (price 10.0) < product3 (price 50.0)
        assert product1_position < product2_position < product3_position

    def test_product_sort_by_popularity(self, client, user, product1, product2, product3):
        product1.stock = 10
        product1.save()
        product2.stock = 10
        product2.save()
        product3.stock = 10
        product3.save()

        order = Order.objects.create(
            user=user,
            first_name="First",
            middle_name="Middle",
            last_name="Last",
            email="test@example.com",
            phone="123456789",
            address="Test Address",
        )
        OrderItem.objects.create(order=order, product=product3, price=product3.price, quantity=5)
        OrderItem.objects.create(order=order, product=product1, price=product1.price, quantity=3)

        url = reverse('products:product_list')
        filter_data = {
            'sort': 'popularity'
        }
        response = client.get(url, data=filter_data)
        assert response.status_code == 200

        content = response.content.decode('utf-8')

        product3_position = content.find(product3.name)
        assert product3_position != -1
        product1_position = content.find(product1.name)
        assert product1_position != -1
        product2_position = content.find(product2.name)
        assert product2_position != -1

        # product3 (5 sales) < product1 (3 sales) < product2 (0 sales)
        assert product3_position < product1_position < product2_position

        assert product1.stock == 7
        assert product2.stock == 10
        assert product3.stock == 5

    def test_product_sort_by_created_date(self, client, user, product1, product2, product3):
        product1.created_at = timezone.now()
        product2.created_at = timezone.now()
        product3.created_at = timezone.now()
        url = reverse('products:product_list')
        response = client.get(url)
        assert response.status_code == 200

        content = response.content.decode('utf-8')

        product1_position = content.find(product1.name)
        assert product1_position != -1
        product2_position = content.find(product2.name)
        assert product2_position != -1
        product3_position = content.find(product3.name)
        assert product3_position != -1
        # product 3 created last it will be first after ordering
        assert product3_position < product2_position < product1_position

    def test_product_detail_view_success(self, client, user, product1):
        Review.objects.create(product=product1, user=user, rating=4, comment="Good product")
        Review.objects.create(product=product1, user=user, rating=5, comment="Great product")

        url = reverse('products:product_detail', kwargs={'slug': product1.slug})
        response = client.get(url)
        assert response.status_code == 200

        content = response.content.decode('utf-8')
        assert product1.name in content
        assert product1.description in content
        assert f"${product1.price}" in content
        assert "4.5" in content
        assert "Good product" in content
        assert "Great product" in content

    def test_product_detail_view_inactive_returns_404(self, client, product1):
        product1.is_active = False
        product1.save()

        url = reverse('products:product_detail', kwargs={'slug': product1.slug})
        response = client.get(url)
        assert response.status_code == 404

    def test_product_detail_view_nonexistent_returns_404(self, client):
        url = reverse('products:product_detail', kwargs={'slug': 'non-existent-product-slug-12345'})
        response = client.get(url)
        assert response.status_code == 404




     