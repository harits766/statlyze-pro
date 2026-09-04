"""Dependency FastAPI: validasi token dari header Authorization, lalu
ambil user yang lagi login. Dipakai di endpoint mana pun yang butuh login,
tinggal tambahin parameter `current_user: User = Depends(get_current_user)`.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_access_token

# tokenUrl cuma buat dokumentasi Swagger, nunjukkin endpoint mana buat dapetin token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    subject = payload.get("sub")
    if not subject:
        raise credentials_exception

    # Token baru isinya ID user (angka). Token lama -- yang dibikin sebelum
    # login pakai username ada -- isinya email, jadi tetap dilayani biar user
    # yang masih pegang token lama nggak tiba-tiba ke-logout.
    if subject.isdigit():
        user = db.query(User).filter(User.id == int(subject)).first()
    else:
        user = db.query(User).filter(User.email == subject.lower()).first()

    if user is None:
        raise credentials_exception
    return user
