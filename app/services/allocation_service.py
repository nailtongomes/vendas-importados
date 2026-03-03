import uuid
from decimal import Decimal, ROUND_HALF_UP
from app import db
from app.models import Unit, UnitCost, CostSource, CostType

def allocate_lot_costs(lot_id: int, costs: dict) -> str:
    """
    Allocates costs to units in a lot proportionally to their USD cost.
    Costs dict format: {CostType.FREIGHT_INTL: Decimal('100.00'), ...}
    Returns the allocation_run_id.
    """
    allocation_run_id = str(uuid.uuid4())

    units = Unit.query.filter_by(purchase_lot_id=lot_id).all()
    if not units:
        return allocation_run_id

    total_usd = sum((unit.usd_cost for unit in units), Decimal('0.00'))
    if total_usd == 0:
        raise ValueError("Total USD cost of lot is zero, cannot allocate proportionally.")

    # Remove previous allocated costs for this lot
    UnitCost.query.filter_by(lot_id=lot_id, source=CostSource.ALLOCATED).delete()

    for cost_type_str, total_cost_val in costs.items():
        if not total_cost_val or Decimal(total_cost_val) == 0:
            continue
        
        cost_type = CostType(cost_type_str)
        total_cost = Decimal(total_cost_val)
        
        allocated_so_far = Decimal('0.00')

        # Sort units by USD cost descending to allocate remainders to the most expensive ones
        sorted_units = sorted(units, key=lambda u: u.usd_cost, reverse=True)

        for i, unit in enumerate(sorted_units):
            if i == len(sorted_units) - 1:
                # Last unit gets the exact remainder to avoid cent rounding issues
                allocated_val = total_cost - allocated_so_far
            else:
                proportion = unit.usd_cost / total_usd
                allocated_val = (total_cost * proportion).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                allocated_so_far += allocated_val

            new_cost = UnitCost(
                unit_id=unit.id,
                cost_type=cost_type,
                brl_value=allocated_val,
                source=CostSource.ALLOCATED,
                lot_id=lot_id,
                allocation_run_id=allocation_run_id
            )
            db.session.add(new_cost)

    db.session.commit()
    return allocation_run_id
