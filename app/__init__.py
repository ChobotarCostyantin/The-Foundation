from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from config import Config

# Ініціалізуємо розширення глобально, але без прив'язки до конкретного app
mongo = PyMongo()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ініціалізація розширень з конкретним app
    mongo.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = "Будь ласка, увійдіть, щоб отримати доступ."

    # Імпорт та реєстрація Blueprints (маршрутів)
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.inventory import inventory_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)

    # Імпорт моделі User для завантажувача сесій
    from app.models import User
    from bson.objectid import ObjectId

    @login_manager.user_loader
    def load_user(user_id):
        user_doc = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
        return None

    return app