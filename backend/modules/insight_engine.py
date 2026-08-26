"""Insight rule engine.

Setiap insight dihasilkan dari kondisi logis atas output statistical_engine,
lalu dirender ke kalimat lewat template + interpolasi angka. Tidak ada
model bahasa generatif di sini sama sekali — murni if/else + string format.
Tiap insight diberi skor prioritas biar yang paling signifikan tampil duluan.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Insight:
    text: str
    priority: float  # makin tinggi makin signifikan / layak diprioritaskan
    category: str


def insights_from_correlation(results: list[dict]) -> list[Insight]:
    insights = []
    for r in results:
        if r["p_value"] is None or r["p_value"] >= 0.05:
            continue
        strength = abs(r["r"])
        if strength >= 0.7:
            label = "kuat"
        elif strength >= 0.4:
            label = "moderat"
        else:
            continue  # korelasi lemah dianggap belum cukup menarik jadi insight
        arah = "positif" if r["r"] > 0 else "negatif"
        text = (
            f"Korelasi {label} {arah} antara '{r['var_x']}' dan '{r['var_y']}' "
            f"({r['method']}, r={r['r']:.2f}, p={r['p_value']:.3f})."
        )
        insights.append(Insight(text=text, priority=strength, category="korelasi"))
    return insights


def insights_from_group_comparison(result: dict) -> list[Insight]:
    if not result.get("method") or not result.get("significant"):
        return []
    text = (
        f"Rata-rata '{result['numeric_col']}' berbeda signifikan antar kelompok "
        f"'{result['group_col']}' ({result['method']}, p={result['p_value']:.3f})."
    )
    priority = 1 - result["p_value"]
    return [Insight(text=text, priority=priority, category="perbandingan_grup")]


def insights_from_outliers(outlier_summary: dict) -> list[Insight]:
    insights = []
    for col, info in outlier_summary.items():
        if info["pct_outliers"] < 1:
            continue
        text = (
            f"Kolom '{col}' memiliki {info['n_outliers']} outlier "
            f"({info['pct_outliers']:.1f}% dari data), perlu dicek lebih lanjut."
        )
        insights.append(Insight(text=text, priority=info["pct_outliers"] / 100, category="outlier"))
    return insights


def insights_from_missing(profiling: dict, threshold: float = 20.0) -> list[Insight]:
    insights = []
    for col, info in profiling.items():
        if info.get("missing_pct", 0) >= threshold:
            text = f"Kolom '{col}' memiliki {info['missing_pct']:.1f}% data hilang."
            insights.append(Insight(text=text, priority=info["missing_pct"] / 100, category="missing_data"))
    return insights


def insights_from_association(results: list[dict]) -> list[Insight]:
    """Dari uji Chi-square + Cramer's V antar kolom kategorikal."""
    insights = []
    for r in results:
        if r["p_value"] is None or r["p_value"] >= 0.05:
            continue
        v = r.get("cramers_v") or 0.0
        if v < 0.2:
            continue  # asosiasi terlalu lemah buat dianggap menarik
        strength = "kuat" if v >= 0.5 else "moderat"
        text = (
            f"Asosiasi {strength} antara '{r['var_x']}' dan '{r['var_y']}' "
            f"(Cramer's V={v:.2f}, p={r['p_value']:.3f})."
        )
        insights.append(Insight(text=text, priority=v, category="asosiasi_kategorikal"))
    return insights


def insights_from_regression(result: dict) -> list[Insight]:
    """Dari hasil linear_regression atau logistic_regression di modules/regression.py."""
    if not result.get("method"):
        return []
    sig_predictors = [name for name, info in result["coefficients"].items() if info["significant"]]
    if not sig_predictors:
        return []

    if result["method"] == "linear_regression":
        text = (
            f"'{result['target']}' berhubungan signifikan dengan {', '.join(sig_predictors)} "
            f"lewat regresi linear (R²={result['r_squared']:.2f})."
        )
        priority = result["r_squared"]
    else:
        text = (
            f"'{result['target']}' berhubungan signifikan dengan {', '.join(sig_predictors)} "
            f"lewat regresi logistik (pseudo-R²={result['pseudo_r_squared']:.2f})."
        )
        priority = result["pseudo_r_squared"]

    return [Insight(text=text, priority=priority, category="regresi")]


def insights_from_clustering(result: dict) -> list[Insight]:
    """Dari hasil hierarchical_clustering di modules/clustering.py."""
    if not result.get("method") or result.get("silhouette_score", -1) < 0.25:
        return []  # silhouette rendah = pemisahan cluster nggak cukup meyakinkan
    cols_preview = ", ".join(result["columns"][:3])
    text = (
        f"Data terbagi jadi {result['n_clusters']} kelompok alami berdasarkan "
        f"{cols_preview} (silhouette score={result['silhouette_score']:.2f})."
    )
    return [Insight(text=text, priority=result["silhouette_score"], category="clustering")]


def insights_from_pca(result: dict) -> list[Insight]:
    """Dari hasil pca_analysis di modules/multivariate.py."""
    if not result.get("method"):
        return []
    text = (
        f"{result['n_components']} komponen utama sudah menjelaskan "
        f"{result['cumulative_variance_pct']:.0f}% variasi dari {len(result['columns'])} variabel numerik."
    )
    return [Insight(text=text, priority=result["cumulative_variance_pct"] / 100, category="multivariat")]


def rank_insights(all_insights: list[Insight], top_n: int | None = None) -> list[Insight]:
    ranked = sorted(all_insights, key=lambda i: i.priority, reverse=True)
    return ranked[:top_n] if top_n else ranked
