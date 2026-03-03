from decimal import Decimal, ROUND_HALF_UP

def get_base_brl(usd_cost: Decimal, exchange_rate: Decimal) -> Decimal:
    """Calculates the base BRL cost from USD."""
    return (usd_cost * exchange_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def get_total_cost_brl(base_brl: Decimal, unit_costs: list) -> Decimal:
    """Calculates total BRL cost by adding all unit costs to the base BRL."""
    total_costs = sum((cost.brl_value for cost in unit_costs), Decimal('0.00'))
    return (base_brl + total_costs).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def get_net_profit(sell_price_brl: Decimal, total_cost_brl: Decimal, commission_brl: Decimal) -> Decimal:
    """Calculates net profit."""
    return (sell_price_brl - total_cost_brl - commission_brl).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def get_net_margin(net_profit: Decimal, sell_price_brl: Decimal) -> Decimal:
    """Calculates net margin as a percentage."""
    if sell_price_brl == 0:
        return Decimal('0.00')
    return (net_profit / sell_price_brl).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
