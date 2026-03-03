from decimal import Decimal
from datetime import datetime
from app import db

def sell_unit(
    unit_id: int, sell_price_brl: Decimal, commission_brl: Decimal = Decimal('0.00'),
    channel: str = None, notes: str = None
):
    """
    Registers a sale for a unit and updates its status.
    Must be called within a request context or manual db session context.
    """
    from app.models import Unit, Sale, UnitStatus

    unit = Unit.query.with_for_update().get(unit_id) # Lock row for update
    if not unit:
        raise ValueError("Unit not found.")
    
    if unit.status == UnitStatus.SOLD:
        raise ValueError("Unit is already sold.")

    sale = Sale(
        unit_id=unit_id,
        sell_price_brl=sell_price_brl,
        commission_brl=commission_brl,
        channel=channel,
        notes=notes,
        sold_at=datetime.utcnow()
    )
    
    unit.status = UnitStatus.SOLD
    
    db.session.add(sale)
    db.session.commit()
    
    return sale

def create_manual_cost(unit_id: int, cost_type: str, brl_value: Decimal, notes: str = None):
 
    """Creates a manual unit cost."""
    from app.models import UnitCost, CostSource, CostType
    
    cost = UnitCost(
        unit_id=unit_id,
        cost_type=CostType(cost_type),
        brl_value=brl_value,
        source=CostSource.MANUAL,
        notes=notes
    )
    db.session.add(cost)
    db.session.commit()
    return cost
