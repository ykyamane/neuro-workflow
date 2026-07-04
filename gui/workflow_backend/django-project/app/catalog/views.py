"""REST API proxy views for mdb dataset catalog."""

import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.auth.authentication import KeycloakAuthentication

from .mdb_client import MDBClientError, get_mdb_client, normalize_dataset
from .serializers import CatalogListQuerySerializer, CatalogSearchQuerySerializer

logger = logging.getLogger(__name__)


def _mdb_error_response(exc: MDBClientError) -> Response:
    code = exc.status_code or status.HTTP_502_BAD_GATEWAY
    if code == status.HTTP_502_BAD_GATEWAY:
        payload = {"error": str(exc), "mdb_available": False}
    else:
        payload = {"error": str(exc), "mdb_available": True}
    return Response(payload, status=code)


@method_decorator(csrf_exempt, name="dispatch")
class CatalogSearchView(APIView):
    """
    GET /api/catalog/search/

  Query: q (required), source (optional), include_data_urls (optional)
    """

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CatalogSearchQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request parameters", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        client = get_mdb_client()
        try:
            raw_datasets = client.search_datasets(
                query=data["q"],
                source=data.get("source"),
            )
        except MDBClientError as exc:
            return _mdb_error_response(exc)

        include_urls = data.get("include_data_urls", False)
        datasets = [
            normalize_dataset(item, include_data_urls=include_urls)
            for item in raw_datasets
        ]
        return Response(
            {
                "datasets": datasets,
                "count": len(datasets),
                "query": data["q"],
                "source": data.get("source"),
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class CatalogDatasetListView(APIView):
    """
    GET /api/catalog/datasets/

    Query: source (optional), limit (optional), include_data_urls (optional)
    """

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CatalogListQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request parameters", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        client = get_mdb_client()
        try:
            raw_datasets = client.list_datasets(
                source=data.get("source"),
                limit=data.get("limit", 50),
            )
        except MDBClientError as exc:
            return _mdb_error_response(exc)

        include_urls = data.get("include_data_urls", False)
        datasets = [
            normalize_dataset(item, include_data_urls=include_urls)
            for item in raw_datasets
        ]
        return Response(
            {
                "datasets": datasets,
                "count": len(datasets),
                "source": data.get("source"),
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class CatalogDatasetDetailView(APIView):
    """
    GET /api/catalog/datasets/<source>/<dataset_id>/

    Query: include_metadata (optional, default false)
    """

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, source: str, dataset_id: str):
        include_metadata = request.query_params.get("include_metadata", "").lower() in (
            "1",
            "true",
            "yes",
        )
        client = get_mdb_client()
        try:
            raw = client.get_dataset(source=source, dataset_id=dataset_id)
        except MDBClientError as exc:
            return _mdb_error_response(exc)

        if raw is None:
            return Response(
                {"error": f"Dataset not found: {source}/{dataset_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        dataset = normalize_dataset(
            raw,
            include_data_urls=True,
            include_metadata=include_metadata,
        )
        return Response({"dataset": dataset})


@method_decorator(csrf_exempt, name="dispatch")
class CatalogStatusView(APIView):
    """GET /api/catalog/status/ — mdb api_statistics proxy."""

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = get_mdb_client()
        try:
            stats = client.get_statistics()
        except MDBClientError as exc:
            return _mdb_error_response(exc)

        return Response(
            {
                "mdb_available": True,
                "mdb_base_url": client.base_url,
                "statistics": stats,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class CatalogSyncView(APIView):
    """POST /api/catalog/sync/ — trigger mdb external API sync."""

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = get_mdb_client()
        try:
            result = client.sync_all()
        except MDBClientError as exc:
            return _mdb_error_response(exc)

        return Response({"mdb_available": True, "results": result})
