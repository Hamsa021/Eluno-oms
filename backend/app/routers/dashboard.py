from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.models import Order, OrderStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    total_active = (
        db.query(func.count(Order.id))
        .filter(Order.status.notin_([OrderStatus.DELIVERED, OrderStatus.CANCELLED]))
        .scalar()
    )
    at_risk = db.query(func.count(Order.id)).filter(Order.is_at_risk == True).scalar()  # noqa: E712
    breached = (
        db.query(func.count(Order.id))
        .filter(
            Order.sla_deadline < datetime.utcnow(),
            Order.status.notin_([OrderStatus.DELIVERED, OrderStatus.CANCELLED]),
        )
        .scalar()
    )
    by_status = (
        db.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )

    return {
        "total_active": total_active,
        "at_risk_count": at_risk,
        "breached_count": breached,
        "by_status": {status.value: count for status, count in by_status},
    }


@router.get("/locations")
def store_locations(db: Session = Depends(get_db)) -> List[str]:
    rows = db.query(Order.store_location).distinct().all()
    return [r[0] for r in rows]
