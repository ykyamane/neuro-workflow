from django.db import models
from django.contrib.auth.models import User
import uuid


class FlowProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="flow_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "flow_projects"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class FlowNode(models.Model):
    id = models.CharField(max_length=255, primary_key=True)  # React Flow node ID
    project = models.ForeignKey(
        FlowProject, on_delete=models.CASCADE, related_name="nodes"
    )
    position_x = models.FloatField()
    position_y = models.FloatField()
    node_type = models.CharField(max_length=100)
    data = models.JSONField()  # React Flow, The entire data object
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "flow_nodes"
        ordering = ["created_at"]

    def __str__(self):
        return f"Node {self.id} in {self.project.name}"

    def has_parameter_modifications(self):
        """Check for parameter changes"""
        return self.data.get("has_parameter_modifications", False)

    def get_modified_parameters(self):
        """Get the list of changed parameters"""
        modifications = self.data.get("parameter_modifications", {})
        return {
            param_key: {
                "original_value": param_info.get("original_value"),
                "current_value": param_info.get("current_value"),
                "modified_at": param_info.get("modified_at")
            }
            for param_key, param_info in modifications.items()
            if param_info.get("is_modified", False)
        }

    def get_parameter_modification_count(self):
        """Get the number of changed parameters"""
        return len(self.get_modified_parameters())


class FlowEdge(models.Model):
    id = models.CharField(max_length=255, primary_key=True)  # React Flow edge ID
    project = models.ForeignKey(
        FlowProject, on_delete=models.CASCADE, related_name="edges"
    )
    source_node = models.ForeignKey(
        FlowNode, on_delete=models.CASCADE, related_name="outgoing_edges"
    )
    target_node = models.ForeignKey(
        FlowNode, on_delete=models.CASCADE, related_name="incoming_edges"
    )
    source_handle = models.CharField(max_length=255, null=True, blank=True)
    target_handle = models.CharField(max_length=255, null=True, blank=True)
    edge_data = models.JSONField(default=dict)  # Additional edge settings
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "flow_edges"
        ordering = ["created_at"]

    def __str__(self):
        return f"Edge {self.id}: {self.source_node.id} -> {self.target_node.id}"
