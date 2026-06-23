from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from .models import CustomDatabase
from .views import CustomDatabaseDetailView, CustomDatabaseListView


class CustomDatabaseAccessTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner")
        self.other_user = User.objects.create_user(username="other")

    def _database(self, **overrides):
        data = {
            "name": "Test custom database",
            "base_url": "https://example.com",
            "adapter_type": "rest_api",
            "is_active": True,
            "created_by": self.owner,
        }
        data.update(overrides)
        return CustomDatabase.objects.create(**data)

    def test_list_only_returns_active_databases(self):
        active = self._database(name="Active database")
        self._database(name="Inactive database", is_active=False)

        request = self.factory.get("/api/metadata/custom-databases/")
        force_authenticate(request, user=self.owner)

        response = CustomDatabaseListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [str(active.id)])

    def test_owner_can_delete_inactive_database(self):
        database = self._database(is_active=False)

        request = self.factory.delete(f"/api/metadata/custom-databases/{database.id}/")
        force_authenticate(request, user=self.owner)

        response = CustomDatabaseDetailView.as_view()(request, db_id=database.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_manage_database(self):
        database = self._database()

        request = self.factory.get(f"/api/metadata/custom-databases/{database.id}/")
        force_authenticate(request, user=self.other_user)

        response = CustomDatabaseDetailView.as_view()(request, db_id=database.id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
