from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime
from app import mongo
from app.models import AnomalyObject, ContainmentChamber # Імпортуємо нові моделі

inventory_bp = Blueprint('inventory', __name__)

# --- Chambers Routes ---

@inventory_bp.route('/chambers')
@login_required
def chambers_list():
    if not current_user.is_admin():
        flash('У вас немає права доступу до цього ресурсу.', 'danger')
        return redirect(url_for('main.index'))
    
    # Отримуємо дані з БД і перетворюємо їх на об'єкти класу ContainmentChamber
    chambers_data = mongo.db.chambers.find()
    chambers = [ContainmentChamber(doc) for doc in chambers_data]
    return render_template('chambers_list.html', chambers=chambers)

@inventory_bp.route('/chambers/new', methods=['GET', 'POST'])
@login_required
def create_chamber():
    if not current_user.is_admin():
        flash('У вас немає права доступу до цього ресурсу.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Створюємо екземпляр моделі з даних форми
        new_chamber = ContainmentChamber({
            'chamber_type': request.form.get('chamber_type'),
            'size_dimensions': request.form.get('size_dimensions'),
            'security_level': request.form.get('security_level'),
            'environmental_controls': request.form.get('environmental_controls'),
            'monitoring_equipment': request.form.get('monitoring_equipment'),
            'construction_materials': request.form.get('construction_materials'),
            'location': request.form.get('location'), # Це поле збігається з site_name/location
            'capacity': request.form.get('capacity'),
            'status': 'Active'
        })
        
        mongo.db.chambers.insert_one(new_chamber.to_bson())
        flash('Камера успішно створена!', 'success')
        return redirect(url_for('inventory.chambers_list'))
        
    return render_template('create_chamber.html')

@inventory_bp.route('/chambers/delete/<chamber_id>')
@login_required
def delete_chamber(chamber_id):
    if not current_user.is_admin():
        flash('У вас немає права доступу до цього ресурсу.', 'danger')
        return redirect(url_for('main.index'))
    
    chamber_doc = mongo.db.chambers.find_one({"_id": ObjectId(chamber_id)})
    
    if not chamber_doc:
        flash('Камеру не знайдено.', 'danger')
        return redirect(url_for('inventory.chambers_list'))
    
    # міняємо chamber_id у об'єктів на null
    mongo.db.objects.update_many(
        {"chamber_id": ObjectId(chamber_id)},
        {"$set": {"chamber_id": None}}
    )
    
    # міняємо статус у об'єктів на "Awaiting Containment"
    mongo.db.objects.update_many(
        {"chamber_id": ObjectId(chamber_id)},
        {"$set": {"status": "Awaiting Containment"}}
    )
    
    mongo.db.chambers.delete_one({"_id": ObjectId(chamber_id)})
    
    flash('Камера успішно видалена!', 'success')
    return redirect(url_for('inventory.chambers_list'))

@inventory_bp.route('/chambers/<chamber_id>')
@login_required
def view_chamber(chamber_id):
    if not current_user.is_admin():
        flash('У вас немає права доступу до цього ресурсу.', 'danger')
        return redirect(url_for('main.index'))

    # 1. Знаходимо камеру
    chamber_doc = mongo.db.chambers.find_one({"_id": ObjectId(chamber_id)})
    if not chamber_doc:
        flash('Камеру не знайдено.', 'danger')
        return redirect(url_for('inventory.chambers_list'))
    
    chamber = ContainmentChamber(chamber_doc)

    # 2. Знаходимо всі об'єкти, які знаходяться в цій камері
    objects_cursor = mongo.db.objects.find({"chamber_id": chamber_doc['_id']})
    contained_objects = [AnomalyObject(doc) for doc in objects_cursor]

    return render_template('chamber_details.html', chamber=chamber, objects=contained_objects)

@inventory_bp.route('/chambers/edit/<chamber_id>', methods=['GET', 'POST'])
@login_required
def edit_chamber(chamber_id):
    # Перевірка прав
    if not current_user.is_admin():
        flash('У вас немає права доступу до цього ресурсу.', 'danger')
        return redirect(url_for('main.index'))

    # Отримуємо камеру
    chamber_doc = mongo.db.chambers.find_one({"_id": ObjectId(chamber_id)})
    if not chamber_doc:
        flash('Камеру не знайдено.', 'danger')
        return redirect(url_for('inventory.chambers_list'))
    
    chamber = ContainmentChamber(chamber_doc)

    if request.method == 'POST':
        try:
            new_capacity = int(request.form.get('capacity'))
        except ValueError:
            new_capacity = chamber.capacity # Якщо ввели щось не те

        # ВАЖЛИВО: Перевірка, чи не намагаємося ми зменшити місткість нижче поточної заповненості
        if new_capacity < chamber.current_occupancy:
            flash(f"Помилка: Нова місткість ({new_capacity}) менша за поточну кількість об'єктів ({chamber.current_occupancy}). Спочатку перемістіть зайві об'єкти.", 'danger')
            return redirect(url_for('inventory.edit_chamber', chamber_id=chamber_id))

        updated_data = {
            'location': request.form.get('location'),
            'chamber_type': request.form.get('chamber_type'),
            'size_dimensions': request.form.get('size_dimensions'),
            'security_level': request.form.get('security_level'),
            'environmental_controls': request.form.get('environmental_controls'),
            'monitoring_equipment': request.form.get('monitoring_equipment'),
            'construction_materials': request.form.get('construction_materials'),
            'capacity': new_capacity,
            # Додаємо можливість змінювати статус вручну (наприклад, на "Under Maintenance")
            'status': request.form.get('status') 
        }

        mongo.db.chambers.update_one(
            {"_id": ObjectId(chamber_id)},
            {"$set": updated_data}
        )

        flash('Дані камери успішно оновлено!', 'success')
        return redirect(url_for('inventory.chambers_list'))

    return render_template('edit_chamber.html', chamber=chamber)

# --- Objects Routes ---

@inventory_bp.route('/objects')
@login_required
def objects_list():
    objects_data = mongo.db.objects.find()
    objects_list = []
    
    for doc in objects_data:
        obj = AnomalyObject(doc)
        # Якщо об'єкт приписаний до камери, знаходимо її
        if obj.chamber_id:
            chamber_doc = mongo.db.chambers.find_one({"_id": ObjectId(obj.chamber_id)})
            if chamber_doc:
                obj.chamber_info = ContainmentChamber(chamber_doc)
        objects_list.append(obj)
        
    return render_template('objects_list.html', objects=objects_list)

@inventory_bp.route('/objects/new', methods=['GET', 'POST'])
@login_required
def create_object():
    if not current_user.is_admin():
        flash('У вас немає права доступу до цього ресурсу.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        chamber_id = request.form.get('chamber_id')
        
        # Створюємо об'єкт моделі
        new_object = AnomalyObject({
            'object_number': request.form.get('object_number'),
            'object_name': request.form.get('object_name'),
            'object_class': request.form.get('object_class'),
            'description': request.form.get('description'),
            'special_properties': request.form.get('special_properties'),
            'special_contaiment_procedures': request.form.get('special_contaiment_procedures'),
            'discovery_date': request.form.get('discovery_date'),
            'chamber_id': chamber_id,
            'status': 'Contained' if chamber_id else 'Discovered'
        })

        # Логіка оновлення заповненості камери
        if chamber_id:
            chamber_doc = mongo.db.chambers.find_one({"_id": ObjectId(chamber_id)})
            if chamber_doc:
                chamber = ContainmentChamber(chamber_doc)
                if chamber.current_occupancy < chamber.capacity:
                    mongo.db.chambers.update_one(
                        {"_id": ObjectId(chamber_id)},
                        {"$inc": {"current_occupancy": 1}}
                    )
                else:
                    flash('Помилка: Обрана камера переповнена!', 'danger')
                    available_chambers = [ContainmentChamber(doc) for doc in mongo.db.chambers.find({"$expr": {"$lt": ["$current_occupancy", "$capacity"]}})]
                    return render_template('create_object.html', chambers=available_chambers)

        mongo.db.objects.insert_one(new_object.to_bson())
        flash("Об'єкт зареєстровано успішно!", 'success')
        return redirect(url_for('inventory.objects_list'))

    # Завантажуємо доступні камери як об'єкти
    chambers_cursor = mongo.db.chambers.find({
        "$expr": {"$lt": ["$current_occupancy", "$capacity"]}
    })
    available_chambers = [ContainmentChamber(doc) for doc in chambers_cursor]
    
    return render_template('create_object.html', chambers=available_chambers)

@inventory_bp.route('/objects/delete/<object_id>')
@login_required
def delete_object(object_id):
    if not current_user.is_admin:
        flash('У вас немає права доступу до цього ресурсу.', 'danger')
        return redirect(url_for('main.index'))
    
    # 1. Знаходимо об'єкт перед видаленням, щоб перевірити камеру
    obj_doc = mongo.db.objects.find_one({"_id": ObjectId(object_id)})
    
    if not obj_doc:
        flash('Об\'єкт не знайдено.', 'danger')
        return redirect(url_for('inventory.objects_list'))

    # 2. Якщо об'єкт був у камері, звільняємо місце
    if obj_doc.get('chamber_id'):
        mongo.db.chambers.update_one(
            {"_id": ObjectId(obj_doc['chamber_id'])},
            {"$inc": {"current_occupancy": -1}} # Зменшуємо лічильник на 1
        )

    # 3. Видаляємо сам об'єкт
    mongo.db.objects.delete_one({"_id": ObjectId(object_id)})
    
    flash('Об\'єкт успішно видалено (декомісовано).', 'success')
    return redirect(url_for('inventory.objects_list'))

@inventory_bp.route('/objects/edit/<object_id>', methods=['GET', 'POST'])
@login_required
def edit_object(object_id):
    # Перевірка прав
    if not current_user.is_admin():
        flash('У вас немає права доступу до цього ресурсу.', 'danger')
        return redirect(url_for('main.index'))

    # Отримуємо поточний об'єкт
    obj_doc = mongo.db.objects.find_one({"_id": ObjectId(object_id)})
    if not obj_doc:
        flash("Об'єкт не знайдено.", 'danger')
        return redirect(url_for('inventory.objects_list'))
    
    obj = AnomalyObject(obj_doc)

    if request.method == 'POST':
        # Отримуємо нові дані з форми
        new_chamber_id = request.form.get('chamber_id')
        old_chamber_id = str(obj.chamber_id) if obj.chamber_id else None

        # --- Логіка зміни камери ---
        # Якщо камера змінилася (або була додана/видалена)
        if new_chamber_id != old_chamber_id:
            
            # 1. Якщо була стара камера, звільняємо місце в ній
            if old_chamber_id:
                mongo.db.chambers.update_one(
                    {"_id": ObjectId(old_chamber_id)},
                    {"$inc": {"current_occupancy": -1}}
                )

            # 2. Якщо обрана нова камера, займаємо місце (з перевіркою)
            if new_chamber_id:
                target_chamber = mongo.db.chambers.find_one({"_id": ObjectId(new_chamber_id)})
                
                # Перевіряємо, чи не переповнена нова камера
                if target_chamber and target_chamber['current_occupancy'] >= target_chamber['capacity']:
                    # Відкочуємо зміни: повертаємо об'єкт у стару камеру (візуально для користувача)
                    if old_chamber_id:
                         mongo.db.chambers.update_one(
                            {"_id": ObjectId(old_chamber_id)},
                            {"$inc": {"current_occupancy": 1}}
                        )
                    flash(f"Помилка: Камера {target_chamber.get('location')} переповнена!", 'danger')
                    return redirect(url_for('inventory.edit_object', object_id=object_id))
                
                # Якщо є місце, збільшуємо лічильник
                mongo.db.chambers.update_one(
                    {"_id": ObjectId(new_chamber_id)},
                    {"$inc": {"current_occupancy": 1}}
                )

        # --- Оновлення даних об'єкта ---
        updated_data = {
            'object_number': request.form.get('object_number'),
            'object_name': request.form.get('object_name'),
            'object_class': request.form.get('object_class'),
            'description': request.form.get('description'),
            'special_properties': request.form.get('special_properties'),
            'special_contaiment_procedures': request.form.get('special_contaiment_procedures'),
            'discovery_date': request.form.get('discovery_date'),
            'chamber_id': new_chamber_id if new_chamber_id else None,
            # Оновлюємо статус залежно від наявності камери
            'status': 'Contained' if new_chamber_id else 'Under Study' 
        }

        mongo.db.objects.update_one(
            {"_id": ObjectId(object_id)},
            {"$set": updated_data}
        )

        flash("Дані об'єкта успішно оновлено!", 'success')
        return redirect(url_for('inventory.objects_list'))

    # GET-запит: Завантажуємо дані для форми
    # Завантажуємо камери, де є місце, АБО ту камеру, в якій об'єкт зараз (щоб вона була в списку)
    chambers_cursor = mongo.db.chambers.find({
        "$or": [
            {"$expr": {"$lt": ["$current_occupancy", "$capacity"]}},
            {"_id": ObjectId(obj.chamber_id) if obj.chamber_id else None}
        ]
    })
    available_chambers = [ContainmentChamber(doc) for doc in chambers_cursor]

    return render_template('edit_object.html', obj=obj, chambers=available_chambers)