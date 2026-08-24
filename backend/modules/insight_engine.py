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


def rank_insights(all_insights: list[Insight], top_n: int | None = None) -> list[Insight]:
    ranked = sorted(all_insights, key=lambda i: i.priority, reverse=True)
    return ranked[:top_n] if top_n else ranked
