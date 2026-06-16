import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Enum, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id():
    return str(uuid.uuid4())


class OrderStatus(str, enum.Enum):
    PLACED = "placed"
    INVENTORY_CHECK = "inventory_check"
    PROCESSING = "processing"
    LENS_FITTING = "lens_fitting"
    QC = "qc"
    QC_FAILED = "qc_failed"      # loops back to processing
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class LensType(str, enum.Enum):
    SINGLE_VISION = "single_vision"
    BIFOCAL = "bifocal"
    PROGRESSIVE = "progressive"
    CONTACT_LENS = "contact_lens"


# SLA in hours per lens type (tweak based on real ops data)
SLA_HOURS = {
    LensType.SINGLE_VISION: 24,
    LensType.BIFOCAL: 48,
    LensType.PROGRESSIVE: 72,
    LensType.CONTACT_LENS: 24,
}

# Stage allocation as % of total SLA (used by heuristic predictor)
STAGE_SLA_WEIGHTS = {
    OrderStatus.PLACED: 0.05,
    OrderStatus.INVENTORY_CHECK: 0.10,
    OrderStatus.PROCESSING: 0.35,
    OrderStatus.LENS_FITTING: 0.25,
    OrderStatus.QC: 0.15,
    OrderStatus.DISPATCHED: 0.10,
}


class LensInventory(Base):
    __tablename__ = "lens_inventory"

    id = Column(String, primary_key=True, default=gen_id)
    lens_type = Column(Enum(LensType), nullable=False)
    lens_index = Column(String, nullable=False)       # e.g. "1.56", "1.67"
    coating = Column(String, nullable=False)           # e.g. "AR", "Blue-cut", "None"
    power_min = Column(Float, nullable=False)          # sphere power range this SKU covers
    power_max = Column(Float, nullable=False)
    in_house_qty = Column(Integer, default=0)
    reorder_lead_time_hours = Column(Integer, default=72)  # if not in stock

    def __repr__(self):
        return f"<LensInventory {self.lens_type} idx={self.lens_index} coat={self.coating}>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=gen_id)
    order_number = Column(String, unique=True, nullable=False)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_email = Column(String, nullable=True)

    source = Column(String, default="store")           # store / website / app / partner
    store_location = Column(String, nullable=False)

    # Prescription details
    sphere_power = Column(Float, nullable=False)
    cylinder_power = Column(Float, default=0.0)
    lens_type = Column(Enum(LensType), nullable=False)
    lens_index = Column(String, nullable=False)
    coating = Column(String, nullable=False)
    frame_sku = Column(String, nullable=True)

    in_house = Column(Boolean, default=None, nullable=True)  # set after inventory check

    status = Column(Enum(OrderStatus), default=OrderStatus.PLACED)
    qc_fail_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    sla_deadline = Column(DateTime, nullable=False)
    delivered_at = Column(DateTime, nullable=True)

    breach_risk_score = Column(Float, default=0.0)     # 0-1 probability from predictor
    is_at_risk = Column(Boolean, default=False)
    alert_sent = Column(Boolean, default=False)

    status_history = relationship(
        "StatusHistory", back_populates="order", cascade="all, delete-orphan"
    )


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(String, primary_key=True, default=gen_id)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    reason = Column(Text, nullable=True)               # required if delay
    changed_by = Column(String, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="status_history")
