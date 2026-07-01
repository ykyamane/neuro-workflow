#!/bin/bash
# Container entrypoint for the NeuroWorkflow Django backend.
#
# Starts a long-lived ssh-agent on a fixed socket so the backend can submit
# jobs to the RIKEN compute server over SSH using a passphrase-protected key
# that an admin unlocks ONCE per container start:
#
#   docker exec -e SSH_AUTH_SOCK=/tmp/ssh-agent.sock -it <backend> \
#       ssh-add /root/.ssh/id_ed25519
#
# This is additive and inert by default: the agent simply holds no keys until
# an admin adds one, and nothing here runs unless a workflow is submitted with
# backend=slurm. The live (JupyterHub) execution path is unaffected.
set -e

export SSH_AUTH_SOCK=/tmp/ssh-agent.sock

# Start the agent only if its socket is not already live (fresh /tmp on start).
if [ ! -S "$SSH_AUTH_SOCK" ]; then
    ssh-agent -a "$SSH_AUTH_SOCK" >/dev/null
fi

exec "$@"
