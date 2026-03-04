import pytest
from app import create_app, db
from app.models import ProductModel, PurchaseLot, Unit, Sale, UnitStatus, UnitCost, CostType, CostSource, AdminUser
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
    client = app.test_client()
    # Authenticate the test client
    with client.session_transaction() as sess:
        sess['authenticated'] = True
    return client

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


def test_delete_unit_available(client, init_db):
    """Test deleting an available unit."""
    u = Unit(serial='DEL1', product_model_id=init_db['model_id'], purchase_lot_id=init_db['lot_id'], usd_cost=Decimal('500.00'))
    db.session.add(u)
    db.session.commit()
    uid = u.id

    response = client.delete(f'/api/unit/{uid}')
    assert response.status_code == 200
    assert response.json['success'] is True

    assert Unit.query.get(uid) is None


def test_delete_unit_with_sale(client, init_db):
    """Test deleting a sold unit removes the associated sale too."""
    u = Unit(serial='DEL2', product_model_id=init_db['model_id'], purchase_lot_id=init_db['lot_id'], usd_cost=Decimal('500.00'), status=UnitStatus.SOLD)
    db.session.add(u)
    db.session.commit()

    sale = Sale(unit_id=u.id, sell_price_brl=Decimal('3000.00'), commission_brl=Decimal('0.00'))
    db.session.add(sale)
    db.session.commit()
    uid = u.id
    sale_id = sale.id

    response = client.delete(f'/api/unit/{uid}')
    assert response.status_code == 200
    assert response.json['success'] is True

    assert Unit.query.get(uid) is None
    assert Sale.query.get(sale_id) is None


def test_delete_unit_with_costs(client, init_db):
    """Test deleting a unit cascades deletion to its costs."""
    u = Unit(serial='DEL3', product_model_id=init_db['model_id'], purchase_lot_id=init_db['lot_id'], usd_cost=Decimal('500.00'))
    db.session.add(u)
    db.session.commit()

    cost = UnitCost(unit_id=u.id, cost_type=CostType.FREIGHT_INTL, brl_value=Decimal('100.00'), source=CostSource.MANUAL)
    db.session.add(cost)
    db.session.commit()
    uid = u.id
    cost_id = cost.id

    response = client.delete(f'/api/unit/{uid}')
    assert response.status_code == 200

    assert Unit.query.get(uid) is None
    assert UnitCost.query.get(cost_id) is None


def test_delete_unit_not_found(client, init_db):
    """Test deleting a non-existent unit returns 404."""
    response = client.delete('/api/unit/99999')
    assert response.status_code == 404


def test_setup_creates_admin(client, app):
    """Test that setup page creates admin user."""
    # No admin users exist initially
    assert AdminUser.query.count() == 0

    response = client.post('/setup', data={
        'username': 'myadmin',
        'password': 'secret123',
        'password_confirm': 'secret123'
    }, follow_redirects=False)
    assert response.status_code == 302

    admin = AdminUser.query.filter_by(username='myadmin').first()
    assert admin is not None
    assert admin.check_password('secret123')


def test_setup_blocked_after_admin_exists(client, app):
    """Test that setup page redirects to login if admin already exists."""
    admin = AdminUser(username='existing')
    admin.set_password('pass1234')
    db.session.add(admin)
    db.session.commit()

    response = client.get('/setup', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_setup_password_mismatch(client, app):
    """Test setup rejects mismatched passwords."""
    response = client.post('/setup', data={
        'username': 'admin',
        'password': 'pass1234',
        'password_confirm': 'different'
    })
    assert response.status_code == 200
    assert AdminUser.query.count() == 0


def test_login_with_db_credentials(app):
    """Test login works with DB-stored credentials."""
    admin = AdminUser(username='testadmin')
    admin.set_password('testpass')
    db.session.add(admin)
    db.session.commit()

    client = app.test_client()
    response = client.post('/login', data={
        'username': 'testadmin',
        'password': 'testpass'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/dashboard' in response.headers['Location']
