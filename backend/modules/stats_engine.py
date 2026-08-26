"""Statistical engine.

Semua uji di sini murni scipy/numpy — tidak ada panggilan API eksternal.
Metode uji dipilih otomatis berdasarkan hasil uji asumsi (normalitas),
bukan di-hardcode, supaya hasilnya tetap valid secara metodologis.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats


def test_normality(series: pd.Series, alpha: float = 0.05) -> dict:
    """Uji Shapiro-Wilk. Untuk n besar (>5000) pakai subsample biar stabil."""
    clean = series.dropna()
    if len(clean) < 3:
        return {"is_normal": None, "p_value": None, "test": "shapiro"}
    sample = clean.sample(5000, random_state=42) if len(clean) > 5000 else clean
    stat, p = stats.shapiro(sample)
    return {"is_normal": bool(p > alpha), "p_value": float(p), "test": "shapiro"}


def correlation_pair(x: pd.Series, y: pd.Series, alpha: float = 0.05) -> dict:
    """Uji korelasi 2 variabel numerik.

    Pearson kalau keduanya lolos uji normalitas, Spearman kalau tidak.
    """
    paired = pd.concat([x, y], axis=1).dropna()
    if len(paired) < 3:
        return {"method": None, "r": None, "p_value": None}
    x_normal = test_normality(paired.iloc[:, 0], alpha)["is_normal"]
    y_normal = test_normality(paired.iloc[:, 1], alpha)["is_normal"]
    if x_normal and y_normal:
        r, p = stats.pearsonr(paired.iloc[:, 0], paired.iloc[:, 1])
        method = "pearson"
    else:
        r, p = stats.spearmanr(paired.iloc[:, 0], paired.iloc[:, 1])
        method = "spearman"
    return {"method": method, "r": float(r), "p_value": float(p), "n": len(paired)}


def correlation_matrix(df: pd.DataFrame, numeric_cols: list[str], alpha: float = 0.05) -> list[dict]:
    """Uji korelasi untuk semua pasangan kolom numerik."""
    results = []
    for col_x, col_y in combinations(numeric_cols, 2):
        res = correlation_pair(df[col_x], df[col_y], alpha)
        if res["method"] is not None:
            res.update({"var_x": col_x, "var_y": col_y})
            results.append(res)
    return results


def compare_groups(df: pd.DataFrame, numeric_col: str, group_col: str, alpha: float = 0.05) -> dict:
    """Uji beda numeric_col antar kategori group_col.

    Auto-pilih: 2 grup -> Welch t-test / Mann-Whitney U;
    >2 grup -> ANOVA / Kruskal-Wallis — tergantung normalitas tiap grup.
    """
    grouped = df.groupby(group_col)[numeric_col]
    groups, labels = [], []
    for name, g in grouped:
        clean = g.dropna()
        if len(clean) >= 3:
            groups.append(clean.values)
            labels.append(name)

    if len(groups) < 2:
        return {"method": None}

    all_normal = all(test_normality(pd.Series(g), alpha)["is_normal"] for g in groups)

    if len(groups) == 2:
        if all_normal:
            stat, p = stats.ttest_ind(groups[0], groups[1], equal_var=False)
            method = "welch_t_test"
        else:
            stat, p = stats.mannwhitneyu(groups[0], groups[1])
            method = "mann_whitney_u"
    else:
        if all_normal:
            stat, p = stats.f_oneway(*groups)
            method = "anova"
        else:
            stat, p = stats.kruskal(*groups)
            method = "kruskal_wallis"

    return {
        "method": method,
        "statistic": float(stat),
        "p_value": float(p),
        "significant": bool(p < alpha),
        "groups": labels,
        "numeric_col": numeric_col,
        "group_col": group_col,
    }


def association_categorical(x: pd.Series, y: pd.Series) -> dict:
    """Uji asosiasi 2 variabel kategorikal: Chi-square (signifikansi) + Cramer's V
    (kekuatan asosiasi, 0-1, biar bisa dibandingin sama korelasi numerik).
    """
    paired = pd.concat([x, y], axis=1).dropna()
    if len(paired) < 5:
        return {"method": None}
    table = pd.crosstab(paired.iloc[:, 0], paired.iloc[:, 1])
    if table.shape[0] < 2 or table.shape[1] < 2:
        return {"method": None}
    chi2, p, _, _ = stats.chi2_contingency(table)
    n = table.to_numpy().sum()
    min_dim = min(table.shape) - 1
    cramers_v = float((chi2 / (n * min_dim)) ** 0.5) if min_dim > 0 else None
    return {
        "method": "chi_square",
        "chi2": float(chi2),
        "p_value": float(p),
        "cramers_v": cramers_v,
        "n": int(n),
    }


def association_matrix(df: pd.DataFrame, categorical_cols: list[str]) -> list[dict]:
    """Uji asosiasi untuk semua pasangan kolom kategorikal."""
    results = []
    for col_x, col_y in combinations(categorical_cols, 2):
        res = association_categorical(df[col_x], df[col_y])
        if res["method"] is not None:
            res.update({"var_x": col_x, "var_y": col_y})
            results.append(res)
    return results


def compute_vif(df: pd.DataFrame, numeric_cols: list[str]) -> dict[str, float]:
    """Variance Inflation Factor tiap kolom numerik -- indikator multikolinearitas.

    Dihitung manual dari R^2 regresi kolom itu terhadap kolom numerik lainnya
    (VIF = 1 / (1 - R^2)), pakai numpy least-squares -- nggak butuh statsmodels
    cuma buat ini. VIF > 5 biasanya dianggap tanda multikolinearitas tinggi.
    """
    clean = df[numeric_cols].dropna()
    if len(numeric_cols) < 2 or len(clean) < len(numeric_cols) + 2:
        return {}
    vif = {}
    for col in numeric_cols:
        others = [c for c in numeric_cols if c != col]
        X = clean[others].to_numpy()
        y = clean[col].to_numpy()
        X_design = np.column_stack([np.ones(len(X)), X])
        try:
            coef, *_ = np.linalg.lstsq(X_design, y, rcond=None)
        except np.linalg.LinAlgError:
            continue
        y_pred = X_design @ coef
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        vif[col] = float("inf") if r2 >= 0.999 else float(1 / (1 - r2))
    return vif
