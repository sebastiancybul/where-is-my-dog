"""
Test for the user API
"""

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework import status

REGISTER_USER_URL = reverse("users:register")  # /api/auth/register
LOGIN_URL = reverse("users:login")  # /api/auth/login
CURRENT_USER_URL = reverse("users:current_user")  # /api/auth/me

USERNAME = "janek123"
EMAIL = "test@example.com"
PASSWORD = "testpass123"


def create_user(**params):
    """Create and return a new user"""
    defaults = {"username": USERNAME, "email": EMAIL, "password": PASSWORD}

    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


class PublicUserApiTests(APITestCase):
    """Test unauthenticated auth endpoints"""

    def test_register_user_success(self):
        """
        Test that user can register with valid credentials and receives JWT tokens.
        """  # noqa

        payload = {
            "username": "janek123",
            "email": "test@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "phone": "666444333",
        }
        res = self.client.post(REGISTER_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)
        self.assertNotIn("password2", res.data)
        self.assertEqual(res.data["user"]["username"], payload["username"])
        self.assertEqual(res.data["user"]["phone"], payload["phone"])
        self.assertIn("access", res.data["tokens"])
        self.assertIn("refresh", res.data["tokens"])

    def test_login_user_success(self):
        """Test that user can login with valid email and password."""
        user = create_user(
            username="testuser", email="test@example.com", password="test123"
        )
        payload = {"email": user.email, "password": "test123"}
        res = self.client.post(LOGIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", res.data)
        self.assertEqual(res.data["user"]["email"], user.email)
        self.assertNotIn("password", res.data)
        self.assertIn("access", res.data["tokens"])
        self.assertIn("refresh", res.data["tokens"])

    def test_login_with_invalid_password(self):
        """Test returns status 401 if password invalid"""

        payload = {"email": "test@example.com", "password": "test123"}
        create_user(**payload)
        payload["password"] = "test1234"
        res = self.client.post(LOGIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("tokens", res.data)

    def test_login_with_invalid_email(self):
        """Test returns status 401 if email invalid"""

        payload = {"email": "test@example.com", "password": "test123"}
        create_user(**payload)
        payload["email"] = "test123@example.com"
        res = self.client.post(LOGIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("tokens", res.data)

    def test_register_with_duplicate_email_fails(self):
        """Test that registration fails when email already exists."""
        create_user(email="test@example.com")

        payload = {
            "username": "newuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password2": "testpass123",
        }
        res = self.client.post(REGISTER_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_mismatched_passwords_fails(self):
        """Test that registration fails when passwords don't match."""
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password2": "different123",  # ← Różne hasła
        }
        res = self.client.post(REGISTER_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_current_user_unauthenticated_fails(self):
        """Test that unauthenticated request to /me returns 401."""
        client = APIClient()  # Nowy client bez auth
        res = client.get(CURRENT_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateAuthAPITests(APITestCase):
    """Test authenticated auth endpoints"""

    def setUp(self):
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_current_user(self):
        """Test retrieving data of the current authenticated user"""

        res = self.client.get(CURRENT_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], USERNAME)
        self.assertEqual(res.data["email"], EMAIL)
        self.assertNotIn("password", res.data)
