from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Доступ заборонено: потрібні права Адміністратора.', 'warning')
        return redirect(url_for('main.user_dashboard'))
    return render_template('admin_dashboard.html', username=current_user.username)

@main_bp.route('/dashboard/user')
@login_required
def user_dashboard():
    if current_user.is_admin():
        flash('Доступ заборонено', 'warning')
        return redirect(url_for('main.admin_dashboard'))
    return render_template('user_dashboard.html', username=current_user.username, role=current_user.role)