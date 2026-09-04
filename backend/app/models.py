"""Model SQLAlchemy: User, Dataset, Insight.

Struktur relasinya:
  User (1) --- (banyak) Dataset (1) --- (banyak) Insight

Field `category`, `text`, `priority` di Insight sengaja dibikin sama
persis dengan dataclass Insight di modules/insight_engine.py -- jadi
nanti nyimpen hasil insight_engine ke database tinggal mapping 1-1,
nggak perlu transformasi data.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # username & email sama-sama unik dan sama-sama bisa dipakai buat login.
    # Keduanya disimpan dalam huruf kecil semua (dinormalisasi di schemas.py),
    # jadi "Budi" dan "budi" dianggap user yang sama -- ini penting karena
    # perbandingan string di SQLite/Postgres itu case-sensitive secara default.
    username = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    datasets = relationship(
        "Dataset", back_populates="owner", cascade="all, delete-orphan"
    )


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # lokasi file di storage, bukan isinya
    size_bytes = Column(Integer, nullable=True)
    status = Column(String, default="uploaded")  # uploaded | processing | done | failed
    uploaded_at = Column(DateTime, default=dt.datetime.utcnow)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="datasets")

    insights = relationship(
        "Insight", back_populates="dataset", cascade="all, delete-orphan"
    )


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)  # korelasi | outlier | missing_data | perbandingan_grup
    text = Column(Text, nullable=False)
    priority = Column(Float, default=0.0)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    dataset = relationship("Dataset", back_populates="insights")
