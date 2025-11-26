from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import mongo
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.user_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        existing_user = mongo.db.users.find_one({"username": username})
        if existing_user:
            flash('Користувач з таким іменем вже існує.', 'danger')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)
        
        user_data = {
            'username': username,
            'password_hash': hashed_password,
            'role': 'researcher' 
        }
        mongo.db.users.insert_one(user_data)
        
        flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.user_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_doc = mongo.db.users.find_one({"username": username})

        if user_doc and check_password_hash(user_doc['password_hash'], password):
            user = User(user_doc)
            login_user(user)
            
            if user.is_admin():
                return redirect(url_for('main.admin_dashboard'))
            else:
                return redirect(url_for('main.user_dashboard'))
        else:
            flash('Невірне ім\'я користувача або пароль.', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви успішно вийшли із системи.', 'success')
    return redirect(url_for('main.index'))