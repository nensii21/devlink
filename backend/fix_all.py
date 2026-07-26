import glob
import re

for filepath in glob.glob("tests/test_*.py") + glob.glob("app/tests/test_*.py"):
    with open(filepath, "r") as f:
        content = f.read()
    
    original = content
    
    # 1. Remove local engine creation
    content = re.sub(
        r'engine = create_engine\(\s*"sqlite://(?:/:memory:)?",\s*connect_args={"check_same_thread": False},\s*poolclass=StaticPool,?\s*\)\n?',
        '',
        content,
        flags=re.MULTILINE
    )
    
    # 2. Replace TestingSessionLocal assignment with import
    content = re.sub(
        r'TestingSessionLocal = sessionmaker\([^\)]*\)\n?',
        'from tests.conftest import TestingSessionLocal\n',
        content,
        flags=re.MULTILINE
    )
    
    # 3. Remove local override_get_db
    content = re.sub(
        r'def override_get_db\(\):.*?finally:\s+db\.close\(\)\n+',
        '',
        content,
        flags=re.DOTALL
    )
    
    # 4. Remove local setup_db
    content = re.sub(
        r'@pytest\.fixture\(autouse=True\)\ndef setup_db\(\):.*?app\.dependency_overrides\.clear\(\)\n+',
        '',
        content,
        flags=re.DOTALL
    )
    
    # 5. Remove test_last_seen.py specific setup_db which doesn't clear
    content = re.sub(
        r'@pytest\.fixture\(autouse=True\)\ndef setup_db\(\):\n\s+app\.dependency_overrides\[get_database\] = override_get_db\n\s+Base\.metadata\.create_all\(bind=engine\)\n+',
        '',
        content,
        flags=re.DOTALL
    )

    if original != content:
        with open(filepath, "w") as f:
            f.write(content)
            print(f"Fixed {filepath}")

