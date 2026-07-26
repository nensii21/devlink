import re
import os
import glob

def process_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # We want to remove the engine creation, TestingSessionLocal, override_get_db, setup_db, and db
    # We can do this with regexes that match the block of code.

    content = re.sub(r'engine = create_engine\(\s*"sqlite.*?poolclass=StaticPool,\n\)', '', content, flags=re.DOTALL)
    content = re.sub(r'TestingSessionLocal = sessionmaker\(bind=engine, autoflush=False, autocommit=False\)\n', '', content)

    content = re.sub(r'def override_get_db\(\):.*?finally:\n\s*db\.close\(\)\n', '', content, flags=re.DOTALL)
    
    content = re.sub(r'@pytest\.fixture\(autouse=True\)\ndef setup_db\(\):.*?app\.dependency_overrides\.clear\(\)\n', '', content, flags=re.DOTALL)

    content = re.sub(r'@pytest\.fixture\(\)\ndef db\(\):.*?finally:\n\s*session\.close\(\)\n', '', content, flags=re.DOTALL)

    # Some files use db instead of session in the db fixture
    content = re.sub(r'@pytest\.fixture\(scope="function"\)\ndef db\(\):.*?finally:\n\s*db\.close\(\)\n', '', content, flags=re.DOTALL)

    # Remove consecutive blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    with open(filepath, "w") as f:
        f.write(content)

for filepath in glob.glob("tests/test_*.py") + glob.glob("app/tests/test_*.py"):
    process_file(filepath)
