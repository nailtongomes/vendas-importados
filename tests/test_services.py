import pytest
from app import create_app, db
from app.models import ProductModel, PurchaseLot, Unit, UnitCost, CostType, CostSource
from app.services import get_base_brl, get_total_cost_brl, get_net_profit, get_net_margin, allocate_lot_costs, sell_unit, create_manual_cost
from decimal import Decimal

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_base_brl():
    usd_cost = Decimal('500.00')
    exchange_rate = Decimal('5.250000')
    assert get_base_brl(usd_cost, exchange_rate) == Decimal('2625.00')

def test_total_cost_brl(app):
    base_brl = Decimal('2625.00')
    unit = Unit(serial='123', product_model_id=1, purchase_lot_id=1, usd_cost=Decimal('500.00')) # mocked
    db.session.add(unit)
    db.session.commit()
    
    cost1 = create_manual_cost(unit.id, CostType.FREIGHT_INTL, Decimal('100.00'))
    cost2 = create_manual_cost(unit.id, CostType.IMPORT_TAX, Decimal('50.55'))
    
    assert get_total_cost_brl(base_brl, [cost1, cost2]) == Decimal('2775.55')

def test_net_profits():
    total_cost = Decimal('2775.50')
    sell_price = Decimal('3500.00')
    commission = Decimal('100.00')
    
    profit = get_net_profit(sell_price, total_cost, commission)
    assert profit == Decimal('624.50')
    
    margin = get_net_margin(profit, sell_price)
    assert margin == Decimal('0.1784') # 17.84%

def test_allocation_logic(app):
    lot = PurchaseLot(supplier="Apple US", exchange_rate=Decimal('5.0000'))
    model = ProductModel(name="iPhone", storage_gb=128)
    db.session.add_all([lot, model])
    db.session.commit()
    
    # Unit 1 is more expensive ($600), Unit 2 is cheaper ($400). Total = $1000
    u1 = Unit(serial='111', product_model_id=model.id, purchase_lot_id=lot.id, usd_cost=Decimal('600.00'))
    u2 = Unit(serial='222', product_model_id=model.id, purchase_lot_id=lot.id, usd_cost=Decimal('400.00'))
    db.session.add_all([u1, u2])
    db.session.commit()
    
    # Allocate 100 BRL in freight. Unit 1 should get 60, Unit 2 should get 40.
    allocate_lot_costs(lot.id, {CostType.FREIGHT_INTL: Decimal('100.00')})
    
    c1 = UnitCost.query.filter_by(unit_id=u1.id).first()
    c2 = UnitCost.query.filter_by(unit_id=u2.id).first()
    
    assert c1.brl_value == Decimal('60.00')
    assert c2.brl_value == Decimal('40.00')

def test_sell_unit(app):
    lot = PurchaseLot(supplier="Apple US", exchange_rate=Decimal('5.0000'))
    model = ProductModel(name="iPhone", storage_gb=128)
    db.session.add_all([lot, model])
    db.session.commit()
    
    u = Unit(serial='333', product_model_id=model.id, purchase_lot_id=lot.id, usd_cost=Decimal('500.00'))
    db.session.add(u)
    db.session.commit()
    
    sale = sell_unit(u.id, Decimal('3000.00'), Decimal('100.00'), "Instagram")
    assert sale.unit_id == u.id
    assert sale.sell_price_brl == Decimal('3000.00')
    assert sale.commission_brl == Decimal('100.00')
    assert sale.channel == "Instagram"
    
    from app.models import UnitStatus
    db.session.refresh(u)
    assert u.status == UnitStatus.SOLD

def test_sell_unit_errors(app):
    with pytest.raises(ValueError, match="Unit not found."):
        sell_unit(999, Decimal('100.00'))
        
    lot = PurchaseLot(supplier="Temp", exchange_rate=Decimal('5.0000'))
    model = ProductModel(name="Temp")
    db.session.add_all([lot, model])
    db.session.commit()
    
    from app.models import UnitStatus
    u = Unit(serial='444', product_model_id=model.id, purchase_lot_id=lot.id, usd_cost=Decimal('500.00'), status=UnitStatus.SOLD)
    db.session.add(u)
    db.session.commit()
    
    with pytest.raises(ValueError, match="Unit is already sold."):
        sell_unit(u.id, Decimal('100.00'))

