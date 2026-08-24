"""Statistical engine.

Semua uji di sini murni scipy/numpy — tidak ada panggilan API eksternal.
Metode uji dipilih otomatis berdasarkan hasil uji asumsi (normalitas),
bukan di-hardcode, supaya hasilnya tetap valid secara metodologis.
"""
from __future__ import annotations

from itertools import combinations

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
