import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.database import get_user_by_user_id
from app.schemas import UserInfo

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "systematic-fallback-secret-key-1234")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request) -> UserInfo:
    token = request.cookies.get("sys_access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        print(f"JWT decode failed: {e}")
        raise credentials_exception

    user_data = get_user_by_user_id(user_id)
    if user_data is None:
        print(f"User not found in DB: {user_id}")
        raise credentials_exception

    if not user_data.get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user")

    return UserInfo(
        id=user_data["id"],
        user_id=user_data["user_id"],
        full_name=user_data["full_name"],
        role=user_data["role"],
        email=user_data.get("email"),
        feedback=user_data.get("feedback"),
        feedback_status=user_data.get("feedback_status"),
        feedback_dev_comments=user_data.get("feedback_dev_comments")
    )


async def require_admin(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
