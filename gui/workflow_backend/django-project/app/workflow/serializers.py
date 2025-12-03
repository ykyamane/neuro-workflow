from rest_framework import serializers
from .models import FlowProject, FlowNode, FlowEdge
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class FlowProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    nodes_count = serializers.SerializerMethodField()
    edges_count = serializers.SerializerMethodField()

    class Meta:
        model = FlowProject
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "created_at",
            "updated_at",
            "is_active",
            "nodes_count",
            "edges_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "owner"]

    def get_nodes_count(self, obj):
        if not obj.pk:
            return 0
        return getattr(obj, "nodes", []).count() if hasattr(obj, "nodes") else 0

    def get_edges_count(self, obj):
        if not obj.pk:
            return 0
        return getattr(obj, "edges", []).count() if hasattr(obj, "edges") else 0


class FlowNodeSerializer(serializers.ModelSerializer):
    has_parameter_modifications = serializers.SerializerMethodField()
    modified_parameters = serializers.SerializerMethodField()
    parameter_modification_count = serializers.SerializerMethodField()

    class Meta:
        model = FlowNode
        fields = [
            "id",
            "project",
            "position_x",
            "position_y",
            "node_type",
            "data",
            "created_at",
            "updated_at",
            "has_parameter_modifications",
            "modified_parameters",
            "parameter_modification_count",
        ]
        read_only_fields = ["created_at", "updated_at", "has_parameter_modifications", "modified_parameters", "parameter_modification_count"]

    def get_has_parameter_modifications(self, obj):
        """Are there any parameter changes?"""
        return obj.has_parameter_modifications()

    def get_modified_parameters(self, obj):
        """Details of changed parameters"""
        return obj.get_modified_parameters()

    def get_parameter_modification_count(self, obj):
        """The number of parameters that were changed"""
        return obj.get_parameter_modification_count()

    def validate(self, data):
        # React Flow-style validation
        if "data" in data:
            required_keys = ["label"]
            for key in required_keys:
                if key not in data["data"]:
                    raise serializers.ValidationError(
                        f"Node data must contain '{key}' field"
                    )
        return data


class FlowEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowEdge
        fields = [
            "id",
            "project",
            "source_node",
            "target_node",
            "source_handle",
            "target_handle",
            "edge_data",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        # Connections can only be made between nodes within the same project
        if data["source_node"].project != data["target_node"].project:
            raise serializers.ValidationError("Nodes must be in the same project")

        # Preventing self-reference
        if data["source_node"] == data["target_node"]:
            raise serializers.ValidationError("Cannot connect a node to itself")

        return data


# Flow-preserving serializer for the entire React Flow
class FlowDataSerializer(serializers.Serializer):
    nodes = serializers.ListField(child=serializers.DictField())
    edges = serializers.ListField(child=serializers.DictField())

    def validate_nodes(self, value):
        for node in value:
            if "id" not in node:
                raise serializers.ValidationError("Each node must have an 'id' field")
            if (
                "position" not in node
                or "x" not in node["position"]
                or "y" not in node["position"]
            ):
                raise serializers.ValidationError(
                    "Each node must have position with x and y coordinates"
                )
            if "data" not in node:
                raise serializers.ValidationError("Each node must have a 'data' field")
        return value

    def validate_edges(self, value):
        for edge in value:
            required_fields = ["id", "source", "target"]
            for field in required_fields:
                if field not in edge:
                    raise serializers.ValidationError(
                        f"Each edge must have a '{field}' field"
                    )
        return value
