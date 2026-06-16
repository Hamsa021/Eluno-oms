# Eluno AI — Order Management System

AI-powered order management system for an eyewear brand, covering the full order lifecycle from intake to delivery across three integrated modules: lens inventory management, an order status dashboard, and TAT (turnaround time) breach prediction with alerts.

## Stack
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (SQLite for local dev) + APScheduler + scikit-learn
- **Frontend**: React + Vite + Tailwind CSS
- **Alerts**: SMTP (email) + Twilio WhatsApp API

## Project structure
```
eluno-oms/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── database.py          # DB session/engine setup
│   │   ├── seed.py               # Seeds inventory + demo orders
│   │   ├── models/
│   │   │   ├── models.py        # SQLAlchemy ORM models
│   │   │   └── schemas.py       # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── orders.py        # Order CRUD, status transitions, filters
│   │   │   ├── inventory.py     # Inventory check + listing
│   │   │   └── dashboard.py     # Summary stats, store locations
│   │   └── services/
│   │       ├── inventory_service.py   # Module 1: in-house/procured lookup
│   │       ├── tat_predictor.py       # Module 3: heuristic + ML breach scoring
│   │       ├── train_model.py         # Optional: trains the ML model
│   │       ├── alert_service.py       # Email/WhatsApp dispatch
│   │       └── scheduler.py           # Periodic breach scan job
│   ├── requirements.txt
│   ├── render.yaml              # Render deployment config
│   ├── Dockerfile               # Alternative deploy path
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx               # Module 2: dashboard shell
    │   ├── components/           # Header, FilterBar, OrderTable, OrderDetail, NewOrderModal
    │   ├── api/client.js         # Backend API client
    │   └── constants.js          # Status labels, SLA math, transitions
    ├── package.json
    ├── vercel.json
    └── .env.example
```

## Run locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m app.seed        # seeds inventory + 5 demo orders
uvicorn app.main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`.

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Opens at `http://localhost:5173`. Set `VITE_API_URL` in `.env` if backend isn't on `localhost:8000`.

## Deploy

**Backend (Render)**: push to GitHub, create a new Render Web Service from `backend/render.yaml` (Blueprint deploy). It provisions a free Postgres DB and wires `DATABASE_URL` automatically. Alternatively use the included `Dockerfile` on Railway/Fly.io.

**Frontend (Vercel)**: import the `frontend/` folder as a Vercel project, set `VITE_API_URL` env var to your deployed backend URL, deploy.

**Alerts**: set `SMTP_*` and `TWILIO_*` env vars (see `backend/.env.example`) on your backend host. Without them, alerts are logged to console only — the system still runs end-to-end for a demo.

## Upgrading TAT prediction to a trained ML model
The system ships with a heuristic risk score that works with zero historical data. Once real order history accumulates (or to demo the ML path immediately with synthetic data):
```bash
cd backend
python -m app.services.train_model
```
This writes `tat_model.joblib`, which `tat_predictor.py` auto-loads on the next restart — no code changes needed.

## Demo walkthrough checklist (for the 15-min recording)
1. Show the seeded dashboard: active orders, SLA countdowns, at-risk flag on the seeded QC-failed order.
2. Filter by status / lens type / store location.
3. Create a new order — show the inventory preview switching between in-house and procured.
4. Open an order, walk through a valid status transition, then attempt an invalid one (rejected) and a QC-fail without a reason (rejected) to show validation.
5. Show the status history log building up.
6. Explain the breach predictor (heuristic vs. optional ML model) and show a console-logged alert (or live email/WhatsApp if credentials are configured).
7. Briefly walk through `ARCHITECTURE_NOTE.md`.
