# Quick Test Guide for Custom Database Feature

## ✅ Test Database 1: NeuroMorpho.org (Recommended)

This is one of our existing databases, so we can test if the generic adapter can integrate it.

### Step 1: Test Connection

```bash
curl -X POST http://localhost:3000/api/metadata/custom-databases/test-connection/ \
  -H "Content-Type: application/json \
  -d '{
    "base_url": "https://neuromorpho.org/api",
    "api_key": ""
  }'
```

**Expected Result**: Connection should succeed (server is reachable)

### Step 2: Create Database via UI

1. Go to **Settings → Custom Databases** in the UI
2. Click **"Add Database"**
3. Fill in:
   - **Name**: `NeuroMorpho Test`
   - **Description**: `Testing generic adapter with NeuroMorpho`
   - **Base URL**: `https://neuromorpho.org/api`
   - **API Key**: (leave empty)
   - **Adapter Type**: `REST API`
4. Click **"Test Connection"** - should succeed
5. Click **"Create"**

### Step 3: Create Database via API

```bash
curl -X POST http://localhost:3000/api/metadata/custom-databases/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NeuroMorpho Test",
    "description": "Testing generic adapter with NeuroMorpho API",
    "base_url": "https://neuromorpho.org/api",
    "api_key": "",
    "adapter_type": "rest_api",
    "is_active": true
  }'
```

### Step 4: Test Parameter Query

After creating the database, test if it's included in parameter suggestions:

```bash
curl "http://localhost:3000/api/metadata/parameters/suggest/?parameter_name=dendrite_length&parameter_description=Total+length+of+dendrites&species=mouse"
```

**Expected**: You should see suggestions from:
- Allen Brain Atlas
- NeuroMorpho (original adapter)
- NeuroMorpho Test (your custom database via generic adapter)
- PubMed
- NeuroML-DB

---

## ✅ Test Database 2: Simple REST API Test

For a simple connectivity test, you can use a public API that returns JSON:

### Test with JSONPlaceholder (Simple Test API)

```bash
curl -X POST http://localhost:3000/api/metadata/custom-databases/test-connection/ \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://jsonplaceholder.typicode.com",
    "api_key": ""
  }'
```

**Note**: This won't have neuroscience data, but tests connectivity.

---

## 📋 Complete Test Checklist

- [ ] Test connection to NeuroMorpho API
- [ ] Create custom database via UI
- [ ] Verify database appears in list
- [ ] Test connection button works
- [ ] Query parameter suggestions (verify custom DB is included)
- [ ] Edit database (change name, test connection again)
- [ ] Delete database

---

## 🔍 What to Look For

### Connection Test:
- ✅ Success message with working pattern
- ❌ Error message with helpful suggestions if it fails

### Parameter Suggestions:
- Custom database should appear in the `source` field
- Confidence score should be around 0.6 (for generic adapter)
- Values should be extracted if API response format matches

### UI:
- Database list shows all databases
- Status badges (Verified/Not Verified, Active/Inactive)
- Edit and Delete buttons work
- Test connection shows results

---

## 🐛 Troubleshooting

### Connection Test Fails:
1. Check if URL is correct (must start with `http://` or `https://`)
2. Check if server is accessible from Docker container
3. Check if API requires authentication (API key)
4. Review error suggestions in the response

### Database Not Appearing in Suggestions:
1. Check if database is marked as `is_verified: true`
2. Check if database is `is_active: true`
3. Check backend logs for errors
4. Verify the API response format matches expected patterns

### Values Not Extracted:
- The generic adapter looks for values in common JSON patterns
- If your API uses a different format, you may need to customize the adapter
- Check the API response structure and see if it matches expected patterns
