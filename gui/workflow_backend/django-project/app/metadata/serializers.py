from rest_framework import serializers
from typing import Any, Optional, Dict, List


class ParameterSuggestionSerializer(serializers.Serializer):
    """Serializer for parameter suggestion response."""
    value = serializers.JSONField(help_text="Suggested parameter value")
    source = serializers.CharField(help_text="Source of the suggestion (e.g., 'allen_brain', 'neuromorpho')")
    confidence = serializers.FloatField(help_text="Confidence score from 0.0 to 1.0")
    description = serializers.CharField(help_text="Explanation of the suggestion")
    species = serializers.CharField(required=False, allow_null=True, help_text="Species this value applies to")
    citation = serializers.CharField(required=False, allow_null=True, help_text="Paper or source citation")
    metadata = serializers.DictField(required=False, allow_null=True, help_text="Additional metadata")


class ParameterSuggestionRequestSerializer(serializers.Serializer):
    """Serializer for parameter suggestion request."""
    parameter_name = serializers.CharField(required=True, help_text="Name of the parameter")
    parameter_description = serializers.CharField(required=True, help_text="Description of the parameter")
    node_type = serializers.CharField(required=False, allow_null=True, help_text="Type of node this parameter belongs to")
    species = serializers.CharField(required=False, allow_null=True, help_text="Species to query for (mouse, monkey, human, etc.)")
    context = serializers.DictField(required=False, allow_null=True, help_text="Additional context (e.g., brain region, cell type)")


class ParameterSuggestionResponseSerializer(serializers.Serializer):
    """Serializer for the full parameter suggestion API response."""
    suggestions = ParameterSuggestionSerializer(many=True, help_text="List of parameter suggestions")
    parameter_name = serializers.CharField(help_text="Name of the parameter queried")
    parameter_description = serializers.CharField(help_text="Description of the parameter queried")
    species = serializers.CharField(required=False, allow_null=True, help_text="Species filter applied")

