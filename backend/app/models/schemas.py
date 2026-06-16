from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from app.models.models import OrderStatus, LensType


class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    source: str = "store"
    store_location: str
    sphere_power: float
    cylinder_power: float = 0.0
    lens_type: LensType
    lens_index: str
    coating: str
    frame_sku: Optional[str] = None


class StatusUpdate(BaseModel):
    new_status: OrderStatus
    reason: Optional[str] = None
    changed_by: Optional[str] = "system"


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_number: str
    customer_name: str
    customer_phone: str
    store_location: str
    source: str
    sphere_power: float
    cylinder_power: float
    lens_type: LensType
    lens_index: str
    coating: str
    in_house: Optional[bool]
    status: OrderStatus
    qc_fail_count: int
    created_at: datetime
    sla_deadline: datetime
    delivered_at: Optional[datetime]
    breach_risk_score: float
    is_at_risk: bool


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: Optional[str]
    to_status: str
    reason: Optional[str]
    changed_by: Optional[str]
    changed_at: datetime


class InventoryCheckResult(BaseModel):
    in_house: bool
    matched_sku_id: Optional[str] = None
    available_qty: int = 0
    estimated_ready_hours: int
