from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from jose import jwt
from pydantic import BaseModel, EmailStr
from typing import Optional
import os

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"

# Schemas
class ParentCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class ParentLogin(BaseModel):
    email: EmailStr
    password: str

class ChildCreate(BaseModel):
    first_name: str
    nickname: Optional[str] = None
    date_of_birth: str
    grade_level: str
    pin: str
    preferred_language: Optional[str] = "en"

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain[:72], hashed)

def create_token(parent_id: int) -> str:
    return jwt.encode({"sub": str(parent_id)}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_parent_id(authorization: Optional[str] = Header(None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401)

# Routes
@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/api/v1/auth/parent/register")
def register(parent: ParentCreate, db: Session = Depends(get_db)):
    existing = db.execute(f"SELECT id FROM parents WHERE email='{parent.email}'").fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email exists")

    hashed = get_password_hash(parent.password)
    result = db.execute(
        f"INSERT INTO parents (email, full_name, hashed_password) VALUES ('{parent.email}', '{parent.full_name}', '{hashed}') RETURNING id"
    )
    db.commit()
    parent_id = result.fetchone()[0]

    return {
        "access_token": create_token(parent_id),
        "token_type": "bearer",
        "parent_id": parent_id,
        "email": parent.email,
        "full_name": parent.full_name
    }

@app.post("/api/v1/auth/parent/login")
def login(creds: ParentLogin, db: Session = Depends(get_db)):
    result = db.execute(f"SELECT id, hashed_password, full_name FROM parents WHERE email='{creds.email}'").fetchone()
    if not result or not verify_password(creds.password, result[1]):
        raise HTTPException(status_code=401)

    return {
        "access_token": create_token(result[0]),
        "token_type": "bearer",
        "parent_id": result[0],
        "email": creds.email,
        "full_name": result[2]
    }

@app.post("/api/v1/children/")
def create_child(
    child: ChildCreate,
    db: Session = Depends(get_db),
    parent_id: int = Depends(get_current_parent_id)
):
    hashed_pin = get_password_hash(child.pin)
    result = db.execute(f"""
        INSERT INTO children (parent_id, first_name, nickname, date_of_birth, grade_level, hashed_pin, preferred_language)
        VALUES ({parent_id}, '{child.first_name}', '{child.nickname}', '{child.date_of_birth}', '{child.grade_level}', '{hashed_pin}', '{child.preferred_language}')
        RETURNING id, parent_id, first_name, nickname, grade_level, created_at
    """)
    db.commit()
    row = result.fetchone()

    return {
        "id": row[0],
        "parent_id": row[1],
        "first_name": row[2],
        "nickname": row[3],
        "grade_level": row[4],
        "created_at": row[5]
    }

@app.get("/api/v1/children/")
def get_children(db: Session = Depends(get_db), parent_id: int = Depends(get_current_parent_id)):
    result = db.execute(f"SELECT id, parent_id, first_name, nickname, grade_level, created_at FROM children WHERE parent_id={parent_id}")
    children = []
    for row in result:
        children.append({
            "id": row[0],
            "parent_id": row[1],
            "first_name": row[2],
            "nickname": row[3],
            "grade_level": row[4],
            "created_at": row[5]
        })
    return children
