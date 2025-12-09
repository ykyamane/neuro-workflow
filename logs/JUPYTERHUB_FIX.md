# JupyterHub Network Configuration Fix

## Issue
JupyterHub was unable to spawn user containers. The spawned containers were crashing immediately after creation.

## Root Cause
Network mismatch between JupyterHub configuration and Docker Compose setup:
- **Docker Compose**: JupyterHub service is on `jupyterhub-network`
- **JupyterHub Config**: Was trying to spawn containers on `neuro-workflow_workflow` network
- **Result**: Spawned containers couldn't communicate with JupyterHub, causing timeouts

## Fix Applied

**File**: `gui/workflow_backend/django-project/neuroworkflow/jupyterhub_config.py`

**Changed**:
```python
# Before:
c.DockerSpawner.network_name = "neuro-workflow_workflow"

# After:
c.DockerSpawner.network_name = "jupyterhub-network"
```

## Verification

After the fix:
1. JupyterHub restarted successfully
2. Network configuration now matches Docker Compose setup
3. Spawned containers will be on the same network as JupyterHub

## Testing

To test if the fix works:
1. Go to http://localhost:8000
2. Log in with username `test` and password `password`
3. Wait for the server to spawn (should complete within 2-3 minutes)
4. You should be redirected to JupyterLab

## If Issues Persist

If containers still fail to spawn, check:

1. **Container logs**:
   ```bash
   docker logs $(docker ps -aq --filter "name=jupyter-test" | head -1)
   ```

2. **JupyterHub logs**:
   ```bash
   docker-compose -f gui/docker-compose.yml logs jupyterhub --tail 50
   ```

3. **Network connectivity**:
   ```bash
   docker network inspect jupyterhub-network
   ```

4. **Image availability**:
   ```bash
   docker images | grep nest-jupyterlab
   ```

## Related Files

- `gui/docker-compose.yml` - Defines `jupyterhub-network`
- `gui/workflow_backend/django-project/neuroworkflow/jupyterhub_config.py` - JupyterHub configuration

## Note

This issue likely occurred because:
- Upstream repository may have changed network configuration
- During merge, the network name in config didn't match the docker-compose.yml
- The merge preferred upstream's config, but docker-compose.yml had a different network name

**Resolution**: Aligned config with docker-compose.yml network name.

