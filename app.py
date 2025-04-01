from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from models import db, Owner, Pet, Appointment, Note, Vaccination  # Импортируем модели
import json
import csv_importer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vet_clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'your_secret_key'  # Замените на надёжное значение
db.init_app(app)  # Инициализируем db с Flask


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

@app.route('/vaccinations')
def vaccinations():
    # Получение всех записей вакцинации
    vaccinations = Vaccination.query.all()
    return render_template('vaccinations.html', vaccinations=vaccinations)

@app.route('/vaccination/new', methods=['GET', 'POST'])
def new_vaccination():
    owners = Owner.query.all()
    pets = Pet.query.all()

    if request.method == 'POST':
        owner_id = request.form['owner_id']
        pet_id = request.form['pet_id']

        owner = Owner.query.get(owner_id)
        pet = Pet.query.get(pet_id)

        # Автозаполнение данных
        new_vaccination = Vaccination(
            vaccine_name=request.form['vaccine_name'],
            # date_administered=request.form['date_administered'],
            date_administered = datetime.strptime(request.form['date_administered'], '%Y-%m-%d').date(),
            previous_vaccination_date = datetime.strptime(request.form['previous_vaccination_date'], '%Y-%m-%d').date() if request.form['previous_vaccination_date'] else None,
            next_due_date = datetime.strptime(request.form['next_due_date'], '%Y-%m-%d').date() if request.form['next_due_date'] else None,
            vaccination_type=request.form['vaccination_type'],
            dose_ml=request.form['dose_ml'],    
            # previous_vaccination_date=request.form.get('previous_vaccination_date'),
            # next_due_date=request.form.get('next_due_date'),
            pet_id=pet.id,
            owner_id=owner.id,
            owner_name=owner.name,
            owner_address=owner.address,
            pet_species=pet.species,
            pet_breed=pet.breed,
            pet_card_number=pet.card_number,
            pet_age= pet.pet_age(),
        )

        db.session.add(new_vaccination)
        db.session.commit()

        flash("Запись о вакцинации успешно добавлена!")
        return redirect(url_for('vaccinations'))

    return render_template('vaccination_form.html', owners=owners, pets=pets)

@app.route('/vaccination/edit/<int:id>', methods=['GET', 'POST'])
def edit_vaccination(id):
    vaccination = Vaccination.query.get(id)
    if request.method == 'POST':
        vaccination.vaccine_name = request.form['vaccine_name']
        vaccination.date_administered = request.form['date_administered']
        vaccination.vaccination_type = request.form['vaccination_type']
        vaccination.dose_ml = request.form['dose_ml']
        vaccination.previous_vaccination_date = request.form.get('previous_vaccination_date')

        db.session.commit()

        flash("Запись о вакцинации успешно обновлена!")
        return redirect(url_for('vaccinations'))

    return render_template('vaccination_form.html', vaccination=vaccination)

@app.route('/vaccination/delete/<int:id>', methods=['POST'])
def delete_vaccination(id):
    vaccination = Vaccination.query.get(id)
    db.session.delete(vaccination)
    db.session.commit()

    flash("Запись о вакцинации успешно удалена!")
    return redirect(url_for('vaccinations'))

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
    appointments = Appointment.query.all()
    return render_template('appointments.html', appointments=appointments)



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
    search_query = request.args.get('search', '').strip()
    search_field = request.args.get('search_field', 'name')  # По умолчанию ищем по ФИО
    
    # Базовый запрос
    query = Owner.query
    
    if search_query:
        if search_field == 'id':
            try:
                search_id = int(search_query)
                query = query.filter(Owner.id == search_id)
            except ValueError:
                # Если ввели не число для ID
                query = query.filter(False)  # Возвращаем пустой результат
        else:
            search_pattern = f"%{search_query}%"
            if search_field == 'name':
                query = query.filter(Owner.name.ilike(search_pattern))
            elif search_field == 'address':
                query = query.filter(Owner.address.ilike(search_pattern))
            elif search_field == 'phone':
                # Удаляем все нецифровые символы для поиска по телефону
                phone_digits = ''.join(filter(str.isdigit, search_query))
                if phone_digits:
                    query = query.filter(Owner.phone.ilike(f"%{phone_digits}%"))
    
    owners_filtered = query.order_by(Owner.name).all()
    
    return render_template(
        'owners.html',
        owners=owners_filtered,
        search_query=search_query,
        search_field=search_field
    )

# ================================
# РАБОТА С КАРТОЧКАМИ ЖИВОТНЫХ
# ================================

# Добавление карточки животного (привязка к владельцу)
@app.route('/add_pet', methods=['GET', 'POST'])
def add_pet():
    owners = Owner.query.all()
    if not owners:
        flash("Сначала создайте карточку владельца!", 'error')
        return redirect(url_for('add_owner'))

    if request.method == 'POST':
        form_data = {
            'owner_id': request.form.get('owner_id'),
            'name': request.form.get('name'),
            'card_number': request.form.get('card_number'),
            'species': request.form.get('species'),
            'gender': request.form.get('gender'),
            'breed': request.form.get('breed'),
            'coloration': request.form.get('coloration'),
            'birth_date': request.form.get('birth_date'),
            'chronic_diseases': request.form.get('chronic_diseases'),
            'allergies': request.form.get('allergies')
        }

        # Проверка на уникальность номера карточки
        if Pet.query.filter_by(card_number=form_data['card_number']).first():
            flash("Ошибка: животное с таким номером карточки уже существует!", 'error')
            return render_template('add_pet.html', owners=owners, form_data=form_data)

        try:
            owner_id = int(form_data['owner_id'])
        except ValueError:
            flash("Неверный идентификатор владельца!", 'error')
            return render_template('add_pet.html', owners=owners, form_data=form_data)

        try:
            birth_date_str = form_data['birth_date']
            try:
                birth_date = datetime.strptime(birth_date_str, "%d-%m-%Y").date()
            except ValueError:
                try:
                    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                except ValueError:
                    flash("Неверный формат даты рождения.", 'error')
                    return render_template('add_pet.html', owners=owners, form_data=form_data)

            new_pet = Pet(
                owner_id=owner_id,
                name=form_data['name'],
                card_number=form_data['card_number'],
                species=form_data['species'],
                gender=form_data['gender'],
                breed=form_data['breed'],
                coloration=form_data['coloration'],
                birth_date=birth_date,
                chronic_diseases=form_data['chronic_diseases'],
                allergies=form_data['allergies']
            )

            db.session.add(new_pet)
            db.session.commit()
            flash("Карточка животного успешно добавлена!", 'success')
            return redirect(url_for('pets_list'))

        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при добавлении карточки: {str(e)}", 'error')
            return render_template('add_pet.html', owners=owners, form_data=form_data)

    return render_template('add_pet.html', owners=owners, form_data={})

@app.route('/pet/<int:pet_id>', methods=['GET', 'POST'])
def pet_card(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    
    if request.method == 'POST':
        form_data = {
            'name': request.form.get('name'),
            'card_number': request.form.get('card_number'),
            'species': request.form.get('species'),
            'gender': request.form.get('gender'),
            'breed': request.form.get('breed'),
            'coloration': request.form.get('coloration'),
            'birth_date': request.form.get('birth_date'),
            'chronic_diseases': request.form.get('chronic_diseases'),
            'allergies': request.form.get('allergies')
        }

        # Проверка на уникальность номера карточки (если изменился)
        if form_data['card_number'] != pet.card_number:
            if Pet.query.filter_by(card_number=form_data['card_number']).first():
                flash("Ошибка: животное с таким номером карточки уже существует!", 'error')
                return render_template('pet_card.html', pet=pet, owner=pet.owner, form_data=form_data)

        try:
            # Обновляем данные питомца
            pet.name = form_data['name']
            pet.card_number = form_data['card_number']
            pet.species = form_data['species']
            pet.gender = form_data['gender']
            pet.breed = form_data['breed']
            pet.coloration = form_data['coloration']
            
            try:
                pet.birth_date = datetime.strptime(form_data['birth_date'], "%d-%m-%Y").date()
            except ValueError:
                try:
                    pet.birth_date = datetime.strptime(form_data['birth_date'], "%Y-%m-%d").date()
                except ValueError:
                    flash("Неверный формат даты рождения.", 'error')
                    return render_template('pet_card.html', pet=pet, owner=pet.owner, form_data=form_data)
            
            pet.chronic_diseases = form_data['chronic_diseases']
            pet.allergies = form_data['allergies']
            
            db.session.commit()
            flash("Карточка животного обновлена!", 'success')
            return redirect(url_for('pets_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при обновлении карточки: {str(e)}", 'error')
            return render_template('pet_card.html', pet=pet, owner=pet.owner, form_data=form_data)
    
    # Для GET запроса просто отображаем текущие данные питомца
    form_data = {
        'name': pet.name,
        'card_number': pet.card_number,
        'species': pet.species,
        'gender': pet.gender,
        'breed': pet.breed,
        'coloration': pet.coloration,
        'birth_date': pet.birth_date.strftime('%d-%m-%Y'),
        'chronic_diseases': pet.chronic_diseases,
        'allergies': pet.allergies
    }
    return render_template('pet_card.html', pet=pet, owner=pet.owner, form_data=form_data)

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
# КОМАНДЫ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
# ================================
@app.cli.command("import-csv")
def import_csv_command():
    """Импорт данных из CSV файла"""
    try:
        from csv_importer import import_csv  # Вынесем импортер в отдельный файл
        import_csv('test_.csv')
        print("Импорт успешно завершен!")
    except Exception as e:
        print(f"Ошибка импорта: {str(e)}")
        import traceback
        traceback.print_exc()

@app.cli.command("reset-db")
def reset_db():
    """Полный сброс и пересоздание базы данных"""
    try:
        db.drop_all()
        db.create_all()
        print("База данных успешно пересоздана!")
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

# ================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ================================
if __name__ == '__main__':
    app.run(debug=True)
