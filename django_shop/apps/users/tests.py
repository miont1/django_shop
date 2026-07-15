import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse

User = get_user_model()

@pytest.mark.django_db
class TestUser:
    def test_user_creation(self):
        user = User.objects.create_user(email="email@email.com", password="testpass122")
        assert user.email == "email@email.com"
        assert user.check_password("testpass122") is True
        assert user.is_superuser is False

    def test_superuser_creation(self):
        user = User.objects.create_superuser(email="email@email.com", password="superuserpass123")
        assert user.email == "email@email.com"
        assert user.check_password("superuserpass123") is True
        assert user.is_superuser is True

    def test_unique_email(self):
        user = User.objects.create_user(email="email@email.com", password="testpass122")
        with pytest.raises(IntegrityError):
            user2 = User.objects.create_user(email="email@email.com", password="testpass123")

    def test_user_no_email(self):
        with pytest.raises(ValueError):
            user = User.objects.create_user(email=None, password="testpass122")

    def test_user_no_password(self):
        user = User.objects.create_user(email="email@email.com", password=None)
        assert user.has_usable_password() is False


@pytest.mark.django_db
class TestUserViews:
    def test_register_get(self, client):
        url = reverse('users:register')
        response = client.get(url)
        assert response.status_code == 200
        assert b"Register" in response.content
        assert b"Email" in response.content

    def test_login_get(self, client):
        url = reverse('users:login')
        response = client.get(url)
        assert response.status_code == 200
        assert b"Sign In" in response.content
        assert b"Email" in response.content