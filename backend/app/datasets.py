"""Endpoint dataset: upload, trigger analisis, ambil hasil insight.

Semua endpoint di sini butuh login (lewat get_current_user), dan tiap
user cuma bisa akses dataset miliknya sendiri -- dicek manual di
_get_owned_dataset, bukan cuma diasumsikan dari ID.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from modules.clustering import hierarchical_clustering
from modules.data_loader import detect_column_types, load_data, validate_data
from modules.insight_engine import (
    insights_from_association,
    insights_from_clustering,
    insights_from_correlation,
    insights_from_group_comparison,
    insights_from_missing,
    insights_from_outliers,
    insights_from_pca,
    insights_from_regression,
    rank_insights,
)
from modules.multivariate import pca_analysis
from modules.profiling import descriptive_stats, outlier_summary
from modules.recommender import recommend_analyses
from modules.regression import linear_regression, logistic_regression
from modules.stats_engine import (
    association_matrix,
    compare_groups,
    compute_vif,
    correlation_matrix,
)

# Batasin jumlah analisis lanjutan (regresi/clustering/PCA) yang auto-dijalanin
# per dataset -- biar tetap cepat & fokus ke yang paling relevan aja, konsisten
# sama filosofi top_n di rank_insights.
MAX_ADVANCED_ANALYSES = 2

from .auth import get_current_user
from .database import get_db
from .limiter import limiter
from .models import Dataset, Insight, User
from .schemas import DatasetOut, InsightOut
from .storage import save_upload

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def upload_dataset(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        file_path, size_bytes = save_upload(file, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    dataset = Dataset(
        filename=file.filename,
        file_path=file_path,
        size_bytes=size_bytes,
        status="uploaded",
        owner_id=current_user.id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def _get_owned_dataset(dataset_id: int, current_user: User, db: Session) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if dataset is None or dataset.owner_id != current_user.id:
        # sengaja 404, bukan 403 -- biar orang lain nggak bisa nebak-nebak
        # ID mana yang valid tapi bukan punya dia
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan")
    return dataset


@router.post("/{dataset_id}/analyze", response_model=list[InsightOut])
@limiter.limit("10/minute")
def analyze_dataset(
    request: Request,
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = _get_owned_dataset(dataset_id, current_user, db)

    dataset.status = "processing"
    db.commit()

    try:
        df = load_data(dataset.file_path)
        validate_data(df)
        col_types = detect_column_types(df)
        numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
        categorical_cols = [c for c, t in col_types.items() if t == "categorical"]

        profiling = descriptive_stats(df, col_types)
        outliers = outlier_summary(df, col_types)

        all_insights = []
        all_insights += insights_from_missing(profiling)
        all_insights += insights_from_outliers(outliers)

        # -- Tahap 1: EDA --
        corr_results: list[dict] = []
        if len(numeric_cols) >= 2:
            corr_results = correlation_matrix(df, numeric_cols)
            all_insights += insights_from_correlation(corr_results)

        if len(categorical_cols) >= 2:
            assoc_results = association_matrix(df, categorical_cols)
            all_insights += insights_from_association(assoc_results)

        for num_col in numeric_cols[:5]:
            for cat_col in categorical_cols[:3]:
                n_groups = df[cat_col].nunique()
                if n_groups < 2 or n_groups > 10:
                    continue
                result = compare_groups(df, num_col, cat_col)
                all_insights += insights_from_group_comparison(result)

        vif = compute_vif(df, numeric_cols) if len(numeric_cols) >= 2 else {}
        binary_categoricals = [c for c in categorical_cols if df[c].nunique(dropna=True) == 2]

        # -- Tahap 2: rekomendasi analisis lanjutan (rule-based, baca hasil EDA) --
        recommendations = recommend_analyses(
            numeric_cols=numeric_cols,
            categorical_cols=categorical_cols,
            n_rows=len(df),
            corr_results=corr_results,
            vif=vif,
            binary_categoricals=binary_categoricals,
        )

        # -- Tahap 3: auto-jalanin analisis lanjutan paling relevan --
        for rec in recommendations[:MAX_ADVANCED_ANALYSES]:
            if rec.method == "regression":
                result = linear_regression(df, rec.params["target"], [rec.params["predictor"]])
                all_insights += insights_from_regression(result)
            elif rec.method == "logistic_regression":
                result = logistic_regression(df, rec.params["target"], rec.params["predictors"])
                all_insights += insights_from_regression(result)
            elif rec.method == "clustering":
                result = hierarchical_clustering(df, rec.params["columns"])
                all_insights += insights_from_clustering(result)
            elif rec.method == "pca":
                result = pca_analysis(df, rec.params["columns"])
                all_insights += insights_from_pca(result)

        # -- Tahap 4: insight, sama seperti sebelumnya --
        ranked = rank_insights(all_insights, top_n=15)

        # hapus insight lama kalau dataset ini dianalisis ulang
        db.query(Insight).filter(Insight.dataset_id == dataset.id).delete()

        db_insights = [
            Insight(
                category=ins.category,
                text=ins.text,
                priority=ins.priority,
                dataset_id=dataset.id,
            )
            for ins in ranked
        ]
        db.add_all(db_insights)
        dataset.status = "done"
        db.commit()

    except Exception:
        dataset.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail="Gagal memproses dataset")

    db.refresh(dataset)
    return dataset.insights


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(Dataset).filter(Dataset.owner_id == current_user.id).all()


@router.get("/{dataset_id}/insights", response_model=list[InsightOut])
def get_insights(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = _get_owned_dataset(dataset_id, current_user, db)
    return dataset.insights
