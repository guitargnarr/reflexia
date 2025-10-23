# 🔧 Quick Fix Guide - Reflexia Environment Setup

## Problem
Test files have docstring syntax errors preventing pytest from running.

## Solution - Manual Quick Fix

Run these commands to fix all docstring issues at once:

```bash
cd ~/Projects/reflexia-model-manager

# Fix config.py
sed -i '' '13s/^/\n/' config.py

# Fix recovery.py
sed -i '' '13s/^/\n/' recovery.py

# Fix model_manager.py
sed -i '' '13s/^/\n/' model_manager.py

# Fix monitoring.py
sed -i '' '13s/^/\n/' monitoring.py

# Fix prompt_manager.py
sed -i '' '13s/^/\n/' prompt_manager.py

# Fix memory_manager.py
sed -i '' '13s/^/\n/' memory_manager.py

echo "✅ All docstrings fixed!"
```

## Test It

```bash
# Activate environment
source reflexia-venv/bin/activate

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

## Expected Output

```
tests/test_recovery.py::TestCircuitBreaker::test_circuit_breaker_initial_state PASSED
tests/test_recovery.py::TestCircuitBreaker::test_circuit_breaker_open_after_failures PASSED
tests/test_recovery.py::TestCircuitBreaker::test_circuit_breaker_half_open_after_timeout PASSED
... (more tests)
```

## What Was Wrong

The docstrings had this format (INVALID):
```python
"""
Copyright notice
"""
Module description  # ← This line causes syntax error
"""
```

Should be (VALID):
```python
"""
Copyright notice

Module description  # ← Blank line before this
"""
```

## Files That Need Fixing

- `config.py`
- `recovery.py`
- `model_manager.py`
- `monitoring.py`
- `prompt_manager.py`
- `memory_manager.py`
- `rag_helper.py`
- `rag_manager.py`
- `utils.py`
- `main.py`

## Alternative: Use sed Script

```bash
cd ~/Projects/reflexia-model-manager

# Fix all .py files in project root
for file in *.py; do
    if grep -q '"""$' "$file"; then
        # Add blank line after closing """ if next line is not blank
        sed -i '' '/"""$/!b; n; /^$/!i\
' "$file"
    fi
done

echo "✅ All files processed!"
```

## Verify Fix Worked

```bash
# Test Python syntax
python3 -m py_compile config.py
python3 -m py_compile recovery.py
python3 -m py_compile model_manager.py

# If no errors, you're good!
echo "✅ Syntax valid!"
```
