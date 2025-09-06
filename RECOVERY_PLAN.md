# Recovery Plan - Clean Git History for Phase 1 & 2 Implementation

## Problem
- We have complete Phase 1 & 2 implementation working at commit `fa468ad`
- But git history contains hardcoded API keys in test files
- GitHub push protection blocks any push that includes commits with secrets
- Need to preserve all implementation + test files but remove secret history

## Solution: Extract & Clean Approach

### Step 1: Backup Current Working State
Save all current files to temporary location:
- All Phase 1 & 2 implementation files (providers.py, media_handlers.py, const.py, services.yaml, etc.)
- All test files (test_*.py, conftest.py, pytest.ini, run_tests.sh, etc.)
- Configuration files (manifest.json, hacs.json, etc.)

### Step 2: Reset to Clean Upstream
```bash
git reset --hard 34b7028  # Clean upstream commit with no secrets
```

### Step 3: Restore Clean Implementation
Copy back from temp:
- **Implementation files** (with domain already changed from llmvision_debug to llmvision):
  - custom_components/llmvision/providers.py (with structured response support)
  - custom_components/llmvision/media_handlers.py (with _select_frames_with_minimums)
  - custom_components/llmvision/const.py (with Phase 1 & 2 constants)
  - custom_components/llmvision/services.yaml (with new parameters)
  - custom_components/llmvision/manifest.json (v1.6.0, rmaher001 repo)
  - custom_components/llmvision/llm_logger.py (updated paths)
  - Other supporting files

- **Test files** (cleaned of hardcoded secrets):
  - tests/unit/test_structured_responses.py
  - tests/unit/test_frame_selection.py
  - tests/integration/test_provider_integration.py
  - tests/conftest.py, pytest.ini, run_tests.sh
  - tests/test_secrets.py.template (placeholder keys like "your-key-here")

- **Configuration files**:
  - hacs.json (updated for LLM Vision)
  - package_detection.yaml (example automation)

### Step 4: Single Clean Commit
Create one commit with:
- Complete Phase 1 & 2 implementation
- Complete test suite with placeholder secrets
- All configuration for HACS deployment
- Clean git history with no real API keys

### Step 5: Push Clean History
Push to GitHub without triggering secret detection.

## What We Preserve
✅ Complete Phase 1 - Structured JSON response support for all providers  
✅ Complete Phase 2 - Multi-camera frame selection with _select_frames_with_minimums  
✅ All test files and test structure  
✅ Domain renamed from llmvision_debug to llmvision  
✅ Version 1.6.0 ready for HACS deployment  
✅ Clean git history without secrets  

## What We Fix
❌ Remove hardcoded API keys from git history  
❌ Remove secret detection blocking GitHub pushes  
❌ Provide template for users to add their own test keys  

## Result
- Clean repository ready for public deployment
- Complete implementation with all 12 hours of work preserved
- Test suite that users can run by adding their own API keys
- No more GitHub push protection issues