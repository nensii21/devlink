import glob
import re

for filepath in glob.glob("tests/test_*.py") + glob.glob("app/tests/test_*.py"):
    with open(filepath, "r") as f:
        content = f.read()

    # Look for def override_get_db():\n    db = TestingSessionLocal()\n    try:\n        yield db\n    finally:
    pattern = r'(def override_get_db\(\):\s+db = TestingSessionLocal\(\)\s+try:\s+yield db)(\s+finally:)'
    
    if re.search(pattern, content):
        content = re.sub(pattern, r'\1\n        db.commit()\2', content)
        with open(filepath, "w") as f:
            f.write(content)

