from django.urls import path
from .views import (
    ParameterSuggestionView,
    SpeciesSpecificParametersView,
    CustomDatabaseListView,
    CustomDatabaseDetailView,
    DatabaseConnectionTestView,
)

app_name = "metadata"

urlpatterns = [
    # Parameter suggestion endpoint
    path(
        "parameters/suggest/",
        ParameterSuggestionView.as_view(),
        name="parameter-suggest"
    ),
    # Species-specific parameters endpoint
    path(
        "parameters/species-specific/",
        SpeciesSpecificParametersView.as_view(),
        name="species-specific-parameters"
    ),
    # Custom database management endpoints
    path(
        "custom-databases/",
        CustomDatabaseListView.as_view(),
        name="custom-database-list"
    ),
    path(
        "custom-databases/test-connection/",
        DatabaseConnectionTestView.as_view(),
        name="test-connection"
    ),
    path(
        "custom-databases/<uuid:db_id>/",
        CustomDatabaseDetailView.as_view(),
        name="custom-database-detail"
    ),
]

