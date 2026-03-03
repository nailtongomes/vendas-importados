import pytest
from app import create_app, db
from app.models import ProductModel, PurchaseLot, Unit, Sale, UnitStatus
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

@pytest.fixture
def init_db(app):
    lot = PurchaseLot(supplier="Apple US", exchange_rate=Decimal('5.0000'))
    model = ProductModel(name="iPhone 15", storage_gb=256)
    db.session.add_all([lot, model])
    db.session.commit()
    return {'lot_id': lot.id, 'model_id': model.id, 'model_name': model.name}

def test_create_unit_with_quantity(client, init_db):
    response = client.post('/api/unit', json={
        'lot_id': init_db['lot_id'],
        'model_name': init_db['model_name'],
        'serial': 'ABC',
        'usd_cost': '500.00',
        'quantity': 3
    })
    
    assert response.status_code == 201
    
    # Check if 3 units were actually created
    units = Unit.query.all()
    assert len(units) == 3
    
    serials = [u.serial for u in units]
    assert 'ABC-1' in serials
    assert 'ABC-2' in serials
    assert 'ABC-3' in serials

def test_create_unit_without_quantity(client, init_db):
    response = client.post('/api/unit', json={
        'lot_id': init_db['lot_id'],
        'model_name': init_db['model_name'],
        'serial': 'DEF',
        'usd_cost': '500.00'
    })
    
    assert response.status_code == 201
    units = Unit.query.filter_by(serial='DEF').all()
    assert len(units) == 1

def test_update_unit_status_to_sold(client, init_db):
    # First create a unit
    u = Unit(serial='123', product_model_id=init_db['model_id'], purchase_lot_id=init_db['lot_id'], usd_cost=Decimal('500.00'))
    db.session.add(u)
    db.session.commit()
    
    assert u.status == UnitStatus.AVAILABLE
    
    # Patch status to SOLD
    response = client.patch(f'/api/unit/{u.id}', json={
        'status': 'SOLD'
    })
    
    assert response.status_code == 200
    assert response.json['success'] is True
    
    db.session.refresh(u)
    assert u.status == UnitStatus.SOLD
    
    # Verify sale was automatically created
    sale = Sale.query.filter_by(unit_id=u.id).first()
    assert sale is not None
    assert sale.sell_price_brl == Decimal('0.00')
    assert sale.commission_brl == Decimal('0.00')
    assert sale.channel == "Estoque"

def test_update_sale(client, init_db):
    u = Unit(serial='XYZ', product_model_id=init_db['model_id'], purchase_lot_id=init_db['lot_id'], usd_cost=Decimal('500.00'))
    db.session.add(u)
    db.session.commit()
    
    sale = Sale(unit_id=u.id, sell_price_brl=Decimal('0.00'), commission_brl=Decimal('0.00'), channel="Estoque")
    db.session.add(sale)
    db.session.commit()
    
    # Update the sale details
    response = client.patch(f'/api/sale/{sale.id}', json={
        'sell_price_brl': '3500.00',
        'commission_brl': '100.00',
        'channel': 'WhatsApp'
    })
    
    assert response.status_code == 200
    
    db.session.refresh(sale)
    assert sale.sell_price_brl == Decimal('3500.00')
    assert sale.commission_brl == Decimal('100.00')
    assert sale.channel == 'WhatsApp'
