from rest_framework import serializers
from typing import Any, Optional, Dict, List
from .models import CustomDatabase


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


class CustomDatabaseSerializer(serializers.ModelSerializer):
    """Serializer for CustomDatabase model."""
    
    class Meta:
        model = CustomDatabase
        fields = [
            'id', 'name', 'description', 'base_url', 'api_key',
            'config', 'adapter_type', 'is_active', 'is_verified',
            'last_tested', 'test_result', 'test_error',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'is_verified', 'last_tested', 'test_result', 'test_error']
    
    def validate_base_url(self, value):
        """Validate base URL format."""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Base URL must start with http:// or https://")
        return value


class CustomDatabaseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new CustomDatabase."""
    
    class Meta:
        model = CustomDatabase
        fields = [
            'name', 'description', 'base_url', 'api_key',
            'config', 'adapter_type', 'is_active'
        ]
    
    def validate_base_url(self, value):
        """Validate base URL format."""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Base URL must start with http:// or https://")
        return value


class DatabaseConnectionTestSerializer(serializers.Serializer):
    """Serializer for testing database connection."""
    base_url = serializers.URLField(required=True, help_text="Base URL of the database")
    api_key = serializers.CharField(required=False, allow_blank=True, help_text="API key if required")
    config = serializers.DictField(required=False, default=dict, help_text="Additional configuration")
