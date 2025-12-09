#!/bin/bash

# Build NEST simulator enabled JupyterLab user server image
echo "Building NEST simulator enabled JupyterLab image..."

docker build --platform linux/amd64 -t nest-jupyterlab -f Dockerfile.nest .

if [ $? -eq 0 ]; then
    echo "✅ Successfully built nest-jupyterlab:latest"
    echo "This image will be used by JupyterHub for user servers"
else
    echo "❌ Failed to build nest-jupyterlab:latest"
    exit 1
fi
