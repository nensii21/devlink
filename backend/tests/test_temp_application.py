from app.schemas.application import ApplicationCreate

try:
    a = ApplicationCreate(project_id="123", flare_id="456", message="Hello")
    print(a.project_id)
except Exception as e:
    print(f"ERROR: {type(e)} {e}")
