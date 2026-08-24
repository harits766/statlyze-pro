"""Modul profiling otomatis: descriptive stats, missing value, outlier."""
from __future__ import annotations

import pandas as pd


def descriptive_stats(df: pd.DataFrame, col_types: dict[str, str]) -> dict:
    """Statistik deskriptif per kolom, disesuaikan tipe datanya."""
    result = {}
    for col, ctype in col_types.items():
        series = df[col].dropna()
        if ctype == "numeric":
            result[col] = {
                "type": "numeric",
                "mean": float(series.mean()) if len(series) else None,
                "median": float(series.median()) if len(series) else None,
                "std": float(series.std()) if len(series) > 1 else None,
                "min": float(series.min()) if len(series) else None,
                "max": float(series.max()) if len(series) else None,
                "skewness": float(series.skew()) if len(series) > 2 else None,
                "kurtosis": float(series.kurt()) if len(series) > 3 else None,
                "missing_pct": float(df[col].isna().mean() * 100),
            }
        elif ctype == "categorical":
            freq = series.value_counts(normalize=True).head(5)
            result[col] = {
                "type": "categorical",
                "n_unique": int(series.nunique()),
                "top_categories": freq.round(4).to_dict(),
                "missing_pct": float(df[col].isna().mean() * 100),
            }
        else:
            result[col] = {
                "type": ctype,
                "missing_pct": float(df[col].isna().mean() * 100),
            }
    return result


def detect_outliers_iqr(series: pd.Series) -> pd.Series:
    """Deteksi outlier numerik pakai metode IQR, return boolean mask."""
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return (series < lower) | (series > upper)


def outlier_summary(df: pd.DataFrame, col_types: dict[str, str]) -> dict:
    """Ringkasan jumlah & persentase outlier per kolom numerik (metode IQR)."""
    summary = {}
    for col, ctype in col_types.items():
        if ctype != "numeric":
            continue
        series = df[col].dropna()
        if len(series) < 4:
            continue
        mask = detect_outliers_iqr(series)
        if mask.sum() > 0:
            summary[col] = {
                "n_outliers": int(mask.sum()),
                "pct_outliers": float(mask.mean() * 100),
            }
    return summary
