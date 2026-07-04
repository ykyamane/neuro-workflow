from rest_framework import serializers

from .mdb_client import VALID_SOURCES


class CatalogSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=True, allow_blank=False, max_length=500)
    source = serializers.ChoiceField(
        choices=sorted(VALID_SOURCES),
        required=False,
        allow_null=True,
    )
    include_data_urls = serializers.BooleanField(required=False, default=False)


class CatalogListQuerySerializer(serializers.Serializer):
    source = serializers.ChoiceField(
        choices=sorted(VALID_SOURCES),
        required=False,
        allow_null=True,
    )
    limit = serializers.IntegerField(required=False, default=50, min_value=1, max_value=500)
    include_data_urls = serializers.BooleanField(required=False, default=False)
