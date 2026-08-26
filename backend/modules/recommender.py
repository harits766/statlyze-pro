"""Rule-based recommender.

Baca karakteristik dataset dari hasil EDA (jumlah variabel, kekuatan korelasi,
multikolinearitas, dst) lalu rekomendasiin analisis lanjutan yang relevan.
Ini murni aturan if/else atas angka yang sudah dihitung stats_engine -- BUKAN
model machine learning, jadi keputusannya bisa dijelasin/di-trace balik ke
angka yang mendasarinya.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Recommendation:
    method: str  # "regression" | "logistic_regression" | "clustering" | "pca"
    reason: str
    priority: float
    params: dict = field(default_factory=dict)


def recommend_analyses(
    numeric_cols: list[str],
    categorical_cols: list[str],
    n_rows: int,
    corr_results: list[dict],
    vif: dict[str, float],
    binary_categoricals: list[str],
) -> list[Recommendation]:
    recs: list[Recommendation] = []

    # -- Regresi linear: ada pasangan numerik-numerik yang korelasinya kuat
    # dan cukup data buat estimasi yang stabil (aturan kasar: n >= 30).
    strong_pairs = [
        r for r in corr_results
        if r["p_value"] is not None and r["p_value"] < 0.05 and abs(r["r"]) >= 0.5
    ]
    if strong_pairs and n_rows >= 30:
        best = max(strong_pairs, key=lambda r: abs(r["r"]))
        recs.append(Recommendation(
            method="regression",
            reason=(
                f"'{best['var_x']}' dan '{best['var_y']}' berkorelasi "
                f"{'kuat' if abs(best['r']) >= 0.7 else 'moderat'} (r={best['r']:.2f}) "
                "-- berpotensi punya hubungan linear yang bisa dimodelkan lebih detail."
            ),
            priority=abs(best["r"]),
            params={"target": best["var_y"], "predictor": best["var_x"]},
        ))

    # -- Regresi logistik: ada kolom biner (cocok jadi target) + prediktor numerik.
    if binary_categoricals and numeric_cols and n_rows >= 30:
        target = binary_categoricals[0]
        recs.append(Recommendation(
            method="logistic_regression",
            reason=(
                f"Kolom '{target}' cuma punya 2 kategori -- cocok dijadikan target "
                "regresi logistik buat lihat variabel mana yang paling berpengaruh."
            ),
            priority=0.6,
            params={"target": target, "predictors": numeric_cols[:5]},
        ))

    # -- Clustering: cukup banyak variabel numerik & sample, tanpa target yang jelas.
    if len(numeric_cols) >= 3 and n_rows >= 30:
        recs.append(Recommendation(
            method="clustering",
            reason=(
                f"Ada {len(numeric_cols)} variabel numerik tanpa target yang jelas "
                "-- berpotensi ada pengelompokan alami (segmen) dalam data."
            ),
            priority=0.5,
            params={"columns": numeric_cols},
        ))

    # -- PCA: multikolinearitas tinggi (variabel saling redundan), atau cuma
    # banyak variabel numerik secara umum (tetap berguna buat ringkas pola).
    high_vif_cols = [c for c, v in vif.items() if v is not None and v > 5]
    if len(high_vif_cols) >= 2:
        recs.append(Recommendation(
            method="pca",
            reason=(
                f"Variabel {', '.join(high_vif_cols[:3])} saling berkorelasi tinggi "
                "(VIF>5) -- bisa diringkas jadi beberapa komponen utama tanpa "
                "kehilangan banyak informasi."
            ),
            priority=0.7,
            params={"columns": numeric_cols},
        ))
    elif len(numeric_cols) >= 4:
        recs.append(Recommendation(
            method="pca",
            reason=(
                f"Ada {len(numeric_cols)} variabel numerik -- PCA membantu lihat "
                "pola utama tanpa harus baca satu-satu."
            ),
            priority=0.4,
            params={"columns": numeric_cols},
        ))

    recs.sort(key=lambda r: r.priority, reverse=True)
    return recs
