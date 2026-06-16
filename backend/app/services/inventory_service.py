from sqlalchemy.orm import Session

from app.models.models import LensInventory
from app.models.schemas import InventoryCheckResult


def check_inventory(
    db: Session,
    lens_type: str,
    lens_index: str,
    coating: str,
    sphere_power: float,
) -> InventoryCheckResult:
    """
    Look up whether the requested lens spec (type, index, coating, power range)
    is held in-house. Matches against LensInventory rows built from past stocking
    data. Falls back to reorder lead time if not in stock.
    """
    match = (
        db.query(LensInventory)
        .filter(
            LensInventory.lens_type == lens_type,
            LensInventory.lens_index == lens_index,
            LensInventory.coating == coating,
            LensInventory.power_min <= sphere_power,
            LensInventory.power_max >= sphere_power,
        )
        .first()
    )

    if match and match.in_house_qty > 0:
        return InventoryCheckResult(
            in_house=True,
            matched_sku_id=match.id,
            available_qty=match.in_house_qty,
            estimated_ready_hours=2,  # in-house lenses are fitted same-day
        )

    if match:
        # SKU known but currently out of stock
        return InventoryCheckResult(
            in_house=False,
            matched_sku_id=match.id,
            available_qty=0,
            estimated_ready_hours=match.reorder_lead_time_hours,
        )

    # No matching SKU at all -> custom/procured lens, longest lead time
    return InventoryCheckResult(
        in_house=False,
        matched_sku_id=None,
        available_qty=0,
        estimated_ready_hours=96,
    )
