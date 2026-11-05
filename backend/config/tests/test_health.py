from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

HEALTH_URL = reverse("health")


class HealthCheckTests(APITestCase):
    def test_returns_ok(self):
        res = self.client.get(HEALTH_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json(), {"status": "ok"})

    def test_invalid_token_is_ignored(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")

        res = self.client.get(HEALTH_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_does_not_query_the_database(self):
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(HEALTH_URL)

        self.assertEqual(len(ctx.captured_queries), 0)
