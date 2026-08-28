"""Clustering statistik klasik (hierarchical clustering), bukan model ML
prediktif -- ini metode unsupervised yang sudah lama ada di statistik
multivariat, dipakai buat nemuin pengelompokan alami dalam data.

Pakai scipy buat linkage-nya. Silhouette score dihitung manual pakai numpy
(bukan scikit-learn) biar tetap konsisten sama stack yang ada.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAX_ROWS_FOR_CLUSTERING = 2000  # jaga performa -- silhouette itu O(n^2)


def _silhouette_score(dist_matrix: np.ndarray, labels: np.ndarray) -> float:
    """Rata-rata silhouette coefficient semua titik. Range -1 s/d 1, makin
    tinggi makin jelas pemisahan antar cluster-nya.
    """
    n = len(labels)
    unique_labels = np.unique(labels)
    if len(unique_labels) < 2:
        return -1.0

    scores = np.zeros(n)
    for i in range(n):
        same_cluster = labels == labels[i]
        same_cluster[i] = False
        if not same_cluster.any():
            scores[i] = 0.0
            continue
        a = dist_matrix[i, same_cluster].mean()  # jarak rata2 ke cluster sendiri
        b = np.inf  # jarak rata2 ke cluster tetangga terdekat
        for lbl in unique_labels:
            if lbl == labels[i]:
                continue
            other_cluster = labels == lbl
            b = min(b, dist_matrix[i, other_cluster].mean())
        scores[i] = (b - a) / max(a, b) if max(a, b) > 0 else 0.0
    return float(scores.mean())


def hierarchical_clustering(df: pd.DataFrame, columns: list[str], max_k: int = 6) -> dict:
    from scipy.cluster.hierarchy import fcluster, linkage  # lazy import, jaga memory startup
    from scipy.spatial.distance import pdist, squareform

    data = df[columns].dropna()
    if len(data) < 10:
        return {"method": None}
    if len(data) > MAX_ROWS_FOR_CLUSTERING:
        data = data.sample(MAX_ROWS_FOR_CLUSTERING, random_state=42)

    X = data.to_numpy()
    std = X.std(axis=0)
    std[std == 0] = 1.0  # cegah divide-by-zero buat kolom konstan
    X_std = (X - X.mean(axis=0)) / std  # WAJIB standardisasi biar skala variabel adil

    dist_matrix = squareform(pdist(X_std))
    Z = linkage(X_std, method="ward")

    best_k, best_score = 2, -1.0
    upper_k = min(max_k, len(data) - 1)
    for k in range(2, upper_k + 1):
        labels = fcluster(Z, k, criterion="maxclust")
        score = _silhouette_score(dist_matrix, labels)
        if score > best_score:
            best_k, best_score = k, score

    final_labels = fcluster(Z, best_k, criterion="maxclust")
    profiles = {}
    for cluster_id in np.unique(final_labels):
        mask = final_labels == cluster_id
        profiles[int(cluster_id)] = {
            "n_members": int(mask.sum()),
            "pct": float(mask.mean() * 100),
            "mean_values": {col: float(data[col].to_numpy()[mask].mean()) for col in columns},
        }

    return {
        "method": "hierarchical_clustering",
        "n_clusters": best_k,
        "silhouette_score": best_score,
        "columns": columns,
        "profiles": profiles,
        "n": len(data),
    }
