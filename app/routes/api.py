from flask import Blueprint, jsonify, request
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from app import db
from app.models import Unit, ProductModel, PurchaseLot, UnitCost, Sale, CostSource, CostType
from app.services import get_base_brl, get_total_cost_brl, get_net_profit, get_net_margin, allocate_lot_costs, sell_unit, create_manual_cost
from app.auth import api_login_required
from sqlalchemy.orm import joinedload
from sqlalchemy import func

bp = Blueprint('api', __name__, url_prefix='/api')

# ── Units ──────────────────────────────────────────────────────────────────────

@bp.route('/units', methods=['GET'])
@api_login_required
def get_units():
    units = Unit.query.options(
        joinedload(Unit.product_model),
        joinedload(Unit.purchase_lot),
        joinedload(Unit.costs)
    ).all()

    data = []
    for u in units:
        base = get_base_brl(u.usd_cost, u.purchase_lot.exchange_rate)
        total = get_total_cost_brl(base, u.costs)
        data.append({
            'id': u.id,
            'serial': u.serial,
            'model_label': _model_label(u.product_model),
            'usd_cost': str(u.usd_cost),
            'total_cost_brl': str(total),
            'status': u.status.value,
            'holder': u.holder or '',
            'lot_id': u.purchase_lot_id
        })
    return jsonify({'data': data})


@bp.route('/unit', methods=['POST'])
@api_login_required
def create_unit():
    data = request.json or {}
    required = ['lot_id', 'serial', 'usd_cost', 'model_name']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Campo obrigatório: {field}'}), 400

    lot = PurchaseLot.query.get(data['lot_id'])
    if not lot:
        return jsonify({'error': 'Lote não encontrado'}), 404

    if Unit.query.filter_by(serial=data['serial']).first():
        return jsonify({'error': 'Serial já cadastrado'}), 409

    # Find or create ProductModel
    storage_gb = data.get('storage_gb') or None
    if storage_gb is not None:
        try:
            storage_gb = int(storage_gb)
        except (ValueError, TypeError):
            storage_gb = None

    product_model = ProductModel.query.filter_by(
        name=data['model_name'], storage_gb=storage_gb
    ).first()
    if not product_model:
        product_model = ProductModel(name=data['model_name'], storage_gb=storage_gb)
        db.session.add(product_model)
        db.session.flush()

    try:
        usd_cost = Decimal(str(data['usd_cost']))
    except InvalidOperation:
        return jsonify({'error': 'usd_cost inválido'}), 400

    quantity = int(data.get('quantity', 1))
    if quantity < 1:
        quantity = 1

    base_serial = data['serial']
    created_units = []

    try:
        for i in range(quantity):
            # Generate unique serial if quantity > 1
            current_serial = base_serial if quantity == 1 else f"{base_serial}-{i+1}"

            # Check if this specific serial exists
            if Unit.query.filter_by(serial=current_serial).first():
                if quantity == 1:
                    db.session.rollback()
                    return jsonify({'error': 'Serial já cadastrado'}), 409
                else:
                    current_serial = f"{base_serial}-{int(datetime.now().timestamp())}-{i+1}"

            unit = Unit(
                serial=current_serial,
                product_model_id=product_model.id,
                purchase_lot_id=lot.id,
                usd_cost=usd_cost,
                holder=data.get('holder') or None
            )
            db.session.add(unit)
            created_units.append(unit)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar unidade: {str(e)}'}), 500

    # Return the first created unit as response, the rest will update via reload
    unit = created_units[0]
    base = get_base_brl(unit.usd_cost, lot.exchange_rate)
    total = get_total_cost_brl(base, unit.costs)
    return jsonify({
        'id': unit.id,
        'serial': unit.serial,
        'model_label': _model_label(product_model),
        'usd_cost': str(unit.usd_cost),
        'total_cost_brl': str(total),
        'status': unit.status.value,
        'holder': unit.holder or '',
        'lot_id': unit.purchase_lot_id
    }), 201


@bp.route('/unit/<int:id>', methods=['PATCH'])
@api_login_required
def update_unit(id):
    unit = Unit.query.get_or_404(id)
    data = request.json or {}

    if 'holder' in data:
        unit.holder = data['holder'] or None
    if 'status' in data:
        old_status = unit.status.value if hasattr(unit.status, 'value') else unit.status
        new_status = data['status']
        unit.status = new_status
        
        if new_status == 'SOLD' and old_status != 'SOLD':
            # Check if there's already a sale for this unit
            sale = Sale.query.filter_by(unit_id=unit.id).first()
            if not sale:
                # Create default zero sale that can be updated later
                new_sale = Sale(
                    unit_id=unit.id,
                    sell_price_brl=Decimal('0.00'),
                    commission_brl=Decimal('0.00'),
                    channel="Estoque"
                )
                db.session.add(new_sale)

    if 'usd_cost' in data:
        try:
            unit.usd_cost = Decimal(str(data['usd_cost']))
        except InvalidOperation:
            return jsonify({'error': 'usd_cost inválido'}), 400

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar: {str(e)}'}), 500
    return jsonify({'success': True})


@bp.route('/unit/<int:id>/sell', methods=['POST'])
@api_login_required
def api_sell_unit(id):
    data = request.json or {}
    try:
        sell_price_brl = Decimal(str(data['sell_price_brl']))
        commission_brl = Decimal(str(data.get('commission_brl', '0.00')))
    except (InvalidOperation, KeyError):
        return jsonify({'error': 'Valores inválidos'}), 400

    channel = data.get('channel')
    notes = data.get('notes')

    try:
        sale = sell_unit(id, sell_price_brl, commission_brl, channel, notes)
        return jsonify({'success': True, 'sale_id': sale.id})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Costs ──────────────────────────────────────────────────────────────────────

@bp.route('/unit/<int:id>/costs', methods=['GET'])
@api_login_required
def get_unit_costs(id):
    unit = Unit.query.get_or_404(id)
    costs = []
    for c in unit.costs:
        costs.append({
            'id': c.id,
            'cost_type': c.cost_type.value,
            'brl_value': str(c.brl_value),
            'source': c.source.value,
            'notes': c.notes or ''
        })
    return jsonify({'data': costs})


@bp.route('/unit/<int:id>/costs', methods=['POST'])
@api_login_required
def add_unit_cost(id):
    Unit.query.get_or_404(id)
    data = request.json or {}

    if not data.get('cost_type'):
        return jsonify({'error': 'cost_type obrigatório'}), 400
    if not data.get('brl_value'):
        return jsonify({'error': 'brl_value obrigatório'}), 400

    try:
        brl_value = Decimal(str(data['brl_value']))
    except InvalidOperation:
        return jsonify({'error': 'brl_value inválido'}), 400

    try:
        cost = create_manual_cost(id, data['cost_type'], brl_value, data.get('notes'))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({
        'id': cost.id,
        'cost_type': cost.cost_type.value,
        'brl_value': str(cost.brl_value),
        'source': cost.source.value,
        'notes': cost.notes or ''
    }), 201


@bp.route('/cost/<int:id>', methods=['DELETE'])
@api_login_required
def delete_cost(id):
    cost = UnitCost.query.get_or_404(id)
    if cost.source == CostSource.ALLOCATED:
        return jsonify({'error': 'Custos rateados não podem ser removidos individualmente. Use o re-rateio do lote.'}), 400
    db.session.delete(cost)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover custo: {str(e)}'}), 500
    return jsonify({'success': True})


# ── Lots ───────────────────────────────────────────────────────────────────────

@bp.route('/lots', methods=['GET'])
@api_login_required
def get_lots():
    lots = PurchaseLot.query.options(
        joinedload(PurchaseLot.units).joinedload(Unit.costs)
    ).order_by(PurchaseLot.purchased_at.desc()).all()

    data = []
    for lot in lots:
        unit_count = len(lot.units)
        total_usd = sum(u.usd_cost for u in lot.units) if lot.units else Decimal('0.00')
        total_brl = Decimal('0.00')
        for u in lot.units:
            base = get_base_brl(u.usd_cost, lot.exchange_rate)
            total_brl += get_total_cost_brl(base, u.costs)

        data.append({
            'id': lot.id,
            'purchased_at': lot.purchased_at.strftime('%Y-%m-%d'),
            'supplier': lot.supplier,
            'exchange_rate': str(lot.exchange_rate),
            'notes': lot.notes or '',
            'unit_count': unit_count,
            'total_usd': str(total_usd),
            'total_brl': str(total_brl)
        })
    return jsonify({'data': data})


@bp.route('/lots', methods=['POST'])
@api_login_required
def create_lot():
    data = request.json or {}
    if not data.get('supplier'):
        return jsonify({'error': 'Fornecedor obrigatório'}), 400
    if not data.get('exchange_rate'):
        return jsonify({'error': 'Câmbio obrigatório'}), 400

    try:
        exchange_rate = Decimal(str(data['exchange_rate']))
    except InvalidOperation:
        return jsonify({'error': 'Câmbio inválido'}), 400

    purchased_at = datetime.utcnow()
    if data.get('purchased_at'):
        try:
            purchased_at = datetime.strptime(data['purchased_at'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Data inválida (use YYYY-MM-DD)'}), 400

    lot = PurchaseLot(
        supplier=data['supplier'],
        exchange_rate=exchange_rate,
        purchased_at=purchased_at,
        notes=data.get('notes') or None
    )
    db.session.add(lot)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar lote: {str(e)}'}), 500

    return jsonify({
        'id': lot.id,
        'purchased_at': lot.purchased_at.strftime('%Y-%m-%d'),
        'supplier': lot.supplier,
        'exchange_rate': str(lot.exchange_rate),
        'notes': lot.notes or '',
        'unit_count': 0,
        'total_usd': '0.00',
        'total_brl': '0.00'
    }), 201


@bp.route('/lot/<int:id>/units', methods=['GET'])
@api_login_required
def get_lot_units(id):
    PurchaseLot.query.get_or_404(id)
    units = Unit.query.options(
        joinedload(Unit.product_model),
        joinedload(Unit.costs)
    ).filter_by(purchase_lot_id=id).all()

    lot = PurchaseLot.query.get(id)
    data = []
    for u in units:
        base = get_base_brl(u.usd_cost, lot.exchange_rate)
        total = get_total_cost_brl(base, u.costs)
        data.append({
            'id': u.id,
            'serial': u.serial,
            'model_label': _model_label(u.product_model),
            'usd_cost': str(u.usd_cost),
            'total_cost_brl': str(total),
            'status': u.status.value,
            'holder': u.holder or ''
        })
    return jsonify({'data': data})


@bp.route('/lot/<int:id>/allocate', methods=['POST'])
@api_login_required
def api_allocate_lot(id):
    data = request.json or {}
    try:
        run_id = allocate_lot_costs(id, data)
        return jsonify({'success': True, 'allocation_run_id': run_id})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ── Sales ──────────────────────────────────────────────────────────────────────

@bp.route('/sales', methods=['GET'])
@api_login_required
def get_sales():
    sales = Sale.query.options(
        joinedload(Sale.unit).joinedload(Unit.product_model),
        joinedload(Sale.unit).joinedload(Unit.purchase_lot),
        joinedload(Sale.unit).joinedload(Unit.costs)
    ).order_by(Sale.sold_at.desc()).all()

    data = []
    for s in sales:
        u = s.unit
        base = get_base_brl(u.usd_cost, u.purchase_lot.exchange_rate)
        total_cost = get_total_cost_brl(base, u.costs)
        profit = get_net_profit(s.sell_price_brl, total_cost, s.commission_brl)
        data.append({
            'id': s.id,
            'sold_at': s.sold_at.strftime('%Y-%m-%d'),
            'serial': u.serial,
            'model_label': _model_label(u.product_model),
            'sell_price_brl': str(s.sell_price_brl),
            'total_cost_brl': str(total_cost),
            'commission_brl': str(s.commission_brl),
            'net_profit': str(profit),
            'channel': s.channel or '',
            'notes': s.notes or ''
        })
    return jsonify({'data': data})

@bp.route('/sale/<int:id>', methods=['PATCH'])
@api_login_required
def update_sale(id):
    sale = Sale.query.get_or_404(id)
    data = request.json or {}

    if 'sell_price_brl' in data:
        try:
            sale.sell_price_brl = Decimal(str(data['sell_price_brl']))
        except InvalidOperation:
            return jsonify({'error': 'Preço inválido'}), 400
            
    if 'commission_brl' in data:
        try:
            sale.commission_brl = Decimal(str(data['commission_brl']))
        except InvalidOperation:
            return jsonify({'error': 'Comissão inválida'}), 400

    if 'channel' in data:
        sale.channel = data['channel'] or None

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar venda: {str(e)}'}), 500
    return jsonify({'success': True})


# ── KPIs ───────────────────────────────────────────────────────────────────────

@bp.route('/kpis', methods=['GET'])
@api_login_required
def get_kpis():
    units = Unit.query.options(
        joinedload(Unit.costs),
        joinedload(Unit.purchase_lot)
    ).all()

    stock_count = 0
    stock_value = Decimal('0.00')

    for u in units:
        if u.status.value == "AVAILABLE":
            stock_count += 1
            base = get_base_brl(u.usd_cost, u.purchase_lot.exchange_rate)
            stock_value += get_total_cost_brl(base, u.costs)

    sales = Sale.query.options(
        joinedload(Sale.unit).joinedload(Unit.purchase_lot),
        joinedload(Sale.unit).joinedload(Unit.costs)
    ).all()

    net_profit = Decimal('0.00')
    total_revenue = Decimal('0.00')

    for s in sales:
        u = s.unit
        base = get_base_brl(u.usd_cost, u.purchase_lot.exchange_rate)
        total_cost = get_total_cost_brl(base, u.costs)
        profit = get_net_profit(s.sell_price_brl, total_cost, s.commission_brl)
        net_profit += profit
        total_revenue += s.sell_price_brl

    net_margin = get_net_margin(net_profit, total_revenue) if total_revenue > 0 else Decimal('0.00')

    return jsonify({
        'stock_count': stock_count,
        'stock_value': str(stock_value),
        'sales_count': len(sales),
        'net_profit': str(net_profit),
        'net_margin': str(net_margin)
    })


# ── WhatsApp ───────────────────────────────────────────────────────────────────

@bp.route('/unit/<int:id>/whatsapp', methods=['GET'])
@api_login_required
def get_whatsapp_text(id):
    unit = Unit.query.options(
        joinedload(Unit.product_model),
        joinedload(Unit.sale)
    ).get_or_404(id)

    model = unit.product_model
    storage = f"{model.storage_gb}GB" if model.storage_gb else ""
    price_line = f"R$ {unit.sale.sell_price_brl}" if unit.sale else "R$ --"

    text = f"📱 {model.name}"
    if storage:
        text += f"\n💾 {storage}"
    text += f"\n💰 {price_line}"
    text += "\n\nProduto disponível."

    return jsonify({'text': text})


# ── Helpers ────────────────────────────────────────────────────────────────────

def _model_label(pm):
    if pm.storage_gb:
        return f"{pm.name} {pm.storage_gb}GB"
    return pm.name
