"""Pydantic schemas: bentuk data yang masuk (request) & keluar (response) API.

Ini beda sama models.py (SQLAlchemy) -- models.py itu bentuk tabel di
database, schemas.py ini bentuk JSON yang dilihat/dikirim user lewat API.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        return v


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DatasetOut(BaseModel):
    id: int
    filename: str
    status: str
    size_bytes: int | None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsightOut(BaseModel):
    id: int
    category: str
    text: str
    priority: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
