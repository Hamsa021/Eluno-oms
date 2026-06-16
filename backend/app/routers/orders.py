import random
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Order, StatusHistory, OrderStatus, SLA_HOURS
from app.models.schemas import OrderCreate, OrderOut, StatusUpdate, StatusHistoryOut
from app.services.inventory_service import check_inventory
from app.services.tat_predictor import predict_breach_risk, RISK_ALERT_THRESHOLD

router = APIRouter(prefix="/orders", tags=["orders"])

# Valid forward transitions; QC_FAILED loops back to PROCESSING
ALLOWED_TRANSITIONS = {
    OrderStatus.PLACED: [OrderStatus.INVENTORY_CHECK, OrderStatus.CANCELLED],
    OrderStatus.INVENTORY_CHECK: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
    OrderStatus.PROCESSING: [OrderStatus.LENS_FITTING, OrderStatus.CANCELLED],
    OrderStatus.LENS_FITTING: [OrderStatus.QC, OrderStatus.CANCELLED],
    OrderStatus.QC: [OrderStatus.DISPATCHED, OrderStatus.QC_FAILED],
    OrderStatus.QC_FAILED: [OrderStatus.PROCESSING],  # re-order loop
    OrderStatus.DISPATCHED: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


def _gen_order_number() -> str:
    return f"ELN-{datetime.utcnow().strftime('%y%m%d')}-{random.randint(1000, 9999)}"


@router.post("", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    inv_result = check_inventory(
        db,
        lens_type=payload.lens_type,
        lens_index=payload.lens_index,
        coating=payload.coating,
        sphere_power=payload.sphere_power,
    )

    total_sla = SLA_HOURS[payload.lens_type]
    # If lens must be procured, extend the effective SLA deadline accordingly
    extra_hours = max(0, inv_result.estimated_ready_hours - 2)
    sla_deadline = datetime.utcnow() + timedelta(hours=total_sla + extra_hours)

    order = Order(
        order_number=_gen_order_number(),
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_email=payload.customer_email,
        source=payload.source,
        store_location=payload.store_location,
        sphere_power=payload.sphere_power,
        cylinder_power=payload.cylinder_power,
        lens_type=payload.lens_type,
        lens_index=payload.lens_index,
        coating=payload.coating,
        frame_sku=payload.frame_sku,
        in_house=inv_result.in_house,
        status=OrderStatus.INVENTORY_CHECK,
        sla_deadline=sla_deadline,
    )
    db.add(order)
    db.flush()

    db.add(StatusHistory(
        order_id=order.id,
        from_status=None,
        to_status=OrderStatus.INVENTORY_CHECK,
        reason=f"In-house: {inv_result.in_house}, est. ready in {inv_result.estimated_ready_hours}h",
        changed_by="system",
    ))
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=List[OrderOut])
def list_orders(
    status: Optional[OrderStatus] = None,
    lens_type: Optional[str] = None,
    store_location: Optional[str] = None,
    at_risk_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if lens_type:
        query = query.filter(Order.lens_type == lens_type)
    if store_location:
        query = query.filter(Order.store_location == store_location)
    if at_risk_only:
        query = query.filter(Order.is_at_risk == True)  # noqa: E712
    return query.order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.get("/{order_id}/history", response_model=List[StatusHistoryOut])
def get_order_history(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    return order.status_history


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(order_id: str, payload: StatusUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    allowed = ALLOWED_TRANSITIONS.get(order.status, [])
    if payload.new_status not in allowed:
        raise HTTPException(
            400,
            f"Invalid transition: {order.status} -> {payload.new_status}. "
            f"Allowed: {[s.value for s in allowed]}",
        )

    # Delay reason required whenever the order moves into QC_FAILED, or is
    # manually held/delayed at the same stage
    if payload.new_status == OrderStatus.QC_FAILED and not payload.reason:
        raise HTTPException(400, "Reason is required when logging a QC failure")

    old_status = order.status
    order.status = payload.new_status

    if payload.new_status == OrderStatus.QC_FAILED:
        order.qc_fail_count += 1
    if payload.new_status == OrderStatus.DELIVERED:
        order.delivered_at = datetime.utcnow()

    db.add(StatusHistory(
        order_id=order.id,
        from_status=old_status,
        to_status=payload.new_status,
        reason=payload.reason,
        changed_by=payload.changed_by,
    ))

    # Recompute breach risk on every status change
    order.breach_risk_score = predict_breach_risk(order)
    order.is_at_risk = order.breach_risk_score >= RISK_ALERT_THRESHOLD

    db.commit()
    db.refresh(order)
    return order
