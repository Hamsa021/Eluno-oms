from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import LensInventory, LensType
from app.services.inventory_service import check_inventory
from app.models.schemas import InventoryCheckResult

router = APIRouter(prefix="/inventory", tags=["inventory"])


class InventoryCheckRequest(BaseModel):
    lens_type: LensType
    lens_index: str
    coating: str
    sphere_power: float


class InventoryItemOut(BaseModel):
    id: str
    lens_type: LensType
    lens_index: str
    coating: str
    power_min: float
    power_max: float
    in_house_qty: int
    reorder_lead_time_hours: int

    class Config:
        from_attributes = True


@router.post("/check", response_model=InventoryCheckResult)
def check(payload: InventoryCheckRequest, db: Session = Depends(get_db)):
    return check_inventory(
        db,
        lens_type=payload.lens_type,
        lens_index=payload.lens_index,
        coating=payload.coating,
        sphere_power=payload.sphere_power,
    )


@router.get("", response_model=List[InventoryItemOut])
def list_inventory(db: Session = Depends(get_db)):
    return db.query(LensInventory).all()
