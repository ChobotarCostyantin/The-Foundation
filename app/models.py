from flask_login import UserMixin
from bson.objectid import ObjectId

# --- User Model ---
class User(UserMixin):
    def __init__(self, user_data):
        self.username = user_data.get('username')
        self.password_hash = user_data.get('password_hash')
        self.role = user_data.get('role', 'researcher')
        self.id = str(user_data.get('_id'))

    def is_admin(self):
        return self.role == 'admin'

# --- Anomaly Object Model ---
class AnomalyObject:
    def __init__(self, data):
        self._id = str(data.get('_id')) if data.get('_id') else None
        self.object_number = data.get('object_number')
        self.object_name = data.get('object_name')
        self.object_class = data.get('object_class')
        self.description = data.get('description')
        self.special_contaiment_procedures = data.get('special_contaiment_procedures')
        self.status = data.get('status', 'Under Study')
        self.discovery_date = data.get('discovery_date')
        self.assigned_researchers = data.get('assigned_researchers', [])
        # Зв'язок з камерою
        self.chamber_id = str(data.get('chamber_id')) if data.get('chamber_id') else None

    def to_bson(self):
        """Підготовка даних для запису в MongoDB"""
        return {
            "object_number": self.object_number,
            "object_name": self.object_name,
            "object_class": self.object_class,
            "description": self.description,
            "special_contaiment_procedures": self.special_contaiment_procedures,
            "status": self.status,
            "discovery_date": self.discovery_date,
            "assigned_researchers": self.assigned_researchers,
            "chamber_id": ObjectId(self.chamber_id) if self.chamber_id else None
        }

# --- Containment Chamber Model ---
class ContainmentChamber:
    def __init__(self, data):
        self._id = str(data.get('_id')) if data.get('_id') else None
        self.chamber_type = data.get('chamber_type')
        self.size_dimensions = data.get('size_dimensions')
        self.security_level = data.get('security_level')
        self.environmental_controls = data.get('environmental_controls')
        self.monitoring_equipment = data.get('monitoring_equipment')
        self.construction_materials = data.get('construction_materials')
        self.location = data.get('location')
        self.capacity = int(data.get('capacity', 1))
        self.current_occupancy = int(data.get('current_occupancy', 0))
        self.status = data.get('status', 'Active')

    def to_bson(self):
        """Підготовка даних для запису в MongoDB"""
        return {
            "chamber_type": self.chamber_type,
            "size_dimensions": self.size_dimensions,
            "security_level": self.security_level,
            "environmental_controls": self.environmental_controls,
            "monitoring_equipment": self.monitoring_equipment,
            "construction_materials": self.construction_materials,
            "location": self.location,
            "capacity": self.capacity,
            "current_occupancy": self.current_occupancy,
            "status": self.status
        }