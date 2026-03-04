from flask import Blueprint, render_template, request, redirect, url_for, session

from app.auth import login_required, check_credentials

bp = Blueprint('web', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('authenticated'):
        return redirect(url_for('web.dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if check_credentials(username, password):
            session['authenticated'] = True
            next_url = request.args.get('next') or url_for('web.dashboard')
            return redirect(next_url)
        error = 'Usuário ou senha inválidos.'
    return render_template('login.html', error=error)


@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('web.login'))


@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title="Dashboard")

@bp.route('/estoque')
@login_required
def inventory():
    return render_template('inventory.html', title="Estoque")

@bp.route('/unidade/<int:id>')
@login_required
def unit_detail(id):
    from app.models import Unit
    unit = Unit.query.get_or_404(id)
    return render_template('unit_detail.html', title=f"Detalhe Unidade {unit.serial}", unit=unit)

@bp.route('/lotes')
@login_required
def lots():
    return render_template('lots.html', title="Lotes")

@bp.route('/vendas')
@login_required
def sales():
    return render_template('sales.html', title="Vendas")
