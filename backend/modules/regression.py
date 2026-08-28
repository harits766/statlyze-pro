"""Regresi statistik (statistical inference, bukan predictive ML).

Fokusnya ke koefisien, p-value, dan R^2 -- bukan cuma akurasi prediksi kayak
di machine learning. Pakai statsmodels biar dapet output inferensial lengkap
(standard error, p-value tiap koefisien) yang scikit-learn nggak kasih
langsung.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def linear_regression(df: pd.DataFrame, target: str, predictors: list[str]) -> dict:
    """OLS: target dan semua predictors harus numerik."""
    import statsmodels.api as sm  # lazy import -- statsmodels berat, cuma di-load pas beneran dipakai

    data = df[[target] + predictors].dropna()
    if len(data) < len(predictors) + 5:
        return {"method": None}

    X = sm.add_constant(data[predictors])
    y = data[target]
    model = sm.OLS(y, X).fit()

    coefficients = {
        name: {
            "coef": float(model.params[name]),
            "p_value": float(model.pvalues[name]),
            "significant": bool(model.pvalues[name] < 0.05),
        }
        for name in predictors
    }

    return {
        "method": "linear_regression",
        "target": target,
        "predictors": predictors,
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "coefficients": coefficients,
        "n": len(data),
    }


def logistic_regression(df: pd.DataFrame, target: str, predictors: list[str]) -> dict:
    """Regresi logistik biner: target harus kategorikal dengan tepat 2 kelas."""
    import statsmodels.api as sm  # lazy import -- sama alasannya kayak di linear_regression

    data = df[[target] + predictors].dropna()
    if len(data) < len(predictors) + 10:
        return {"method": None}

    categories = data[target].unique()
    if len(categories) != 2:
        return {"method": None}

    reference_class = categories[0]
    y = (data[target] == reference_class).astype(int)
    X = sm.add_constant(data[predictors])

    try:
        model = sm.Logit(y, X).fit(disp=0)
    except Exception:
        return {"method": None}

    coefficients = {
        name: {
            "coef": float(model.params[name]),
            "odds_ratio": float(np.exp(model.params[name])),
            "p_value": float(model.pvalues[name]),
            "significant": bool(model.pvalues[name] < 0.05),
        }
        for name in predictors
    }

    return {
        "method": "logistic_regression",
        "target": target,
        "reference_class": str(reference_class),
        "predictors": predictors,
        "pseudo_r_squared": float(model.prsquared),
        "coefficients": coefficients,
        "n": len(data),
    }
