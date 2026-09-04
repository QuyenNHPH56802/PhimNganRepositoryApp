# Test Plan: Provider Selection in Project Creation

## Implementation Summary

### Backend ✅
- `GET /providers/{kind}/metadata` endpoint returns provider list with `requires_api_key` flag
- `ProjectCreate` schema accepts `tts_provider_id`, `tts_config`, `translate_provider_id`, `translate_config`
- `create_project` endpoint upserts provider configs to `provider_configs` table

### Frontend ✅
- Fetches TTS and Translation provider metadata on mount
- Displays provider dropdowns with clear labels (🎙️ free, 💻 GPU, ☁️ cloud)
- Shows conditional API key input when `requires_api_key=true`
- Validates API key presence before submission
- Passes provider configs to `api.createProject()`

## Test Scenarios

### Test 1: Edge TTS (No API Key Required) ✅ Expected to work
1. Navigate to http://localhost:3000/projects/new
2. Fill in:
   - Title: "Test Edge TTS"
   - TTS Engine: "Edge TTS (Miễn phí, 2 giọng VN)"
   - Translation: "Ollama Local"
3. Click "Tạo project & xử lý"
4. **Expected**: Project created successfully, workflow triggered
5. **Verify**: Check workflow runs without TTS provider errors

### Test 2: Azure TTS without API Key ❌ Expected to fail
1. Navigate to http://localhost:3000/projects/new
2. Fill in:
   - Title: "Test Azure No Key"
   - TTS Engine: "Azure TTS (Cần API key)"
   - Leave API key field empty
3. Click "Tạo project & xử lý"
4. **Expected**: Form validation error "TTS provider cần API key..."
5. **Verify**: Cannot submit form

### Test 3: Azure TTS with API Key ✅ Expected to work
1. Navigate to http://localhost:3000/projects/new
2. Fill in:
   - Title: "Test Azure With Key"
   - TTS Engine: "Azure TTS (Cần API key)"
   - API key: "test-azure-key-12345"
3. Click "Tạo project & xử lý"
4. **Expected**: Project created, config saved to provider_configs table
5. **Verify**: 
   ```sql
   SELECT * FROM provider_configs 
   WHERE provider_kind='tts' AND provider_id='cloud_azure';
   ```
6. **Verify**: Workflow uses Azure TTS with provided key

### Test 4: Translation Provider with API Key
1. Navigate to http://localhost:3000/projects/new
2. Fill in:
   - Title: "Test OpenAI Translation"
   - Translation Engine: "OpenAI / DeepSeek"
   - API key: "sk-proj-test123"
3. Click "Tạo project & xử lý"
4. **Expected**: Project created with translate provider config
5. **Verify**: Config saved with correct API key in encrypted/secure format

### Test 5: Both Providers Need Keys
1. Select Azure TTS + OpenAI Translation
2. Provide both API keys
3. **Expected**: Both configs saved, workflow uses both
4. **Verify**: Both entries in provider_configs table

## Database Verification

```sql
-- Check provider_configs table structure
SELECT * FROM provider_configs ORDER BY created_at DESC LIMIT 5;

-- Verify config JSON contains api_key (may be encrypted)
SELECT 
  project_id, 
  provider_kind, 
  provider_id, 
  config,
  is_active 
FROM provider_configs 
WHERE project_id = '<test-project-id>';
```

## API Verification

```bash
# 1. Check provider metadata endpoint
curl http://localhost:8000/providers/tts/metadata

# Expected response:
# {
#   "providers": [
#     {"id": "edge_tts", "requires_api_key": false, ...},
#     {"id": "cloud_azure", "requires_api_key": true, ...}
#   ]
# }

# 2. Check translate metadata endpoint
curl http://localhost:8000/providers/translate/metadata

# 3. Create project with provider configs
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API Test Project",
    "source_language": "zh",
    "target_language": "vi",
    "quality_mode": "balanced",
    "language_profile": "zh-vi",
    "tts_provider_id": "cloud_azure",
    "tts_config": {"api_key": "test-key"},
    "translate_provider_id": "openai_compatible_http",
    "translate_config": {"api_key": "sk-test"}
  }'
```

## Success Criteria

✅ Provider metadata endpoint returns correct data
✅ Frontend displays provider dropdowns correctly
✅ API key validation works (blocks submission when required but empty)
✅ Provider configs are saved to database
✅ Workflow reads provider configs and uses correct provider
✅ Error handling when API key is invalid/expired
✅ UI hints guide user to Settings page for global config

## Known Issues / Future Work

- [ ] Encrypt API keys in database (currently stored in plaintext JSON)
- [ ] Add provider config inheritance from global Settings
- [ ] Add provider health check before workflow trigger
- [ ] Show provider status indicator (available/unavailable)
- [ ] Add provider switching during workflow retry
