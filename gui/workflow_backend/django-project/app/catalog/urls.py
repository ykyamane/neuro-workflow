from django.urls import path

from .views import (
    CatalogDatasetDetailView,
    CatalogDatasetListView,
    CatalogSearchView,
    CatalogStatusView,
    CatalogSyncView,
)

app_name = "catalog"

urlpatterns = [
    path("search/", CatalogSearchView.as_view(), name="search"),
    path("datasets/", CatalogDatasetListView.as_view(), name="dataset-list"),
    path(
        "datasets/<str:source>/<str:dataset_id>/",
        CatalogDatasetDetailView.as_view(),
        name="dataset-detail",
    ),
    path("status/", CatalogStatusView.as_view(), name="status"),
    path("sync/", CatalogSyncView.as_view(), name="sync"),
]
