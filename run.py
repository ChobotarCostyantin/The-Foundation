from app import create_app, mongo
from werkzeug.security import generate_password_hash

app = create_app()

# CLI Command for Admin creation
@app.cli.command("create-admin")
def create_admin_command():
    username = input("Введіть ім'я Адміністратора: ")
    password = input("Введіть пароль: ")
    
    # Ми використовуємо app.app_context(), щоб отримати доступ до БД
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
    app.run(debug=True, host='0.0.0.0')