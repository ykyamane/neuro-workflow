#!/bin/bash
# Install Docker Desktop via Homebrew
# This requires your password for sudo

echo "Installing Docker Desktop via Homebrew..."
echo "You will be prompted for your password."
brew install --cask docker

echo ""
echo "✓ Docker Desktop installed!"
echo ""
echo "Next steps:"
echo "1. Open Docker Desktop from Applications"
echo "2. Wait for Docker to start (whale icon in menu bar)"
echo "3. Verify installation:"
echo "   docker --version"
echo "   docker-compose --version"
echo ""
echo "Then you can set up the NeuroWorkflow Web UI!"

