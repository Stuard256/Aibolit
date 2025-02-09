from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Owner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    pets = db.relationship('Pet', backref='owner', lazy=True)
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
    chronic_diseases = db.Column(db.Text)
    allergies = db.Column(db.Text)
    appointments = db.relationship('Appointment', backref='pet', lazy=True)
    vaccinations = db.relationship('Vaccination', backref='pet', lazy=True)  # Связь с вакцинациями
    def pet_age(self):
        today = datetime.today().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))


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

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Vaccination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vaccine_name = db.Column(db.String(100), nullable=False)  # Название вакцины
    date_administered = db.Column(db.Date, nullable=False)  # Дата вакцинации
    next_due_date = db.Column(db.Date, nullable=True)  # Дата следующей вакцинации
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)  # Связь с животным
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)  # Связь с владельцем
    vaccination_type = db.Column(db.String(50), nullable=False)  # Тип вакцинации
    dose_ml = db.Column(db.Float)  # Доза вакцины в мл
    previous_vaccination_date = db.Column(db.Date, nullable=True)  # Дата предыдущей вакцинации

    # Дополнительные поля для отображения данных владельца и животного
    owner_name = db.Column(db.String(150), nullable=False)  # Имя владельца
    owner_address = db.Column(db.String(250), nullable=False)  # Адрес владельца
    pet_species = db.Column(db.String(50), nullable=False)  # Вид животного
    pet_breed = db.Column(db.String(100), nullable=False)  # Порода животного
    pet_card_number = db.Column(db.String(50), nullable=False)  # Номер жетона животного
    pet_age = db.Column(db.Integer, nullable=False)  # Возраст животного

    def __repr__(self):
        return f'<Vaccination {self.vaccine_name} for {self.pet.name}>'
