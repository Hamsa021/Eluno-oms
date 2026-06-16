"""
TAT Breach Prediction (Module 3)

Two modes:
1. Heuristic (default, no training data required) - rule-based risk score using
   elapsed time vs SLA, current stage's expected time budget, in-house vs procured,
   and QC fail history.
2. ML mode (optional upgrade) - if a trained model exists at MODEL_PATH, use it
   instead. See train_model.py for how to train on historical order data.

The heuristic is the safe default for a fresh deployment with no history yet;
swap in the trained model once you've accumulated real order data.
"""
import os
from datetime import datetime
from typing import Optional

import joblib

from app.models.models import Order, OrderStatus, SLA_HOURS, STAGE_SLA_WEIGHTS

MODEL_PATH = os.getenv("TAT_MODEL_PATH", "app/services/tat_model.joblib")

_model = None
if os.path.exists(MODEL_PATH):
    try:
        _model = joblib.load(MODEL_PATH)
    except Exception:
        _model = None


def _elapsed_hours(order: Order) -> float:
    return (datetime.utcnow() - order.created_at).total_seconds() / 3600


def _expected_hours_for_stage(order: Order) -> float:
    """How many SLA-hours should have elapsed by the time an order reaches its
    current stage, under normal conditions."""
    total_sla = SLA_HOURS[order.lens_type]
    weights = STAGE_SLA_WEIGHTS
    cumulative = 0.0
    for stage, weight in weights.items():
        cumulative += weight
        if stage == order.status:
            break
    return total_sla * cumulative


def heuristic_risk_score(order: Order) -> float:
    """
    Returns a 0-1 risk score.
    Signals:
      - time_ratio: elapsed / total SLA  (closer to or over 1.0 = high risk)
      - stage_lag: elapsed vs expected-for-stage (behind schedule = high risk)
      - procured penalty: non-in-house lenses run higher inherent risk
      - QC fail penalty: each QC failure adds significant risk (re-fabrication time)
    """
    total_sla = SLA_HOURS[order.lens_type]
    elapsed = _elapsed_hours(order)
    time_ratio = elapsed / total_sla if total_sla else 0

    expected_for_stage = _expected_hours_for_stage(order)
    stage_lag = max(0, (elapsed - expected_for_stage) / total_sla) if total_sla else 0

    procured_penalty = 0.0 if order.in_house else 0.15
    qc_penalty = min(order.qc_fail_count * 0.25, 0.5)

    score = (0.5 * time_ratio) + (0.3 * stage_lag) + procured_penalty + qc_penalty
    return round(min(max(score, 0.0), 1.0), 3)


def ml_risk_score(order: Order) -> Optional[float]:
    if _model is None:
        return None
    total_sla = SLA_HOURS[order.lens_type]
    elapsed = _elapsed_hours(order)
    features = [[
        elapsed,
        total_sla,
        elapsed / total_sla if total_sla else 0,
        1 if order.in_house else 0,
        order.qc_fail_count,
        list(OrderStatus).index(order.status),
    ]]
    try:
        proba = _model.predict_proba(features)[0][1]  # P(breach)
        return round(float(proba), 3)
    except Exception:
        return None


def predict_breach_risk(order: Order) -> float:
    """Entry point used by the API layer. Prefers ML model if available and
    valid, otherwise falls back to the heuristic — so the system degrades
    gracefully with no historical data."""
    if _model is not None:
        score = ml_risk_score(order)
        if score is not None:
            return score
    return heuristic_risk_score(order)


RISK_ALERT_THRESHOLD = 0.6
