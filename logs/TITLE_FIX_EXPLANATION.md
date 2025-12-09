# Title Field Fix for Old Elements

## Problem

Old elements (nodes created before the recent updates) don't have a title field displayed at the top of their windows, while newly added elements do.

## Root Cause

Old nodes in the database don't have the `instanceName` field set in their `data` JSON. When nodes are loaded from the database, they only have whatever fields were saved when they were created.

## Solution

### 1. Frontend Fallback (Already Implemented)
The frontend component already has a fallback chain:
```typescript
{data.instanceName || data.label || data.file_name || data.nodeType || 'Unnamed Node'}
```

But if **all** these fields are missing, it would show "Unnamed Node".

### 2. Backend Fix (Just Implemented)
When loading nodes from the database, we now **automatically set** `instanceName` if it's missing:

```python
# In FlowService.get_flow_data()
if not node_data_dict.get("instanceName") and not node_data_dict.get("label"):
    # Set default title from available fields
    node_data_dict["instanceName"] = (
        node_data_dict.get("file_name") or 
        node_data_dict.get("nodeType") or 
        f"Node {node.id[:8]}"
    )
```

This ensures that when old nodes are loaded, they get a title assigned automatically.

## How It Works

1. **Old Node Loaded**: Database has node with `data = {"file_name": "my_node.py", "nodeType": "calculationNode"}`
2. **Backend Processing**: Checks if `instanceName` or `label` exists
3. **Auto-Assignment**: Sets `instanceName = "my_node.py"` (from `file_name`)
4. **Frontend Display**: Shows "my_node.py" as the title

## Result

- ✅ Old nodes now have titles displayed
- ✅ New nodes continue to work as before
- ✅ Fallback chain ensures something is always displayed

---

*Fixed: December 2025*

