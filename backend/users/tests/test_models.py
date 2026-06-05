"""
Tests for User model
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class UserModelTests(TestCase):
    """Test User model"""

    def test_create_user_successful(self):
        """Test creating a user is successful"""
        email = "test@example.com"
        password = "testpass123"
        username = "testuser"

        user = User.objects.create_user(
            email=email, password=password, username=username
        )

        self.assertEqual(user.email, email)
        self.assertEqual(user.username, username)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.email_verified)
        self.assertFalse(user.is_moderator)
        self.assertFalse(user.is_banned)

    def test_email_normalized(self):
        """Test email domain is normalized"""
        email = "test@EXAMPLE.COM"
        user = User.objects.create_user(
            email=email, password="test123", username="testuser"
        )

        self.assertEqual(user.email, "test@example.com")

    def test_username_required(self):
        """Test creating user without username raises error"""
        with self.assertRaises((ValueError, IntegrityError)):
            User.objects.create_user(
                email="test@example.com", password="test123", username=""
            )

    def test_email_unique(self):
        """Test email must be unique"""
        email = "test@example.com"
        User.objects.create_user(
            email=email, password="test123", username="user1"
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email=email, password="test123", username="user2"
            )

    def test_full_name_with_names(self):
        """Test full_name property returns first + last name"""
        user = User.objects.create_user(
            email="test@example.com",
            password="test123",
            username="testuser",
            first_name="John",
            last_name="Doe",
        )

        self.assertEqual(user.full_name, "John Doe")

    def test_full_name_without_names(self):
        """Test full_name returns username if names not set"""
        user = User.objects.create_user(
            email="test@example.com", password="test123", username="testuser"
        )

        self.assertEqual(user.full_name, "testuser")

    def test_str_method(self):
        """Test __str__ method returns username"""
        user = User.objects.create_user(
            email="test@example.com", password="test123", username="testuser"
        )

        self.assertEqual(str(user), "testuser")
