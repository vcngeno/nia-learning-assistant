from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
import secrets
import time

# Password hashing context - FIXED for bcrypt compatibility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def generate_parent_id() -> str:
    """Generate a unique parent ID"""
    timestamp = int(time.time())
    random_suffix = secrets.token_hex(4)
    return f"parent_{timestamp}_{random_suffix}"

def generate_student_id() -> str:
    """Generate a unique student ID"""
    timestamp = int(time.time())
    random_suffix = secrets.token_hex(4)
    return f"student_{timestamp}_{random_suffix}"

def hash_pin(pin: str) -> str:
    """Hash a PIN for secure storage - truncate to 72 bytes for bcrypt"""
    # Ensure PIN is within bcrypt's 72-byte limit
    pin_bytes = pin.encode('utf-8')[:72]
    return pwd_context.hash(pin_bytes.decode('utf-8'))

def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify a PIN against its hash"""
    # Truncate to same length as when hashing
    plain_pin_bytes = plain_pin.encode('utf-8')[:72]
    return pwd_context.verify(plain_pin_bytes.decode('utf-8'), hashed_pin)

def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
