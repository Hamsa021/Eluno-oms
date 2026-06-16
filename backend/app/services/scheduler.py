"""
Periodic job: recompute breach risk for all active orders, flag at-risk ones,
and dispatch an alert (email/WhatsApp) once per order when it first crosses
the risk threshold (to avoid alert spam on every poll).
"""
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.models.models import Order, OrderStatus
from app.services.tat_predictor import predict_breach_risk, RISK_ALERT_THRESHOLD
from app.services.alert_service import dispatch_breach_alert

POLL_INTERVAL_MINUTES = 15


def scan_and_alert():
    db = SessionLocal()
    try:
        active_orders = db.query(Order).filter(
            Order.status.notin_([OrderStatus.DELIVERED, OrderStatus.CANCELLED])
        ).all()

        for order in active_orders:
            score = predict_breach_risk(order)
            order.breach_risk_score = score
            was_at_risk = order.is_at_risk
            order.is_at_risk = score >= RISK_ALERT_THRESHOLD

            if order.is_at_risk and not order.alert_sent:
                sent = dispatch_breach_alert(
                    order_number=order.order_number,
                    risk_score=score,
                    status=order.status.value,
                    sla_deadline=order.sla_deadline.isoformat(),
                )
                if sent:
                    order.alert_sent = True

            # Reset alert flag if it drops back below threshold (allows re-alert later)
            if not order.is_at_risk:
                order.alert_sent = False

        db.commit()
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scan_and_alert, "interval", minutes=POLL_INTERVAL_MINUTES, id="breach_scan")
    scheduler.start()
    return scheduler
