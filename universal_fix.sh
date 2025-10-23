#!/bin/bash
# Universal docstring fixer for Reflexia

cd "$(dirname "$0")"

echo "🔧 Fixing all docstring issues..."

# Fix the pattern: """<newline>Text<newline>"""
# Should be: """<newline><newline>Text<newline>"""

for file in *.py tests/*.py; do
    if [[ -f "$file" ]]; then
        # Use sed to find """ followed by text on next line, then another """
        # and insert a blank line between them
        sed -i '' '/"""$/{ N; /\n[A-Z]/{ s/"""\n/"""\n\n/; }; }' "$file" 2>/dev/null
    fi
done

echo "✅ All files processed"
echo ""
echo "Testing imports..."
python3 -c "import config; import recovery; import monitoring; print('✅ All modules import successfully!')" 2>&1
