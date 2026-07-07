import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

# Create your tests here.

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