from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Owner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    pets = db.relationship('Pet', backref='owner', lazy=True, cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='owner', lazy=True)

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    card_number = db.Column(db.String(50), unique=True, nullable=False)
    species = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    coloration = db.Column(db.String(100))
    birth_date = db.Column(db.Date, nullable=False)
    chronic_diseases = db.Column(db.Text, default = '')
    allergies = db.Column(db.Text, default = '')
    appointments = db.relationship('Appointment', backref='pet', lazy=True)
    vaccinations = db.relationship('Vaccination', backref='pet', lazy=True)  # Связь с вакцинациями
    def pet_age(self):
        today = datetime.today().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    def vaccination_age(self, vaccination_date):
        """Возраст на момент вакцинации в формате 'X г Y м Z д' с пропуском нулевых значений"""
        delta = relativedelta(vaccination_date, self.birth_date)
        age_parts = []
        if delta.years > 0:
            age_parts.append(f"{delta.years} г")
        if delta.months > 0:
            age_parts.append(f"{delta.months} м")
        if delta.days > 0:
            age_parts.append(f"{delta.days} д")
        return " ".join(age_parts) if age_parts else "0 д"
    def pet_formatted_age(self):
        delta = relativedelta(datetime.today().date(), self.birth_date)
        age_parts = []
        if delta.years > 0:
            age_parts.append(f"{delta.years} г")
        if delta.months > 0:
            age_parts.append(f"{delta.months} м")
        if delta.days > 0:
            age_parts.append(f"{delta.days} д")
        return " ".join(age_parts) if age_parts else "0 д"

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_date = db.Column(db.String(10), nullable=False)  # Дата приёма
    time = db.Column(db.String(5), nullable=False)  # Время приёма
    duration = db.Column(db.Integer, nullable=False, default=30)  # Длительность в минутах
    description = db.Column(db.String(500))
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)  # Для повторных приёмов
    recurring_type = db.Column(db.String(50))  # Тип повторного приёма, например "10 дней", "1 год" и т.д.
    treatments = db.relationship('AppointmentTreatment', backref='appointment', cascade='all, delete-orphan')
    def total_cost(self):
        return sum(t.total_price for t in self.treatments)
    def __repr__(self):
        return f'<Appointment {self.appointment_date} {self.time} - {self.pet.name}>'

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Vaccination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vaccine_name = db.Column(db.String(100), nullable=False)
    date_administered = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date, nullable=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    vaccination_type = db.Column(db.String(50), nullable=False)
    dose_ml = db.Column(db.Float)
    previous_vaccination_date = db.Column(db.Date, nullable=True)
    
    # Делаем эти поля необязательными
    owner_name = db.Column(db.String(150), nullable=True)
    owner_address = db.Column(db.String(250), nullable=True)
    pet_species = db.Column(db.String(50), nullable=True)
    pet_breed = db.Column(db.String(100), nullable=True)
    pet_card_number = db.Column(db.String(50), nullable=True)
    pet_age = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Vaccination {self.vaccine_name} for {self.pet.name}>'

class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)  # Название назначения
    category = db.Column(db.String(50), nullable=False)  # Вакцина, Лекарство, Процедура
    dosage = db.Column(db.String(50))  # Стандартная дозировка (например "1 мл")
    unit = db.Column(db.String(20), nullable=False)  # Единица измерения (мл, г, таблетка)
    price = db.Column(db.Float, nullable=False)  # Цена за единицу
    description = db.Column(db.Text)  # Дополнительное описание
    def __repr__(self):
        return f'<Treatment {self.name} ({self.price} руб./{self.unit})>'
    
class AppointmentTreatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatment.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, default='')
    treatment = db.relationship('Treatment', lazy='joined')  # joined загрузка для уменьшения запросов