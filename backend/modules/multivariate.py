"""Analisis multivariat: PCA (Principal Component Analysis).

Diimplementasi manual pakai numpy (eigen-decomposition matriks kovarians),
BUKAN scikit-learn -- konsisten sama prinsip proyek: komputasi lokal murni
matematis, tanpa dependency machine learning tambahan buat hal yang secara
matematis straightforward dihitung langsung.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def pca_analysis(df: pd.DataFrame, columns: list[str], variance_threshold: float = 0.8) -> dict:
    data = df[columns].dropna()
    if len(data) < len(columns) + 2 or len(columns) < 2:
        return {"method": None}

    X = data.to_numpy()
    std = X.std(axis=0)
    std[std == 0] = 1.0
    X_std = (X - X.mean(axis=0)) / std  # standardisasi wajib -- PCA sensitif skala

    cov_matrix = np.cov(X_std, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

    # eigh urutin ascending, kita mau descending (komponen paling penting duluan)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    total_variance = eigenvalues.sum()
    if total_variance <= 0:
        return {"method": None}
    explained_ratio = eigenvalues / total_variance
    cumulative = np.cumsum(explained_ratio)

    n_components = int(np.searchsorted(cumulative, variance_threshold) + 1)
    n_components = max(1, min(n_components, len(columns)))

    components = {}
    for i in range(n_components):
        top_loadings = sorted(
            zip(columns, eigenvectors[:, i].tolist()),
            key=lambda pair: abs(pair[1]),
            reverse=True,
        )[:3]
        components[f"PC{i + 1}"] = {
            "explained_variance_pct": float(explained_ratio[i] * 100),
            "top_loadings": [{"variable": name, "loading": round(val, 3)} for name, val in top_loadings],
        }

    return {
        "method": "pca",
        "columns": columns,
        "n_components": n_components,
        "cumulative_variance_pct": float(cumulative[n_components - 1] * 100),
        "components": components,
        "n": len(data),
    }
