/**
 * Handle ID utilities for React Flow node connections.
 *
 * New format: {nodeId}::{fieldName}::{handleType}::{portType}
 * Legacy format: {nodeId}-{fieldName}-{handleType}-{portType}
 */

export const HANDLE_SEPARATOR = '::';

export function generateHandleId(
  nodeId: string,
  fieldName: string,
  handleType: 'input' | 'output',
  portType: string
): string {
  return `${nodeId}${HANDLE_SEPARATOR}${fieldName}${HANDLE_SEPARATOR}${handleType}${HANDLE_SEPARATOR}${portType}`;
}

export interface ParsedHandleId {
  nodeId: string;
  fieldName: string;
  handleType: 'input' | 'output';
  portType: string;
}

export function parseHandleId(handleId: string): ParsedHandleId | null {
  if (!handleId) return null;

  // Try new format first (::)
  if (handleId.includes('::')) {
    const parts = handleId.split('::');
    if (parts.length === 4) {
      return {
        nodeId: parts[0],
        fieldName: parts[1],
        handleType: parts[2] as 'input' | 'output',
        portType: parts[3],
      };
    }
  }

  // Fallback: legacy format using `-` separator
  // Format: {nodeId}-{fieldName}-{handleType}-{portType}
  // Problem: nodeId and fieldName can contain `-`
  // Strategy: handleType is always 'input' or 'output', portType is the last segment
  const parts = handleId.split('-');
  if (parts.length >= 4) {
    const portType = parts[parts.length - 1];
    const handleType = parts[parts.length - 2] as 'input' | 'output';

    if (handleType !== 'input' && handleType !== 'output') {
      return null;
    }

    // nodeId format: calc_{timestamp}_{random} — uses `_` not `-`
    // So parts[0] is always the full nodeId
    const nodeId = parts[0];
    const fieldName = parts.slice(1, -2).join('-');

    return {
      nodeId,
      fieldName,
      handleType,
      portType,
    };
  }

  return null;
}

export function generateEdgeId(
  sourceNodeId: string,
  sourceHandle: string,
  targetNodeId: string,
  targetHandle: string
): string {
  return `${sourceNodeId}${HANDLE_SEPARATOR}${sourceHandle || 'output'}${HANDLE_SEPARATOR}to${HANDLE_SEPARATOR}${targetNodeId}${HANDLE_SEPARATOR}${targetHandle || 'input'}`;
}
