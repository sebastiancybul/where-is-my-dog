from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

WS_TICKET_URL = reverse('ws-ticket')

User = get_user_model()


def create_user(**params):
    defaults = {'username': 'testuser', 'email': 'test@example.com', 'password': 'testpass123'}
    defaults.update(params)
    return User.objects.create_user(**defaults)


class WsTicketApiTests(APITestCase):
    def test_unauthenticated_return_401(self):
        res = self.client.post(WS_TICKET_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('chats.views.converstaion.generate_ticket', return_value='fake_ticket')
    def test_authenticated_returns_200(self, _):
        user = create_user()
        self.client.force_authenticate(user=user)
        res = self.client.post(WS_TICKET_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @patch('chats.views.converstaion.generate_ticket', return_value='fake_ticket')
    def test_ticket_is_in_response(self, _):
        user = create_user()
        self.client.force_authenticate(user=user)
        res = self.client.post(WS_TICKET_URL)
        self.assertIn('ticket', res.data)

    @patch('chats.views.converstaion.generate_ticket', return_value='fake_ticket')
    def test_ticket_is_a_non_empty_string(self, _):
        user = create_user()
        self.client.force_authenticate(user=user)
        res = self.client.post(WS_TICKET_URL)
        self.assertIsInstance(res.data['ticket'], str)
        self.assertTrue(len(res.data['ticket']) > 0)

    def test_get_method_not_allowed(self):
        user = create_user()
        self.client.force_authenticate(user=user)
        res = self.client.get(WS_TICKET_URL)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)