import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine("sqlite:///:memory:", poolclass=StaticPool, connect_args={"check_same_thread": False})
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)

Base.metadata.create_all(engine)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

app = FastAPI()

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.close()

@app.post("/")
def create_user(db = Depends(override_get_db)):
    u = User(name="test")
    db.add(u)
    return {"id": 1}

@app.get("/")
def get_user(db = Depends(override_get_db)):
    u = db.query(User).first()
    return {"name": u.name if u else None}

def test_fastapi():
    client = TestClient(app)
    client.post("/")
    r = client.get("/")
    print("USER IS:", r.json())

if __name__ == "__main__":
    test_fastapi()
