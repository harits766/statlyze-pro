"""Modul upload & validasi data."""
from __future__ import annotations

import warnings

import pandas as pd


def load_data(file) -> pd.DataFrame:
    """Load CSV atau Excel jadi DataFrame, auto-detect format dari nama file."""
    name = getattr(file, "name", str(file)).lower()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)
    return df


def detect_column_types(df: pd.DataFrame) -> dict[str, str]:
    """Deteksi tipe tiap kolom: numeric, categorical, datetime, atau text."""
    types = {}
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            types[col] = "numeric"
            continue
        if pd.api.types.is_datetime64_any_dtype(series):
            types[col] = "datetime"
            continue
        # coba parse sebagai datetime sebelum dianggap kategorik/teks
        try:
            sample = series.dropna().head(20)
            if len(sample) > 0:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    pd.to_datetime(sample, errors="raise")
                types[col] = "datetime"
                continue
        except (ValueError, TypeError):
            pass
        n_unique = series.nunique(dropna=True)
        n_total = len(series.dropna())
        if n_total > 0 and n_unique / n_total < 0.5 and n_unique <= 50:
            types[col] = "categorical"
        else:
            types[col] = "text"
    return types


def validate_data(df: pd.DataFrame) -> list[str]:
    """Validasi ringan, kembalikan list warning (bukan exception)."""
    warnings = []
    if df.empty:
        warnings.append("Dataset kosong.")
        return warnings
    n_dup = int(df.duplicated().sum())
    if n_dup > 0:
        warnings.append(f"Ditemukan {n_dup} baris duplikat.")
    fully_empty_cols = df.columns[df.isna().all()].tolist()
    if fully_empty_cols:
        warnings.append(f"Kolom kosong total: {', '.join(fully_empty_cols)}")
    return warnings
