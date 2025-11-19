import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "secret_key_123")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = "Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки."

class User(UserMixin):
    def __init__(self, user_data):
        self.username = user_data.get('username')
        self.password_hash = user_data.get('password_hash')
        self.role = user_data.get('role', 'researcher')
        self.id = str(user_data.get('_id'))

    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    """Завантажує користувача за його ID для сесії Flask-Login."""
    user_doc = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_doc:
        return User(user_doc)
    return None


@app.route('/')
def index():
    """Головна сторінка (використовуємо ваш landing_page.html)"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Дозволяє реєстрацію для звичайних користувачів (Дослідників)."""
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        existing_user = mongo.db.users.find_one({"username": username})
        if existing_user:
            flash('Користувач з таким іменем вже існує.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        
        user_data = {
            'username': username,
            'password_hash': hashed_password,
            'role': 'researcher' 
        }
        mongo.db.users.insert_one(user_data)
        
        flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Реалізує вхід для різних типів користувачів."""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_doc = mongo.db.users.find_one({"username": username})

        if user_doc and check_password_hash(user_doc['password_hash'], password):
            user = User(user_doc)
            login_user(user)
            
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Невірне ім\'я користувача або пароль.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Вихід із системи."""
    logout_user()
    flash('Ви успішно вийшли із системи.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard/admin')
@login_required
def admin_dashboard():
    """Домашня сторінка для Адміністратора."""
    if not current_user.is_admin():
        flash('Доступ заборонено: потрібні права Адміністратора.', 'warning')
        return redirect(url_for('user_dashboard'))
    return render_template('admin_dashboard.html', username=current_user.username)

@app.route('/dashboard/user')
@login_required
def user_dashboard():
    """Домашня сторінка для звичайного користувача (Дослідника)."""
    return render_template('user_dashboard.html', username=current_user.username, role=current_user.role)

@app.cli.command("create-admin")
def create_admin_command():
    """Команда для створення першого Адміністратора через CLI."""
    username = input("Введіть ім'я Адміністратора: ")
    password = input("Введіть пароль: ")
    
    if mongo.db.users.find_one({"username": username}):
        print(f"Користувач '{username}' вже існує.")
        return

    hashed_password = generate_password_hash(password)
    admin_data = {
        'username': username,
        'password_hash': hashed_password,
        'role': 'admin'
    }
    mongo.db.users.insert_one(admin_data)
    print(f"Адміністратор '{username}' успішно створений.")


if __name__ == '__main__':
    app.run(debug=True)