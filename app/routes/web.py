from flask import Blueprint, render_template

bp = Blueprint('web', __name__)

@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', title="Dashboard")

@bp.route('/estoque')
def inventory():
    return render_template('inventory.html', title="Estoque")

@bp.route('/unidade/<int:id>')
def unit_detail(id):
    from app.models import Unit
    unit = Unit.query.get_or_404(id)
    return render_template('unit_detail.html', title=f"Detalhe Unidade {unit.serial}", unit=unit)

@bp.route('/lotes')
def lots():
    return render_template('lots.html', title="Lotes")

@bp.route('/vendas')
def sales():
    return render_template('sales.html', title="Vendas")
