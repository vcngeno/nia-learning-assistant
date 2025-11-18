"""Validate critical files before starting the application"""
import sys
import ast
from pathlib import Path

def validate_python_file(filepath):
    """Check if file is valid Python and doesn't contain HTML"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

            # Check for HTML tags
            html_indicators = ['<!DOCTYPE html>', '<html', '<head>', '<body>']
            if any(indicator in content for indicator in html_indicators):
                print(f"❌ ERROR: HTML content found in {filepath}")
                return False

            # Validate Python syntax
            ast.parse(content)
            print(f"✅ {filepath} is valid")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {filepath}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating {filepath}: {e}")
        return False

if __name__ == "__main__":
    critical_files = [
        'main.py',
        'database.py',
        'models.py',
        'schemas.py',
        'routers/auth.py',
        'routers/conversation.py',
        'routers/children.py',
        'routers/dashboard.py',
    ]

    print("🔍 Validating Python files...")
    all_valid = True

    for file in critical_files:
        if Path(file).exists():
            if not validate_python_file(file):
                all_valid = False
        else:
            print(f"⚠️  Warning: {file} not found")

    if all_valid:
        print("\n✅ All files validated successfully!")
        sys.exit(0)
    else:
        print("\n❌ Validation failed! Fix errors before deploying.")
        sys.exit(1)
