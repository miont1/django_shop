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

    def test_profile_unauthenticated(self, client):
        url = reverse('users:profile')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_profile_authenticated(self, client):
        user = User.objects.create_user(email="testuser@example.com", password="testpassword123")
        client.force_login(user)
        url = reverse('users:profile')
        response = client.get(url)
        assert response.status_code == 200
        assert b"My Account" in response.content
        assert b"Personal Info" in response.content

    def test_profile_post(self, client):
        user = User.objects.create_user(email="testuser@example.com", password="testpassword123")
        client.force_login(user)
        url = reverse('users:profile')
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'testuser@example.com',
            'phone': '123456789',
            'city': 'Kyiv',
            'address': 'Khreshchatyk 1'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.phone == '123456789'
        assert user.city == 'Kyiv'
        assert user.address == 'Khreshchatyk 1'

    def test_password_change_get(self, client):
        user = User.objects.create_user(email="testuser@example.com", password="testpassword123")
        client.force_login(user)
        url = reverse('users:password_change')
        response = client.get(url)
        assert response.status_code == 200
        assert b"Change Password" in response.content

    def test_password_change_post(self, client):
        user = User.objects.create_user(email="testuser@example.com", password="testpassword123")
        client.force_login(user)
        url = reverse('users:password_change')
        data = {
            'old_password': 'testpassword123',
            'new_password1': 'newsecurepass123',
            'new_password2': 'newsecurepass123',
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse('users:password_change_done')
        user.refresh_from_db()
        assert user.check_password('newsecurepass123') is True

    def test_password_change_done_get(self, client):
        user = User.objects.create_user(email="testuser@example.com", password="testpassword123")
        client.force_login(user)
        url = reverse('users:password_change_done')
        response = client.get(url)
        assert response.status_code == 200
        assert b"Success!" in response.content or b"password has been changed" in response.content

    def test_password_reset_get(self, client):
        url = reverse('users:password_reset')
        response = client.get(url)
        assert response.status_code == 200
        assert b"Reset Password" in response.content
        assert b"Email" in response.content

    def test_password_reset_done_get(self, client):
        url = reverse('users:password_reset_done')
        response = client.get(url)
        assert response.status_code == 200
        assert b"Check your email" in response.content

    def test_password_reset_confirm_invalid(self, client):
        url = reverse('users:password_reset_confirm', kwargs={'uidb64': 'MQ', 'token': 'invalid-token'})
        response = client.get(url)
        assert response.status_code == 200
        assert b"Link Invalid" in response.content

    def test_password_reset_complete_get(self, client):
        url = reverse('users:password_reset_complete')
        response = client.get(url)
        assert response.status_code == 200
        assert b"Password Reset!" in response.content