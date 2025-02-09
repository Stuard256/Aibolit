from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import json

app = Flask(__name__)
# Настройка подключения к базе данных SQLite (файл базы: vet_clinic.db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vet_clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Замените на надёжное значение
db = SQLAlchemy(app)

# ================================
# МОДЕЛИ БАЗЫ ДАННЫХ
# ================================

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

with app.app_context():
    db.create_all()

# ================================
# ГЛАВНАЯ СТРАНИЦА – КАЛЕНДАРЬ И ЗАМЕТКИ АДМИНИСТРАТОРА
# ================================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Если добавляется заметка администратора
        if 'admin_note' in request.form:
            note_content = request.form['admin_note']
            if note_content.strip():
                new_note = Note(content=note_content.strip())
                db.session.add(new_note)
                db.session.commit()
                flash("Заметка успешно добавлена!")
        return redirect(url_for('index'))
    
    # Загружаем заметки для отображения
    notes = Note.query.order_by(Note.timestamp.desc()).all()
    return render_template('index.html', notes=notes)

@app.route('/delete_note/<int:note_id>')
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/api/appointments')
def get_appointments():
    appointments = Appointment.query.all()
    return jsonify([
        {'id': a.id,
         'title': f"{Pet.query.get(a.pet_id).name} ({Owner.query.get(a.owner_id).name})",
         'start': f"{a.appointment_date}T{a.time}",
         'end': calculate_end_time(a.appointment_date, a.time, a.duration)}  # Добавляем время окончания
        for a in appointments
    ])

def calculate_end_time(appointment_date, start_time, duration):
    """Функция для вычисления времени окончания приёма."""
    start_datetime = datetime.strptime(f"{appointment_date} {start_time}", "%Y-%m-%d %H:%M")
    end_datetime = start_datetime + timedelta(minutes=duration)
    return end_datetime.strftime("%Y-%m-%dT%H:%M")


@app.route('/appointment/<int:appointment_id>', methods=['GET', 'POST'])
def appointment_details(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if request.method == 'POST':
        # Логика для редактирования записи приёма
        appointment.appointment_date = request.form['date']
        appointment.time = request.form['time']
        appointment.description = request.form['description']
        appointment.duration = int(request.form['duration'])  # Обновляем длительность
        
        db.session.commit()
        flash('Запись успешно обновлена!', 'success')
        return redirect(url_for('index'))

    return render_template('appointment_details.html', appointment=appointment, owner=appointment.owner, pet=appointment.pet)


@app.route('/appointment/delete/<int:appointment_id>', methods=['POST'])
def appointment_delete(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Удаление записи из базы данных
    db.session.delete(appointment)
    db.session.commit()
    
    flash('Запись успешно удалена!', 'danger')
    return redirect(url_for('index'))


@app.route('/appointments')
def appointments():
    return render_template('appointments.html')



@app.route('/appointment/new', methods=['GET', 'POST'])
def new_appointment():
    owners = Owner.query.all()
    pets = []
    date = request.args.get('date', '')
    time = request.args.get('time', '')

    if request.method == 'POST':
        # Создание нового приёма
        new_appointment = Appointment(
            appointment_date=request.form['date'],
            time=request.form['time'],
            description=request.form['description'],
            owner_id=request.form['owner'],
            pet_id=request.form['pet'],
            duration=int(request.form['duration']),
        )
        db.session.add(new_appointment)
        db.session.commit()

        # Логика для повторных приёмов
        recurring_type = request.form['recurring']
        if recurring_type != 'none':
            if recurring_type == '10_days':
                next_date = datetime.strptime(new_appointment.appointment_date, "%Y-%m-%d") + timedelta(days=10)
            elif recurring_type == '21_days':
                next_date = datetime.strptime(new_appointment.appointment_date, "%Y-%m-%d") + timedelta(days=21)
            elif recurring_type == '1_year':
                next_date = datetime.strptime(new_appointment.appointment_date, "%Y-%m-%d") + timedelta(days=365)
            elif recurring_type == '1_year_birthday':
                pet_birthdate = new_appointment.pet.birth_date
                next_birthday = datetime(pet_birthdate.year + 1, pet_birthdate.month, pet_birthdate.day)
                next_date = next_birthday
            elif recurring_type == 'custom_date':
                next_date = datetime.strptime(request.form['custom_date'], "%Y-%m-%d")
            else:
                next_date = None

            if next_date:
                new_recurring_appointment = Appointment(
                    appointment_date=next_date.strftime("%Y-%m-%d"),
                    time=new_appointment.time,
                    description="Повторный приём: " + new_appointment.description,
                    owner_id=new_appointment.owner_id,
                    pet_id=new_appointment.pet_id,
                    duration=new_appointment.duration,
                    is_recurring=True,
                    recurring_type=recurring_type
                )
                db.session.add(new_recurring_appointment)
                db.session.commit()

        flash("Запись на приём успешно добавлена!")
        return redirect(url_for('index'))

    return render_template('appointment_form.html', owners=owners, pets=pets, date=date, time=time)



@app.route('/api/update_appointment/<int:appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    data = request.json
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.appointment_date = data['date']
    appointment.time = data['time']
    appointment.description = data['description']
    appointment.owner_id = int(data['owner'])
    appointment.pet_id = int(data['pet'])
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/create_appointment', methods=['POST'])
def create_appointment():
    data = request.json
    new_appt = Appointment(
    appointment_date=data['date'],
    time=data['time'],
    description=data['description'],
    owner_id=int(data['owner']),
    pet_id=int(data['pet'])
    )
    db.session.add(new_appt)
    db.session.commit()
    return jsonify({'success': True})


# API: список владельцев
@app.route('/api/owners')
def get_owners():
    owners = Owner.query.all()
    return jsonify([{'id': o.id, 'name': o.name} for o in owners])

# API: список животных у владельца
@app.route('/api/pets')
def get_pets():
    owner_id = request.args.get('owner_id')
    pets = Pet.query.filter_by(owner_id=owner_id).all()
    return jsonify([{'id': p.id, 'name': p.name} for p in pets])
# ================================
# РАБОТА С КАРТОЧКАМИ ВЛАДЕЛЬЦОВ
# ================================

# Добавление карточки владельца
@app.route('/add_owner', methods=['GET', 'POST'])
def add_owner():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        new_owner = Owner(name=name, address=address, phone=phone)
        db.session.add(new_owner)
        db.session.commit()
        flash("Карточка владельца успешно добавлена!")
        return redirect(url_for('owners_list'))
    return render_template('add_owner.html')

# Карточка владельца с возможностью редактирования
@app.route('/owner/<int:owner_id>', methods=['GET', 'POST'])
def owner_card(owner_id):
    owner = Owner.query.get_or_404(owner_id)
    if request.method == 'POST':
        owner.name = request.form['name']
        owner.address = request.form['address']
        owner.phone = request.form['phone']
        db.session.commit()
        flash("Карточка владельца обновлена!")
        return redirect(url_for('owners_list'))
    return render_template('owner_card.html', owner=owner)

# Список владельцев с поиском по ФИО
@app.route('/owners')
def owners_list():
    search_query = request.args.get('search', '')
    if search_query:
        search_query_lower = f"%{search_query.lower()}%"
        owners_filtered = Owner.query.filter(Owner.name.ilike(search_query_lower)).all()
    else:
        owners_filtered = Owner.query.all()
    return render_template('owners.html', owners=owners_filtered, search_query=search_query)

# ================================
# РАБОТА С КАРТОЧКАМИ ЖИВОТНЫХ
# ================================

# Добавление карточки животного (привязка к владельцу)
@app.route('/add_pet', methods=['GET', 'POST'])
def add_pet():
    owners = Owner.query.all()
    if not owners:
        flash("Сначала создайте карточку владельца!")
        return redirect(url_for('add_owner'))
    if request.method == 'POST':
        try:
            owner_id = int(request.form['owner_id'])
        except ValueError:
            flash("Неверный идентификатор владельца!")
            return redirect(url_for('add_pet'))
        name = request.form['name']
        card_number = request.form['card_number']
        species = request.form['species']
        gender = request.form['gender']
        breed = request.form['breed']
        coloration = request.form['coloration']
        birth_date_str = request.form['birth_date']
        try:
            # Ожидается формат "ДД-MM-ГГГГ", если не подходит – пробуем ISO ("ГГГГ-MM-ДД")
            birth_date = datetime.strptime(birth_date_str, "%d-%m-%Y").date()
        except ValueError:
            try:
                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Неверный формат даты рождения.")
                return redirect(url_for('add_pet'))
        chronic_diseases = request.form['chronic_diseases']
        allergies = request.form['allergies']
        new_pet = Pet(owner_id=owner_id, name=name, card_number=card_number, species=species,
                            gender=gender, breed=breed, coloration=coloration, birth_date=birth_date,
                            chronic_diseases=chronic_diseases, allergies=allergies)
        db.session.add(new_pet)
        db.session.commit()
        flash("Карточка животного успешно добавлена!")
        return redirect(url_for('pets_list'))
    return render_template('add_pet.html', owners=owners)

# Карточка животного с возможностью редактирования
@app.route('/pet/<int:pet_id>', methods=['GET', 'POST'])
def pet_card(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if request.method == 'POST':
        pet.name = request.form['name']
        pet.card_number = request.form['card_number']
        pet.species = request.form['species']
        pet.gender = request.form['gender']
        pet.breed = request.form['breed']
        pet.coloration = request.form['coloration']
        birth_date_str = request.form['birth_date']
        try:
            pet.birth_date = datetime.strptime(birth_date_str, "%d-%m-%Y").date()
        except ValueError:
            try:
                pet.birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Неверный формат даты рождения.")
                return redirect(url_for('pet_card', pet_id=pet_id))
        pet.chronic_diseases = request.form['chronic_diseases']
        pet.allergies = request.form['allergies']
        db.session.commit()
        flash("Карточка животного обновлена!")
        return redirect(url_for('pets_list'))
    return render_template('pet_card.html', pet=pet, owner=pet.owner)

# Список животных
@app.route('/pets')
def pets_list():
    pets = Pet.query.all()
    return render_template('pets.html', pets=pets)

# (Опционально) API для динамической загрузки списка животных по владельцу
@app.route('/api/pets/<int:owner_id>')
def get_pets_by_owner(owner_id):
    pets = Pet.query.filter_by(owner_id=owner_id).all()
    pets_list = [{'id': pet.id, 'name': pet.name} for pet in pets]
    return jsonify(pets_list)

# ================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ================================
if __name__ == '__main__':
    app.run(debug=True)
