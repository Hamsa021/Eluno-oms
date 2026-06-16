"""
Optional: train a real ML model for breach prediction once you have historical
order data (or synthetic data to start). Run this script standalone:

    python -m app.services.train_model

It writes tat_model.joblib, which tat_predictor.py will auto-load on next
backend restart.

Replace `generate_synthetic_data()` with a real query against your `orders`
table (filtered to delivered/cancelled orders so the breach label is known)
once you have enough history (recommend 200+ rows minimum).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib


def generate_synthetic_data(n=2000, seed=42):
    rng = np.random.default_rng(seed)

    lens_sla = {0: 24, 1: 48, 2: 72, 3: 24}  # index maps to LensType enum order
    lens_type = rng.integers(0, 4, n)
    total_sla = np.array([lens_sla[t] for t in lens_type])

    in_house = rng.integers(0, 2, n)
    qc_fail_count = rng.poisson(0.3, n)
    stage_idx = rng.integers(0, 7, n)  # 0..6 across the 7 pre-delivery stages

    # elapsed time correlates with stage, in_house, qc fails + noise
    base_progress = stage_idx / 6
    elapsed = (
        base_progress * total_sla
        + (1 - in_house) * rng.normal(8, 3, n)
        + qc_fail_count * rng.normal(20, 5, n)
        + rng.normal(0, 4, n)
    )
    elapsed = np.clip(elapsed, 0, None)

    time_ratio = elapsed / total_sla

    # breach label: ground truth simulated as elapsed exceeding SLA at delivery,
    # in a real dataset this comes from actual delivered_at vs sla_deadline
    breach_prob = 1 / (1 + np.exp(-(time_ratio - 0.85) * 6 - qc_fail_count * 0.5 - (1 - in_house) * 0.3))
    breach = rng.binomial(1, breach_prob)

    df = pd.DataFrame({
        "elapsed_hours": elapsed,
        "total_sla_hours": total_sla,
        "time_ratio": time_ratio,
        "in_house": in_house,
        "qc_fail_count": qc_fail_count,
        "stage_idx": stage_idx,
        "breach": breach,
    })
    return df


def main():
    df = generate_synthetic_data()
    X = df[["elapsed_hours", "total_sla_hours", "time_ratio", "in_house", "qc_fail_count", "stage_idx"]]
    y = df["breach"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds))

    joblib.dump(model, "app/services/tat_model.joblib")
    print("Saved model to app/services/tat_model.joblib")


if __name__ == "__main__":
    main()
