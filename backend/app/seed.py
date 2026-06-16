"""
Seeds the DB with sample lens inventory ("past data") and a handful of demo
orders across different stages, so the dashboard isn't empty on first load.
Run: python -m app.seed
"""
from datetime import datetime, timedelta

from app.database import SessionLocal, engine, Base
from app.models.models import LensInventory, Order, StatusHistory, LensType, OrderStatus, SLA_HOURS

Base.metadata.create_all(bind=engine)


def seed_inventory(db):
    if db.query(LensInventory).count() > 0:
        return
    items = [
        # Single vision - commonly stocked in-house across most power ranges
        LensInventory(lens_type=LensType.SINGLE_VISION, lens_index="1.50", coating="None", power_min=-6, power_max=6, in_house_qty=50, reorder_lead_time_hours=24),
        LensInventory(lens_type=LensType.SINGLE_VISION, lens_index="1.56", coating="AR", power_min=-8, power_max=8, in_house_qty=30, reorder_lead_time_hours=24),
        LensInventory(lens_type=LensType.SINGLE_VISION, lens_index="1.67", coating="AR", power_min=-10, power_max=2, in_house_qty=5, reorder_lead_time_hours=48),
        # Bifocal - lower stock, longer reorder
        LensInventory(lens_type=LensType.BIFOCAL, lens_index="1.56", coating="AR", power_min=-6, power_max=6, in_house_qty=10, reorder_lead_time_hours=48),
        # Progressive - mostly procured, minimal in-house stock
        LensInventory(lens_type=LensType.PROGRESSIVE, lens_index="1.56", coating="Blue-cut", power_min=-4, power_max=4, in_house_qty=0, reorder_lead_time_hours=96),
        LensInventory(lens_type=LensType.PROGRESSIVE, lens_index="1.67", coating="AR", power_min=-6, power_max=6, in_house_qty=2, reorder_lead_time_hours=72),
        # Contact lens - fast moving, well stocked
        LensInventory(lens_type=LensType.CONTACT_LENS, lens_index="N/A", coating="None", power_min=-10, power_max=10, in_house_qty=100, reorder_lead_time_hours=24),
    ]
    db.add_all(items)
    db.commit()
    print(f"Seeded {len(items)} inventory items")


def seed_orders(db):
    if db.query(Order).count() > 0:
        return
    samples = [
        dict(order_number="ELN-DEMO-0001", customer_name="Anita Rao", customer_phone="9900011111",
             store_location="Bengaluru - Indiranagar", source="store", sphere_power=-2.0,
             lens_type=LensType.SINGLE_VISION, lens_index="1.50", coating="None",
             in_house=True, status=OrderStatus.PROCESSING, hours_ago=4),
        dict(order_number="ELN-DEMO-0002", customer_name="Rahul Mehta", customer_phone="9900022222",
             store_location="Mumbai - Andheri", source="website", sphere_power=-5.5,
             lens_type=LensType.PROGRESSIVE, lens_index="1.67", coating="AR",
             in_house=False, status=OrderStatus.LENS_FITTING, hours_ago=50),
        dict(order_number="ELN-DEMO-0003", customer_name="Sneha Iyer", customer_phone="9900033333",
             store_location="Bengaluru - Indiranagar", source="app", sphere_power=1.5,
             lens_type=LensType.BIFOCAL, lens_index="1.56", coating="AR",
             in_house=True, status=OrderStatus.QC, hours_ago=40),
        dict(order_number="ELN-DEMO-0004", customer_name="Vikram Shah", customer_phone="9900044444",
             store_location="Delhi - CP", source="store", sphere_power=-3.0,
             lens_type=LensType.PROGRESSIVE, lens_index="1.56", coating="Blue-cut",
             in_house=False, status=OrderStatus.QC_FAILED, hours_ago=65),
        dict(order_number="ELN-DEMO-0005", customer_name="Divya Nair", customer_phone="9900055555",
             store_location="Mumbai - Andheri", source="partner", sphere_power=0.0,
             lens_type=LensType.CONTACT_LENS, lens_index="N/A", coating="None",
             in_house=True, status=OrderStatus.DISPATCHED, hours_ago=15),
    ]

    from app.services.tat_predictor import predict_breach_risk, RISK_ALERT_THRESHOLD

    for s in samples:
        created_at = datetime.utcnow() - timedelta(hours=s["hours_ago"])
        sla_deadline = created_at + timedelta(hours=SLA_HOURS[s["lens_type"]] + (0 if s["in_house"] else 24))
        order = Order(
            order_number=s["order_number"],
            customer_name=s["customer_name"],
            customer_phone=s["customer_phone"],
            store_location=s["store_location"],
            source=s["source"],
            sphere_power=s["sphere_power"],
            lens_type=s["lens_type"],
            lens_index=s["lens_index"],
            coating=s["coating"],
            in_house=s["in_house"],
            status=s["status"],
            qc_fail_count=1 if s["status"] == OrderStatus.QC_FAILED else 0,
            created_at=created_at,
            sla_deadline=sla_deadline,
        )
        db.add(order)
        db.flush()
        score = predict_breach_risk(order)
        order.breach_risk_score = score
        order.is_at_risk = score >= RISK_ALERT_THRESHOLD
        db.add(StatusHistory(order_id=order.id, from_status=None, to_status=order.status, reason="seed data", changed_by="system"))

    db.commit()
    print(f"Seeded {len(samples)} demo orders")


def main():
    db = SessionLocal()
    try:
        seed_inventory(db)
        seed_orders(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
