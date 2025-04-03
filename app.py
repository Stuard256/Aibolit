from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response  
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from models import db, Owner, Pet, Appointment, Note, Vaccination, Treatment, TreatmentItem, TreatmentType, AppointmentTreatment  # Импортируем модели
import logging
import pdfkit
from docxtpl import DocxTemplate
import io
from forms import TreatmentCalculatorForm , TreatmentForm
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

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

@app.route('/treatment_calculator', methods=['GET', 'POST'])
def treatment_calculator():
    form = TreatmentCalculatorForm()
    treatments = []
    total = 0
    pet_id = None
    
    if request.method == 'POST':
        if 'treatment_search' in request.form:
            # Поиск назначений
            search_term = request.form['treatment_search']
            treatments_found = TreatmentItem.query.filter(
                TreatmentItem.name.ilike(f'%{search_term}%')
            ).limit(10).all()
            return jsonify([{
                'id': t.id,
                'name': t.name,
                'default_dosage': t.default_dosage,
                'unit_price': t.unit_price,
                'unit_measure': t.unit_measure
            } for t in treatments_found])
        
        elif 'add_treatment' in request.form:
            # Добавление назначения в список
            treatment_id = request.form.get('treatment_id')
            quantity = float(request.form.get('quantity', 1))
            
            treatment = TreatmentItem.query.get(treatment_id)
            if treatment:
                treatments.append({
                    'id': treatment.id,
                    'name': treatment.name,
                    'quantity': quantity,
                    'unit_price': treatment.unit_price,
                    'unit_measure': treatment.unit_measure,
                    'total': quantity * treatment.unit_price
                })
                total = sum(t['total'] for t in treatments)
    
    return render_template('treatment_calculator.html', 
                         form=form,
                         treatments=treatments,
                         total=total,
                         pet_id=pet_id)

@app.route('/treatment_search')
def treatment_search():
    term = request.args.get('term', '')
    treatments = Treatment.query.filter(
        Treatment.name.ilike(f'%{term}%')
    ).limit(10).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'dosage': t.dosage,
        'price': t.price,
        'unit': t.unit
    } for t in treatments])

@app.route('/pet_search')
def pet_search():
    term = request.args.get('term', '')
    pets = Pet.query.join(Owner).filter(
        Pet.name.ilike(f'%{term}%') | 
        Pet.card_number.ilike(f'%{term}%')
    ).limit(10).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'card_number': p.card_number,
        'owner': {'name': p.owner.name}
    } for p in pets])

@app.route('/save_treatments', methods=['POST'])
def save_treatments():
    data = request.json
    pet_id = data.get('pet_id')
    treatments = data.get('treatments')
    
    if not pet_id:
        return jsonify({'error': 'Не выбран питомец'}), 400
    
    try:
        # Создаем новый прием
        appointment = Appointment(
            appointment_date=datetime.now().strftime('%Y-%m-%d'),
            time=datetime.now().strftime('%H:%M'),
            pet_id=pet_id,
            owner_id=Pet.query.get(pet_id).owner_id,
            description="Назначения из калькулятора"
        )
        db.session.add(appointment)
        db.session.flush()  # Получаем ID нового приема
        
        # Добавляем назначения
        for treatment in treatments:
            at = AppointmentTreatment(
                appointment_id=appointment.id,
                treatment_item_id=treatment['id'],
                quantity=treatment['quantity'],
                total_price=treatment['total'],
                notes=treatment.get('notes', '')
            )   
            db.session.add(at)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@app.route('/add_treatment', methods=['GET', 'POST'])
def add_treatment():
    form = TreatmentForm()
    
    if form.validate_on_submit():
        try:
            treatment = Treatment(
                name=form.name.data,
                category=form.category.data,
                dosage=form.dosage.data,
                unit=form.unit.data,
                price=form.price.data,
                description=form.description.data
            )
            db.session.add(treatment)
            db.session.commit()
            flash('Назначение успешно добавлено!', 'success')
            return redirect(url_for('list_treatments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении назначения: {str(e)}', 'danger')
    
    return render_template('add_treatment.html', form=form)

@app.route('/treatments')
def list_treatments():
    treatments = Treatment.query.order_by(Treatment.name).all()
    return render_template('treatments.html', treatments=treatments)

@app.route('/generate_report', methods=['POST'])
def generate_report():
    report_type = request.form.get('report_type')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d') 
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')

    previous_day = start_date - timedelta(days=1)
    
    if report_type == 'rabies':
        # Получаем вакцинации от бешенства за период
        vaccinations = db.session.query(Vaccination, Owner, Pet)\
            .join(Owner, Vaccination.owner_id == Owner.id)\
            .join(Pet, Vaccination.pet_id == Pet.id)\
            .filter(
                Vaccination.vaccination_type == 'Бешенство',
                Vaccination.date_administered >= previous_day,
                Vaccination.date_administered <= end_date
            )\
            .order_by(Vaccination.date_administered)\
            .all()
        
        report_data = []
        for idx, (vacc, owner, pet) in enumerate(vaccinations, 1):
            prev_vacc = Vaccination.query.filter(
                Vaccination.pet_id == pet.id,
                Vaccination.vaccination_type == 'Бешенство',
                Vaccination.date_administered < vacc.date_administered
            ).order_by(Vaccination.date_administered.desc()).first()
            
            # Получаем возраст на дату вакцинации
            age_str = pet.vaccination_age(vacc.date_administered)
            
            report_data.append({
                'num': idx,
                'date': vacc.date_administered.strftime('%d.%m.%Y'),
                'owner': owner.name,
                'address': owner.address,
                'animal': pet.species,
                'breed': pet.breed,
                'age': age_str,  # Формат "X г Y м Z д" без нулевых значений
                'prev_vaccination': prev_vacc.date_administered.strftime('%d.%m.%Y') if prev_vacc else '',
                'dose': f"{vacc.dose_ml or 1.0}"
            })
        # Формируем HTML отчета с альбомной ориентацией
        report_html = render_template(
            'rabies_report.html',
            report_data=report_data,
            start_date=start_date.strftime('%d.%m.%Y'),
            end_date=end_date.strftime('%d.%m.%Y')
        )
        
        # Параметры для PDF (альбомная ориентация)
        options = {
            'page-size': 'A4',
            'orientation': 'Landscape',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': 'UTF-8',
        }
        
        # Генерируем PDF
        pdf = pdfkit.from_string(report_html, False, configuration=config, options=options)
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=rabies_report_{start_date.date()}_{end_date.date()}.pdf'
        return response
    
    return "Отчёт по всем вакцинациям (в разработке)"

@app.route('/vaccinations')
def vaccinations():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Vaccination.query
    
    if search:
        query = query.filter(
            Vaccination.vaccine_name.ilike(f'%{search}%') |
            Vaccination.owner_name.ilike(f'%{search}%')
        )
    
    vaccinations = query.order_by(Vaccination.date_administered.desc()).paginate(page=page, per_page=10)
    
    return render_template('vaccinations.html', vaccinations=vaccinations)

@app.route('/vaccination/new', methods=['GET', 'POST'])
def new_vaccination():
    if request.method == 'POST':
        try:
            owner_id = request.form.get('owner_id')
            pet_id = request.form.get('pet_id')
            
            # Получаем владельца и животное из базы
            owner = Owner.query.get(owner_id)
            pet = Pet.query.get(pet_id)
            
            if not owner or not pet:
                flash('Владелец или животное не найдены', 'error')
                return redirect(request.url)
            
            # Рассчитываем возраст животного
            today = date.today()
            pet_age = today.year - pet.birth_date.year - ((today.month, today.day) < (pet.birth_date.month, pet.birth_date.day))
            
            vaccination = Vaccination(
                vaccine_name=request.form['vaccine_name'],
                date_administered=datetime.strptime(request.form['date_administered'], '%Y-%m-%d').date(),
                vaccination_type=request.form['vaccination_type'],
                dose_ml=float(request.form['dose_ml']) if request.form['dose_ml'] else None,
                previous_vaccination_date=datetime.strptime(request.form['previous_vaccination_date'], '%Y-%m-%d').date() if request.form['previous_vaccination_date'] else None,
                next_due_date=datetime.strptime(request.form['next_due_date'], '%Y-%m-%d').date() if request.form['next_due_date'] else None,
                pet_id=pet_id,
                owner_id=owner_id,
                # Заполняем дополнительные поля
                owner_name=owner.name,
                owner_address=owner.address,
                pet_species=pet.species,
                pet_breed=pet.breed,
                pet_card_number=pet.card_number,
                pet_age=pet_age
            )
            
            db.session.add(vaccination)
            db.session.commit()
            flash('Вакцинация успешно добавлена!', 'success')
            return redirect(url_for('vaccinations'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении вакцинации: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('vaccination_form.html')

@app.route('/vaccination/edit/<int:id>', methods=['GET', 'POST'])
def edit_vaccination(id):
    vaccination = Vaccination.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Обновляем основные поля
            vaccination.vaccine_name = request.form['vaccine_name']
            vaccination.date_administered = datetime.strptime(request.form['date_administered'], '%Y-%m-%d').date()
            vaccination.vaccination_type = request.form['vaccination_type']
            vaccination.dose_ml = float(request.form['dose_ml']) if request.form['dose_ml'] else None
            vaccination.previous_vaccination_date = datetime.strptime(request.form['previous_vaccination_date'], '%Y-%m-%d').date() if request.form['previous_vaccination_date'] else None
            vaccination.next_due_date = datetime.strptime(request.form['next_due_date'], '%Y-%m-%d').date() if request.form['next_due_date'] else None
            
            # Если изменился владелец или животное
            if vaccination.owner_id != int(request.form['owner_id']) or vaccination.pet_id != int(request.form['pet_id']):
                owner = Owner.query.get(request.form['owner_id'])
                pet = Pet.query.get(request.form['pet_id'])
                
                if not owner or not pet:
                    flash('Владелец или животное не найдены', 'error')
                    return redirect(request.url)
                
                vaccination.owner_id = owner.id
                vaccination.pet_id = pet.id
                vaccination.owner_name = owner.name
                vaccination.owner_address = owner.address
                vaccination.pet_species = pet.species
                vaccination.pet_breed = pet.breed
                vaccination.pet_card_number = pet.card_number
                
                # Пересчитываем возраст
                today = date.today()
                vaccination.pet_age = today.year - pet.birth_date.year - ((today.month, today.day) < (pet.birth_date.month, pet.birth_date.day))
            
            db.session.commit()
            flash('Вакцинация успешно обновлена!', 'success')
            return redirect(url_for('vaccinations'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении вакцинации: {str(e)}', 'danger')
            return redirect(request.url)
    
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

@app.route('/api/last_vaccination')
def get_last_vaccination():
    pet_id = request.args.get('pet_id')
    vaccine_type = request.args.get('vaccine_type')
    
    if not pet_id or not vaccine_type:
        return jsonify({})
    
    # Ищем последнюю вакцинацию этого типа для данного животного
    last_vaccination = Vaccination.query.filter(
        Vaccination.pet_id == pet_id,
        Vaccination.vaccination_type == vaccine_type
    ).order_by(Vaccination.date_administered.desc()).first()
    
    if last_vaccination:
        return jsonify({
            'date_administered': last_vaccination.date_administered.strftime('%Y-%m-%d')
        })
    
    return jsonify({})

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

@app.route('/api/pets_by_owner')
def get_pets_by_owner():
    owner_id = request.args.get('owner_id')
    if not owner_id:
        return jsonify([])
    
    # Убираем параметр term, так как теперь загружаем всех питомцев
    pets = Pet.query.filter_by(owner_id=owner_id).all()
    
    return jsonify([{'id': p.id, 'text': f"{p.name} ({p.card_number})"} for p in pets])

# API: список животных у владельца
@app.route('/api/pets')
def get_pets():
    owner_id = request.args.get('owner_id')
    pets = Pet.query.filter_by(owner_id=owner_id).all()
    return jsonify([{'id': p.id, 'name': p.name} for p in pets])
# ================================
# РАБОТА С КАРТОЧКАМИ ВЛАДЕЛЬЦОВ
# ================================

@app.route('/api/search_owners')
def search_owners():
    search_term = request.args.get('term', '').strip()
    if not search_term:
        return jsonify([])
    
    owners = Owner.query.filter(
        Owner.name.ilike(f'%{search_term}%')
    ).limit(10).all()
    
    return jsonify([{'id': o.id, 'text': o.name} for o in owners])

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

@app.route('/owners')
def owners_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Получаем все параметры поиска
    search_name = request.args.get('search_name', '').strip()
    search_pet = request.args.get('search_pet', '').strip()
    search_card = request.args.get('search_card', '').strip()
    search_phone = request.args.get('search_phone', '').strip()

    # Базовый запрос
    query = db.session.query(Owner).outerjoin(Pet)

    # Применяем фильтры
    if search_name:
        query = query.filter(Owner.name.ilike(f'%{search_name}%'))
    if search_pet:
        query = query.filter(Pet.name.ilike(f'%{search_pet}%'))
    if search_card:
        # Точное совпадение номера карточки
        query = query.filter(Pet.card_number == search_card)
    if search_phone:
        phone_digits = ''.join(filter(str.isdigit, search_phone))
        query = query.filter(Owner.phone.ilike(f'%{phone_digits}%'))

    # Пагинация
    owners_pagination = query.order_by(Owner.name)\
                            .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'owners.html',
        owners=owners_pagination.items,
        pagination=owners_pagination,
        search_name=search_name,
        search_pet=search_pet,
        search_card=search_card,
        search_phone=search_phone
    )

@app.route('/owner/delete/<int:owner_id>', methods=['POST'])
def delete_owner(owner_id):
    try:
        owner = Owner.query.get_or_404(owner_id)
        
        # Удаляем все связанные записи
        for pet in owner.pets:
            db.session.delete(pet)
        
        db.session.delete(owner)
        db.session.commit()
        flash('Владелец и все его животные успешно удалены', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')
    
    return redirect(url_for('owners_list'))

# ================================
# РАБОТА С КАРТОЧКАМИ ЖИВОТНЫХ
# ================================

# Добавление карточки животного (привязка к владельцу)
@app.route('/add_pet', methods=['GET', 'POST'])
def add_pet():
    # Получаем список владельцев в начале функции
    owners = Owner.query.limit(50).all()
    form_data = request.form if request.method == 'POST' else {}
    selected_owner = None

    if request.method == 'POST':
        owner_id = request.form.get('owner_id')
        if not Owner.query.get(owner_id):
            flash('Выберите существующего владельца', 'error')
            return redirect(url_for('add_pet'))
        
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

    return render_template(
        'add_pet.html',
        owners=owners,  # Теперь переменная owners всегда определена
        form_data=form_data,
        selected_owner=selected_owner
    )

@app.route('/pet/delete/<int:pet_id>', methods=['POST'])
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    owner_id = pet.owner_id
    db.session.delete(pet)
    db.session.commit()
    flash('Карточка животного успешно удалена', 'success')
    return redirect(url_for('owner_card', owner_id=owner_id))

@app.route('/pet/<int:pet_id>', methods=['GET', 'POST'])
def pet_card(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    owner = pet.owner
    
    if request.method == 'POST':
        new_card_number = request.form.get('card_number')
        
        # Проверка на уникальность номера карточки
        if new_card_number != pet.card_number:
            existing_pet = Pet.query.filter_by(card_number=new_card_number).first()
            if existing_pet:
                flash('Ошибка: животное с таким номером карточки уже существует!', 'error')
                return render_template('pet_card.html', 
                                    pet=pet, 
                                    owner=owner,
                                    form_data=request.form)

        # Остальная логика обработки формы
        try:
            # Обновляем данные питомца
            pet.name = request.form['name']
            pet.card_number = new_card_number
            pet.species = request.form['species']
            pet.gender = request.form['gender']
            pet.breed = request.form['breed']
            pet.coloration = request.form['coloration']
            pet.allergies = request.form['allergies']
            pet.chronic_diseases = request.form['chronic_diseases']
            
            # Обработка даты рождения
            try:
                birth_date = datetime.strptime(request.form['birth_date'], "%d-%m-%Y").date()
            except ValueError:
                try:
                    birth_date = datetime.strptime(request.form['birth_date'], "%Y-%m-%d").date()
                except ValueError:
                    flash("Неверный формат даты рождения.", 'error')
                    return render_template('pet_card.html', pet=pet, owner=owner, form_data=request.form)
            
            pet.birth_date = birth_date
            pet.chronic_diseases = request.form['chronic_diseases']
            pet.allergies = request.form['allergies']
            
            db.session.commit()
            flash("Карточка животного обновлена!", 'success')
            return redirect(url_for('pets_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при обновлении карточки: {str(e)}", 'error')
    
    # Для GET запроса
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
    return render_template('pet_card.html', pet=pet, owner=owner, form_data=form_data)

# Список животных
@app.route('/pets')
def pets_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Получаем параметры поиска
    search_owner = request.args.get('search_owner', '').strip()
    search_pet = request.args.get('search_pet', '').strip()

    # Базовый запрос с join
    query = Pet.query.join(Owner)

    # Применяем фильтры
    if search_owner:
        query = query.filter(Owner.name.ilike(f'%{search_owner}%'))
    
    if search_pet:
        query = query.filter(Pet.name.ilike(f'%{search_pet}%'))

    # Пагинация
    pets_pagination = query.order_by(Pet.name).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )

    return render_template(
        'pets.html',
        pets=pets_pagination.items,
        pagination=pets_pagination,
        search_owner=search_owner,
        search_pet=search_pet
    )

def underscore_filter(value):
    if not value:
        return '_' * 30  # Заполняет 30 символами подчеркивания
    return value

@app.route('/print_pet_card/<int:pet_id>')
def print_pet_card(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    owner = Owner.query.get_or_404(pet.owner_id)
    
    # Загружаем ваш шаблон DOCX
    doc = DocxTemplate("card.docx")
    
    # Подготавливаем контекст для заполнения
    context = {
        'card_number': pet.card_number,
        'owner_name': owner.name,
        'address': owner.address,
        'phone': owner.phone,
        'animal_type': pet.species,
        'pet_name': pet.name,
        'breed': pet.breed,
        'color': pet.coloration,
        'birth_date': pet.birth_date.strftime('%d.%m.%Y'),
        'gender': pet.gender
    }
    
    # Заполняем шаблон
    doc.render(context)
    
    # Создаем response
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    
    response = make_response(file_stream.read())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    response.headers['Content-Disposition'] = f'attachment; filename=pet_card_{pet.id}.docx'
    return response

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

@app.cli.command("import-vac-csv")
def import_csv_command():
    """Импорт данных о вакцинах из CSV файла"""
    try:
        from csv_importer import import_vaccinations  # Вынесем импортер в отдельный файл
        import_vaccinations('vac_for_test2.csv')
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
    app.run(host='0.0.0.0', port=5000, debug=True)
