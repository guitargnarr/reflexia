#!/bin/bash
# One-command fix for all Reflexia docstring issues

set -e
cd "$(dirname "$0")"

echo "🔧 Fixing Reflexia Docstrings..."
echo ""

# List of files with docstring issues
FILES=(
    "config.py"
    "recovery.py"
    "model_manager.py"
    "monitoring.py"
    "prompt_manager.py"
    "memory_manager.py"
    "rag_helper.py"
    "rag_manager.py"
    "utils.py"
    "main.py"
)

FIXED=0

for file in "${FILES[@]}"; do
    if [[ -f "$file" ]]; then
        # Check if file has the pattern: """ on line 12, text on line 13
        if sed -n '12p' "$file" | grep -q '"""' && sed -n '13p' "$file" | grep -qv '^$'; then
            # Insert blank line at line 13
            sed -i '' '13s/^/\n/' "$file"
            echo "✅ Fixed: $file"
            ((FIXED++))
        else
            echo "⏭  Skipped: $file (already fixed or different format)"
        fi
    else
        echo "⚠️  Not found: $file"
    fi
done

echo ""
echo "=========================================="
echo "✅ Fixed $FIXED files"
echo "=========================================="
echo ""
echo "Now run:"
echo "  source reflexia-venv/bin/activate"
echo "  pytest tests/ -v"
