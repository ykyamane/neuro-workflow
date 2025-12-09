from django.urls import path
from .views import (
    ParameterSuggestionView,
    SpeciesSpecificParametersView,
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
]

