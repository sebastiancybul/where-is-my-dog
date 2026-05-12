"""
Tests for the settings API
"""
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

UPDATE_PROFILE_URL = reverse('users:settings-profile')
CHANGE_PASSWORD_URL = reverse('users:settings-password')
DELETE_ACCOUNT_URL = reverse('users:settings-account-delete')

USERNAME = 'janek123'
EMAIL = 'test@example.com'
PASSWORD = 'testpass123'


def create_user(**params):
    """Create and return a new user"""
    defaults = {
        'username': USERNAME,
        'email': EMAIL,
        'password': PASSWORD,
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


class PublicSettingsApiTests(APITestCase):
    """Test unauthenticated settings endpoints"""

    def test_update_profile_unauthenticated_fails(self):
        res = self.client.patch(UPDATE_PROFILE_URL, {'username': 'newname'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_unauthenticated_fails(self):
        res = self.client.patch(CHANGE_PASSWORD_URL, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_account_unauthenticated_fails(self):
        res = self.client.post(DELETE_ACCOUNT_URL, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUpdateProfileApiTests(APITestCase):
    """Test update_profile endpoint"""

    def setUp(self):
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_update_username_success(self):
        res = self.client.patch(UPDATE_PROFILE_URL, {'username': 'newusername'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')

    def test_update_phone_success(self):
        res = self.client.patch(UPDATE_PROFILE_URL, {'phone': '999888777'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, '999888777')

    def test_update_username_and_phone_success(self):
        payload = {'username': 'newname', 'phone': '111222333'}
        res = self.client.patch(UPDATE_PROFILE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newname')
        self.assertEqual(self.user.phone, '111222333')

    def test_update_with_taken_username_fails(self):
        create_user(username='taken', email='other@example.com')
        res = self.client.patch(UPDATE_PROFILE_URL, {'username': 'taken'})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, USERNAME)

    def test_empty_patch_does_not_change_data(self):
        res = self.client.patch(UPDATE_PROFILE_URL, {})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, USERNAME)


class PrivateChangePasswordApiTests(APITestCase):
    """Test change_password endpoint"""

    def setUp(self):
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        payload = {
            'password': PASSWORD,
            'new_password': 'newsecurepass456',
            'new_password2': 'newsecurepass456',
        }
        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newsecurepass456'))

    def test_change_password_wrong_old_password_fails(self):
        payload = {
            'password': 'wrongpassword',
            'new_password': 'newsecurepass456',
            'new_password2': 'newsecurepass456',
        }
        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_change_password_mismatched_new_passwords_fails(self):
        payload = {
            'password': PASSWORD,
            'new_password': 'newsecurepass456',
            'new_password2': 'differentpass789',
        }
        res = self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password2', res.data)

    def test_old_password_no_longer_works_after_change(self):
        payload = {
            'password': PASSWORD,
            'new_password': 'newsecurepass456',
            'new_password2': 'newsecurepass456',
        }
        self.client.patch(CHANGE_PASSWORD_URL, payload)

        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(PASSWORD))


class PrivateDeleteAccountApiTests(APITestCase):
    """Test delete_account endpoint"""

    def setUp(self):
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_delete_account_success(self):
        res = self.client.post(DELETE_ACCOUNT_URL, {'password': PASSWORD})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(
            get_user_model().objects.filter(email=EMAIL).exists()
        )

    def test_delete_account_wrong_password_fails(self):
        res = self.client.post(DELETE_ACCOUNT_URL, {'password': 'wrongpassword'})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res.data)
        self.assertTrue(
            get_user_model().objects.filter(email=EMAIL).exists()
        )

    def test_delete_account_missing_password_fails(self):
        res = self.client.post(DELETE_ACCOUNT_URL, {})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            get_user_model().objects.filter(email=EMAIL).exists()
        )
