from django.urls import path
from .views import (
    PythonFileUploadView,
    PythonFileListView,
    UploadedNodesView,
    PythonFileCodeManagementView,
    PythonFileCopyView,
    PythonFileParameterUpdateView,
    NodeCategoryListView,
    BulkSyncNodesView,
)

app_name = "box"

urlpatterns = [
    # file upload
    path("upload/", PythonFileUploadView.as_view(), name="python-file-upload"),
    # File list
    path("files/", PythonFileListView.as_view(), name="python-file-list"),
    # File details/delete
    path("files/<uuid:pk>/", PythonFileListView.as_view(), name="python-file-detail"),
    # List of uploaded nodes (for frontend)
    path("uploaded-nodes/", UploadedNodesView.as_view(), name="uploaded-nodes"),
    path(
        "files/<str:filename>/code/",
        PythonFileCodeManagementView.as_view(),
        name="python-file-code",
    ),
    # file copy
    path("copy/", PythonFileCopyView.as_view(), name="python-file-copy"),
    # Parameter update
    path("parameters/update/", PythonFileParameterUpdateView.as_view(), name="python-file-parameter-update"),
    # Category list
    path("categories/", NodeCategoryListView.as_view(), name="node-categories"),
    # Bulk node synchronization
    path("sync/", BulkSyncNodesView.as_view(), name="bulk-sync-nodes"),
]
