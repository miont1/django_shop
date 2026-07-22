import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse

from apps.products.models import Category, Product, Review  # noqa

User = get_user_model()

@pytest.fixture()
def user():
    return User.objects.create(email='user@a.com', password='password122')

@pytest.fixture()
def product():
    return Product.objects.create(name='product name', description='product description', price=1.3)

@pytest.fixture()
def category():
    return Category.objects.create(name='category name')

@pytest.mark.django_db
class TestProduct:
    def test_product_creation(self, product):
        assert product.name == 'product name'
        assert product.description == 'product description'
        assert product.slug == 'product-name'
        assert product.price == 1.3
        assert product.stock == 0
        assert str(product) == 'product name'

    def test_product_fail_creation(self):
        with pytest.raises(IntegrityError):
            # without price
            Product.objects.create(name='product name', description='product description')

    def test_product_with_negative_stock(self):
        with pytest.raises(IntegrityError):
            Product.objects.create(name='product name', description='product description', price=1.3, stock=-1)

    def test_product_with_negative_price(self):
            product = Product.objects.create(name='product name', description='product description', price=-1.3)
            with pytest.raises(ValidationError):
                product.full_clean()

    def test_product_update(self, product):
        assert product.price == 1.3
        product.price = 3.3
        product.save()
        assert product.price == 3.3
        assert product.name == 'product name'
        assert product.description == 'product description'

    def test_slug_creation(self):
        product = Product.objects.create(name='product name', description='product description', price=1.3)
        assert product.slug == 'product-name'
        product2 = Product.objects.create(name='product name', description='product description', price=2.2)
        assert product2.slug == "product-name-0"
        product3 = Product.objects.create(name="product name", description="product description", price=2.2)
        assert product3.slug == "product-name-1"

    def test_category_creation(self, category):
        assert category.name == 'category name'
        assert category.slug == 'category-name'

    def test_category_fail_creation(self):
        with pytest.raises(IntegrityError):
            Category.objects.create(name=None)

    def test_category_many2many(self):
        category1 = Category.objects.create(name="category1")
        category2 = Category.objects.create(name="category2")
        product = Product.objects.create(name='product1', description='product description', price=1.3)
        product.categories.add(category1, category2)
        assert product.categories.count() == 2
        assert category1.products.filter(id=product.id).exists()
        assert category2.products.filter(id=product.id).exists()

    def test_review_creation(self, user, product):
        review = Review.objects.create(user=user, product=product, rating=1, comment='comment')
        assert review.comment == 'comment'
        assert review.user.email == 'user@a.com'
        assert review.product.name == 'product name'
        assert review.rating == 1

    def test_review_incorrect_rating(self, user, product):
        review = Review.objects.create(user=user, product=product, rating=10, comment="comment")
        with pytest.raises(ValidationError):
            review.full_clean()

        with pytest.raises(IntegrityError):
            Review.objects.create(user=user, product=product, rating=-10, comment='comment')
