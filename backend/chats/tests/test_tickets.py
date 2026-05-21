from unittest.mock import patch

import fakeredis
from django.test import TestCase

from chats.tickets import consume_ticket, generate_ticket


_server = fakeredis.FakeServer()


def fake_client():
    """Returns the same fakeredis server instance for all calls within a test."""
    return fakeredis.FakeRedis(server=_server, decode_responses=True)


class GenerateTicketTests(TestCase):
    def setUp(self):
        # Reset Redis state before each test to avoid side effects
        fakeredis.FakeRedis(server=_server).flushall()

    @patch('chats.tickets._client', fake_client)
    def test_returns_non_empty_string(self):
        ticket = generate_ticket(user_id=1)
        self.assertIsInstance(ticket, str)
        self.assertTrue(len(ticket) > 0)

    @patch('chats.tickets._client', fake_client)
    def test_two_calls_return_different_tickets(self):
        ticket1 = generate_ticket(user_id=1)
        ticket2 = generate_ticket(user_id=1)
        self.assertNotEqual(ticket1, ticket2)


class ConsumeTicketTests(TestCase):
    def setUp(self):
        fakeredis.FakeRedis(server=_server).flushall()

    @patch('chats.tickets._client', fake_client)
    def test_returns_user_id_for_valid_ticket(self):
        ticket = generate_ticket(user_id=7)
        result = consume_ticket(ticket)
        self.assertEqual(result, 7)

    @patch('chats.tickets._client', fake_client)
    def test_ticket_is_one_time_use(self):
        ticket = generate_ticket(user_id=7)
        consume_ticket(ticket)
        self.assertIsNone(consume_ticket(ticket))

    @patch('chats.tickets._client', fake_client)
    def test_returns_none_for_unknown_ticket(self):
        self.assertIsNone(consume_ticket("nonexistent_ticket"))
