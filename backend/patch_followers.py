with open("app/routers/followers.py", "r") as f:
    content = f.read()

content = content.replace("    except Exception:\n        db.rollback()", "    except Exception as e:\n        print(f'ENQUEUE ERROR: {e}')\n        db.rollback()")

with open("app/routers/followers.py", "w") as f:
    f.write(content)
