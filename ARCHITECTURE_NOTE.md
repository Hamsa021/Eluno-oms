# Eluno AI — Architecture Note

## System overview
Three integrated modules on a shared FastAPI + PostgreSQL backend, with a React dashboard frontend.

1. **Lens Inventory Management** — A `lens_inventory` table holds known SKUs (lens type × index × coating × power range) with current stock counts and reorder lead times, built from historical stocking data. On order creation, a deterministic lookup matches the prescription against this table to flag the lens as **in-house** (ships in ~2h) or **procured** (longer SLA, lead time pulled from the matched SKU or a default for unknown specs). This is a rules/lookup engine, not an AI model — the inventory question is a database match problem, not a prediction problem, so adding AI here would add latency and uncertainty without benefit.

2. **Order Dashboard** — Orders move through a fixed state machine: Placed → Inventory Check → Processing → Lens Fitting → QC → Dispatched → Delivered, with QC failures looping back to Processing (re-order). Every transition is validated server-side against an allow-list and logged to a `status_history` table with a mandatory reason on QC failure. The dashboard supports filtering by status, lens type, and store location, and shows live SLA countdowns per order.

3. **TAT Prediction & Breach Alerts** — A background job (APScheduler, polling every 15 min) recomputes a 0–1 breach-risk score per active order and triggers email/WhatsApp alerts when an order crosses a 0.6 threshold, with alert-dedup so a single order doesn't spam. Two interchangeable scoring strategies are implemented:
   - **Heuristic (default)**: weighted combination of (a) elapsed time ÷ SLA budget, (b) actual elapsed time vs. expected time-for-stage (is this order behind schedule for where it currently sits), (c) a fixed penalty for procured (non-in-house) lenses, (d) a penalty per QC failure. This requires no training data and is immediately deployable, auditable, and explainable to ops — important for a system whose outputs trigger team escalations.
   - **ML upgrade path (optional)**: a GradientBoostingClassifier trained on historical order outcomes (features: elapsed hours, total SLA, time ratio, in-house flag, QC fail count, stage index; label: did this order actually breach). The predictor module auto-loads a trained model if present at `tat_model.joblib`, otherwise falls back to the heuristic — so the system degrades gracefully before enough order history exists to train on, and upgrades automatically once it does. A training script with a synthetic-data generator is included so the ML path can be demonstrated even without real historical orders.

## AI/ML models and APIs used, and why
- **Gradient Boosting (scikit-learn)** for breach prediction: tabular data with a handful of engineered features and a binary outcome is the textbook case for tree-based ensembles — they outperform deep learning at this data scale, train in seconds, and give interpretable feature importances the ops team can sanity-check.
- **Heuristic rule engine** as the production default until real order history accumulates (cold-start problem): a hand-tuned weighted formula encoding domain knowledge (SLA ratio, stage lag, sourcing type, QC history) is more reliable than a model trained on too little or synthetic data, and it's transparent — anyone can audit why an order was flagged.
- **No LLM is used for inventory matching or status transitions** — both are deterministic lookup/state-machine problems where an LLM would add cost and non-determinism without improving correctness.
- **Twilio WhatsApp API** and **SMTP** for alert delivery — chosen for fast sandbox setup (no business verification needed) suitable for a demo/MVP; swappable for WhatsApp Business Cloud API or a transactional email provider (SendGrid/Postmark) in production.

## Why this split
The assignment rewards a system that's reliable end-to-end over one with AI bolted on everywhere. AI is applied only where prediction genuinely adds value (breach forecasting); inventory and status management stay deterministic and auditable, which matters more for an ops tool that the team needs to trust and act on quickly.
