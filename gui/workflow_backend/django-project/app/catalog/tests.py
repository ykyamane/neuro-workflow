from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from .mdb_client import MDBClient, normalize_dataset
from .views import CatalogDatasetDetailView, CatalogSearchView, CatalogStatusView


class NormalizeDatasetTests(TestCase):
    def test_normalize_includes_url_summary(self):
        raw = {
            "source": "dandi",
            "dataset_id": "000003",
            "name": "Example",
            "description": "desc",
            "synced_at": "2026-01-01T00:00:00",
            "metadata": {
                "landing_page": "https://dandiarchive.org/dandiset/000003/draft",
                "data_urls": [
                    {
                        "url": "https://example.com/a",
                        "browse_url": "https://dandiarchive.org/dandiset/000003/draft/files/location/a.nwb",
                        "label": "a.nwb",
                    }
                ],
                "data_url_summary": {
                    "count": 1,
                    "total_count": 10,
                    "truncated": True,
                },
            },
        }
        result = normalize_dataset(raw, include_data_urls=True)
        self.assertEqual(result["data_url_count"], 1)
        self.assertEqual(result["data_url_total"], 10)
        self.assertTrue(result["truncated"])
        self.assertEqual(len(result["data_urls"]), 1)
        self.assertEqual(
            result["landing_page"],
            "https://dandiarchive.org/dandiset/000003/draft",
        )


@override_settings(MDB_BASE_URL="http://mdb.test:8004")
class CatalogViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        User = get_user_model()
        self.user = User.objects.create_user(username="catalog-user")

    @patch("app.catalog.views.get_mdb_client")
    def test_search_requires_query(self, mock_get_client):
        mock_get_client.return_value = MagicMock()
        request = self.factory.get("/api/catalog/search/")
        force_authenticate(request, user=self.user)
        response = CatalogSearchView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("app.catalog.views.get_mdb_client")
    def test_search_returns_normalized_datasets(self, mock_get_client):
        client = MagicMock()
        client.search_datasets.return_value = [
            {
                "source": "cbs",
                "dataset_id": "20230511-001",
                "name": "CBS dataset",
                "description": "test",
                "synced_at": "2026-01-01",
                "metadata": {"data_urls": [], "data_url_summary": {"count": 0}},
            }
        ]
        mock_get_client.return_value = client

        request = self.factory.get("/api/catalog/search/", {"q": "marmoset"})
        force_authenticate(request, user=self.user)
        response = CatalogSearchView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["datasets"][0]["source"], "cbs")
        client.search_datasets.assert_called_once_with(query="marmoset", source=None)

    @patch("app.catalog.views.get_mdb_client")
    def test_dataset_detail_not_found(self, mock_get_client):
        client = MagicMock()
        client.get_dataset.return_value = None
        mock_get_client.return_value = client

        request = self.factory.get("/api/catalog/datasets/dandi/missing/")
        force_authenticate(request, user=self.user)
        response = CatalogDatasetDetailView.as_view()(
            request, source="dandi", dataset_id="missing"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("app.catalog.views.get_mdb_client")
    def test_status_proxies_statistics(self, mock_get_client):
        client = MagicMock()
        client.base_url = "http://mdb.test:8004"
        client.get_statistics.return_value = {"total_datasets": 42}
        mock_get_client.return_value = client

        request = self.factory.get("/api/catalog/status/")
        force_authenticate(request, user=self.user)
        response = CatalogStatusView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["mdb_available"])
        self.assertEqual(response.data["statistics"]["total_datasets"], 42)


class MDBClientUnitTests(TestCase):
    def test_base_url_strips_trailing_slash(self):
        client = MDBClient(base_url="http://example.com:8004/")
        self.assertEqual(client.base_url, "http://example.com:8004")
