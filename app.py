# Стандартные библиотеки
import io
import logging
import os
import re
import shutil
from datetime import date, datetime, timedelta

# Сторонние зависимости
import click
import pdfkit
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.relativedelta import relativedelta
from docxtpl import DocxTemplate
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, url_for)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

# Локальные импорты
from forms import TreatmentCalculatorForm, TreatmentForm
from models import (Appointment, AppointmentTreatment, Note, Owner, Pet,
                    Treatment, Vaccination, db)

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vet_clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'your_secret_key'  # Замените на надёжное значение
db.init_app(app)  # Инициализируем db с Flask
csrf = CSRFProtect(app)


def init_scheduler():
    scheduler = BackgroundScheduler()
    backup_interval = app.config.get('BACKUP_INTERVAL_MINUTES', 15)
    scheduler.add_job(create_backup, 'interval', minutes= backup_interval)
    scheduler.start()
    return scheduler

app.config['BACKUP_INTERVAL_MINUTES'] = 15

def create_backup():
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), 'database_backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        db_file = 'instance/vet_clinic.db'
        
        if not os.path.exists(db_file):
            return {'status': 'error', 'message': 'Database file not found'}
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'vet_clinic_backup_{timestamp}.db')
        
        shutil.copy2(db_file, backup_file)
        
        # Удаляем старые бэкапы
        backups = sorted(os.listdir(backup_dir), reverse=True)
        for old_backup in backups[10:]:
            os.remove(os.path.join(backup_dir, old_backup))
            
        app.logger.info(f"Backup created: {backup_file}")
        return {'status': 'success', 'message': f'Backup created: {backup_file}'}
    except Exception as e:
        app.logger.error(f"Backup failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def normalize_phone(phone_str):
    valid_numbers = []
    invalid_numbers = []
    
    raw_numbers = re.split(r'[\s,;|]+', phone_str.strip())
    
    for num in raw_numbers:
        if not num:
            continue
        
        clean_num = re.sub(r'\D', '', num)
        
        if not clean_num:
            invalid_numbers.append(num)
            continue
        
        converted = None
        
        if len(clean_num) == 12 and clean_num.startswith('375'):
            converted = clean_num
        
        elif len(clean_num) == 11 and clean_num.startswith('80'):
            converted = '375' + clean_num[2:]
        
        elif len(clean_num) == 9:
            converted = '375' + clean_num
        
        elif len(clean_num) == 7:
            converted = '37529' + clean_num
        
        elif len(clean_num) == 6:
            converted = '37517' + clean_num
        
        if converted and len(converted) == 12 and converted.startswith('375'):
            valid_numbers.append(converted)
        else:
            invalid_numbers.append(num)
    
    valid_numbers = list(set(valid_numbers))
    invalid_numbers = list(set(invalid_numbers))
    
    return {
        'valid': valid_numbers,
        'invalid': invalid_numbers
    }

@app.route('/', methods=['GET', 'POST'])    
def index():
    notes = Note.query.order_by(Note.timestamp.desc()).all()  # Всегда загружаем заметки
    
    if request.method == 'POST':
        note_content = request.form.get('note')  # Используем 'note' вместо 'admin_note'
        if note_content and note_content.strip():
            new_note = Note(content=note_content.strip())
            db.session.add(new_note)
            db.session.commit()
            flash("Заметка успешно добавлена!", 'success')
            return redirect(url_for('index'))
    
    return render_template('index.html', notes=notes)  # Убедитесь, что передаёте notes

@app.route('/appointment/<int:appointment_id>/treatments', methods=['POST'])
def update_appointment_treatments(appointment_id):
    data = request.json
    try:
        # Удаляем старые назначения
        AppointmentTreatment.query.filter_by(appointment_id=appointment_id).delete()
        
        # Добавляем новые
        for treatment in data['treatments']:
            at = AppointmentTreatment(
                appointment_id=appointment_id,
                treatment_id=treatment['id'],
                quantity=treatment['quantity'],
                total_price=treatment['total'],
            )
            db.session.add(at)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin_panel():
    # Проверка авторизации (добавьте свою логику проверки прав)
    # if not current_user.is_authenticated or not current_user.is_admin:
    #     return redirect(url_for('login'))
    
    # Получаем время последнего бэкапа
    backup_dir = os.path.join(os.path.dirname(__file__), 'database_backups')
    last_backup = None
    if os.path.exists(backup_dir):
        backups = sorted(os.listdir(backup_dir), reverse=True)
        if backups:
            last_backup = datetime.fromtimestamp(os.path.getmtime(os.path.join(backup_dir, backups[0])))
    
    return render_template('admin.html', last_backup=last_backup)

@app.route('/admin/backup', methods=['POST'])
def manual_backup():
    result = create_backup()
    return jsonify(result)

@app.route('/delete_treatment/<int:treatment_id>/<int:appointment_id>')
def delete_treatment(treatment_id, appointment_id):
    treatment = AppointmentTreatment.query.get_or_404(treatment_id)
    db.session.delete(treatment)
    db.session.commit()
    flash('Назначение удалено', 'success')
    return redirect(url_for('appointment_details', appointment_id=appointment_id))

@app.route('/available_card_numbers')
def available_card_numbers():
    # Получаем параметры диапазона из запроса
    range_min = request.args.get('min', default=None, type=int)
    range_max = request.args.get('max', default=None, type=int)
    
    # Получаем все существующие номера карточек
    used_numbers = [int(p.card_number) for p in Pet.query.with_entities(Pet.card_number).all() 
                   if p.card_number and p.card_number.isdigit()]
    
    if not used_numbers:
        # Если нет ни одной карточки, возвращаем сообщение
        return render_template('available_cards.html', 
                            first_25=list(range(1, 26)),
                            last_25=[],
                            has_more=False,
                            total_available=99,
                            min_number=1,
                            max_number=100,
                            range_min=range_min,
                            range_max=range_max)
    
    max_used = max(used_numbers)
    min_used = min(used_numbers)
    
    # Определяем границы диапазона
    min_range = range_min if range_min is not None else 1
    max_range = range_max if range_max is not None else max_used + 100
    
    # Создаем множество всех возможных номеров в диапазоне
    all_numbers = set(range(min_range, max_range + 1))
    used_numbers_set = set(used_numbers)
    
    # Находим свободные номера в диапазоне
    available_numbers = sorted(all_numbers - used_numbers_set)
    
    # Добавляем следующий номер после максимального, если он в диапазоне
    next_number = max_used + 1
    if next_number <= max_range:
        available_numbers.append(next_number)
    
    total_available = len(available_numbers)
    has_more = total_available > 50
    
    if has_more:
        first_25 = available_numbers[:25]
        last_25 = available_numbers[-25:]
    else:
        first_25 = available_numbers
        last_25 = []

    return render_template(
        'available_cards.html',
        first_25=first_25,
        last_25=last_25,
        has_more=has_more,
        total_available=total_available,
        min_number=min_used,
        max_number=max_used,
        range_min=range_min,
        range_max=range_max
    )

@app.route('/edit_treatment/<int:treatment_id>', methods=['GET', 'POST'])
def edit_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    form = TreatmentForm(obj=treatment)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(treatment)
            db.session.commit()
            flash('Назначение успешно обновлено!', 'success')
            return redirect(url_for('list_treatments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении назначения: {str(e)}', 'danger')
    
    return render_template('edit_treatment.html', form=form, treatment=treatment)



@app.route('/delete_treatment/<int:treatment_id>', methods=['POST'])
def delete_treatment_id(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    try:
        db.session.delete(treatment)
        db.session.commit()
        flash('Назначение успешно удалено!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении назначения: {str(e)}', 'danger')
    
    return redirect(url_for('list_treatments'))

@app.route('/treatment_calculator', methods=['GET', 'POST'])
def treatment_calculator():
    form = TreatmentCalculatorForm()
    treatments = []
    total = 0
    pet_id = request.args.get('pet_id')
    appointment_id = request.args.get('appointment_id')

    # Обработка существующего приема
    if appointment_id and appointment_id != 'new':
        appointment = Appointment.query.get(appointment_id)
        if appointment:
            pet_id = appointment.pet_id
            treatments = [{
                'id': at.treatment_id,
                'name': at.treatment.name,
                'quantity': at.quantity,
                'price': at.treatment.price,
                'unit': at.treatment.unit,
                'total': at.total_price,
                'category': at.treatment.category,  # Добавляем категорию
                'vaccine_types': at.treatment.vaccine_types  # Добавляем типы вакцин
            } for at in appointment.treatments]
            total = sum(t['total'] for t in treatments)

    if request.method == 'POST':
        if 'treatment_search' in request.form:
            # Поиск назначений (без изменений)
            pass
        
        elif 'add_treatment' in request.form:
            # Добавление лечения (добавим категорию и типы вакцин)
            treatment_id = request.form.get('treatment_id')
            quantity = float(request.form.get('quantity', 1))
            
            treatment = Treatment.query.get(treatment_id)
            if treatment:
                treatments.append({
                    'id': treatment.id,
                    'name': treatment.name,
                    'quantity': quantity,
                    'price': treatment.price,
                    'unit': treatment.unit,
                    'total': quantity * treatment.price / (treatment.dosage or 1),
                    'category': treatment.category,
                    'vaccine_types': treatment.vaccine_types
                })
                total = sum(t['total'] for t in treatments)
        
        elif 'save_treatments' in request.form:
            try:
                # Создаем или обновляем прием
                if appointment_id and appointment_id != 'new':
                    appointment = Appointment.query.get(appointment_id)
                    AppointmentTreatment.query.filter_by(appointment_id=appointment_id).delete()
                else:
                    if not pet_id:
                        flash('Не выбран питомец', 'error')
                        return redirect(request.url)
                    
                    pet = Pet.query.get(pet_id)
                    appointment = Appointment(
                        appointment_date=datetime.now().date(),
                        time=datetime.now().time(),
                        pet_id=pet_id,
                        owner_id=pet.owner_id,
                        description="Назначения из калькулятора"
                    )
                    db.session.add(appointment)
                    db.session.flush()

                # Сохраняем назначения
                for treatment in treatments:
                    at = AppointmentTreatment(
                        appointment_id=appointment.id,
                        treatment_id=treatment['id'],
                        quantity=treatment['quantity'],
                        total_price=treatment['total'],
                        notes=''
                    )
                    db.session.add(at)

                # Фиксируем изменения перед созданием вакцинаций
                db.session.commit()

                # Автоматическое создание вакцинаций
                if any(t['category'] == 'vaccines' for t in treatments):
                    try:
                        create_vaccinations_for_appointment(appointment)
                    except Exception as vaccine_error:
                        flash(f'Ошибка при создании вакцинаций: {str(vaccine_error)}', 'warning')

                flash('Назначения успешно сохранены', 'success')
                return redirect(url_for('appointment_details', appointment_id=appointment.id))

            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при сохранении: {str(e)}', 'error')
                return redirect(request.url)
    return render_template('treatment_calculator.html', 
                         form=form,
                         treatments=treatments,
                         total=total,
                         pet_id=pet_id,
                         appointment_id=appointment_id)

def create_vaccinations_for_appointment(appointment):
    try:
        appointment = Appointment.query.options(db.joinedload(Appointment.treatments)).get(appointment.id)
        
        for treatment_rel in appointment.treatments:
            treatment = treatment_rel.treatment
            
            if treatment.category == 'vaccines':
                Vaccination.create_from_treatment(
                    appointment=appointment,
                    treatment_rel=treatment_rel
                )
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

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
        pet = Pet.query.get(pet_id)
        if not pet:
            return jsonify({'error': 'Питомец не найден'}), 404

        # Создаем новый прием
        appointment = Appointment(
            appointment_date=datetime.now().date(),
            time=datetime.now().time(),
            pet_id=pet_id,
            owner_id=pet.owner_id,
            description="Назначения из калькулятора"
        )
        db.session.add(appointment)
        db.session.flush()

        # Добавляем назначения
        for treatment_data in treatments:
            treatment_obj = Treatment.query.get(treatment_data['id'])
            if not treatment_obj:
                continue

            # Создаем связь с приемом
            at = AppointmentTreatment(
                appointment_id=appointment.id,
                treatment_id=treatment_obj.id,
                quantity=treatment_data['quantity'],
                total_price=treatment_data['total'],
                notes=treatment_data.get('notes', '')
            )
            db.session.add(at)

            # Создаем отдельные вакцинации для каждого типа
            if treatment_obj.category == 'vaccines' and treatment_obj.vaccine_types:
                for vaccine_type in treatment_obj.vaccine_types:
                    vaccination = Vaccination(
                        vaccine_name=f"{treatment_obj.name} ({vaccine_type})",
                        vaccine_type=vaccine_type,
                        date_administered=appointment.appointment_date,
                        next_due_date=appointment.appointment_date + relativedelta(years=1),
                        pet_id=pet.id,
                        owner_id=pet.owner_id,
                        dose_ml=at.quantity,
                        previous_vaccination_date=get_previous_vaccination_date(pet, vaccine_type),
                        owner_name=pet.owner.name,
                        owner_address=pet.owner.address,
                        pet_species=pet.species,
                        pet_breed=pet.breed,
                        pet_card_number=pet.card_number,
                        pet_age=pet.pet_age()
                    )
                    db.session.add(vaccination)

        db.session.commit()
        return jsonify({'success': True, 'appointment_id': appointment.id})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def get_previous_vaccination_date(pet, vaccine_name):
    last_vaccination = Vaccination.query.filter_by(
        pet_id=pet.id,
        vaccine_name=vaccine_name
    ).order_by(Vaccination.date_administered.desc()).first()
    
    return last_vaccination.date_administered if last_vaccination else None
    

@app.route('/add_treatment', methods=['GET', 'POST'])
def add_treatment():
    form = TreatmentForm()
    
    if form.validate_on_submit():
        try:
            # Проверяем, существует ли уже такое назначение
            existing_treatment = Treatment.query.filter_by(
                name=form.name.data,
                category=form.category.data,
                dosage=form.dosage.data,
                unit=form.unit.data
            ).first()
            
            if existing_treatment:
                flash('Такое назначение уже существует!', 'warning')
                return redirect(url_for('add_treatment'))
            
            vaccine_types = []
            if form.category.data == 'vaccines':
                if form.rabies_vaccine.data: vaccine_types.append('Бешенство')
                if form.viral_vaccine.data: vaccine_types.append('Вирусные')
                if form.fungal_vaccine.data: vaccine_types.append('Грибковые')


            treatment = Treatment(
            name=form.name.data,
            category=form.category.data,
            dosage=form.dosage.data,
            unit=form.unit.data,
            price=form.price.data,
            description=form.description.data,
            vaccine_types=vaccine_types if vaccine_types else None
            )
            
            db.session.add(treatment)
            db.session.commit()
            
            flash('Назначение успешно добавлено!', 'success')
            app.logger.info(f"Добавлено новое назначение: {treatment.name} (ID: {treatment.id})")
            return redirect(url_for('list_treatments'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'Ошибка при добавлении назначения: {str(e)}'
            flash(error_msg, 'danger')
            app.logger.error(error_msg, exc_info=True)
    
    return render_template('add_treatment.html', form=form)

@app.route('/treatments')
def list_treatments():
    category = request.args.get('category')
    query = Treatment.query
    if category and category != 'all':
        query = query.filter(Treatment.category == category)
    treatments = query.order_by(Treatment.category, Treatment.name).all()
    categories = db.session.query(Treatment.category).distinct().order_by(Treatment.category).all()
    categories = [c[0] for c in categories]
    
    return render_template(
        'treatments.html',
        treatments=treatments,
        categories=categories,
        active_category=category
    )

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
    
    elif report_type == 'all':
        from dateutil.relativedelta import relativedelta
        import io
        import zipfile
        from flask import send_file

        # Рассчитываем период 11 месяцев назад
        current_date = datetime.now()
        target_date = current_date - relativedelta(months=11)
        target_month = target_date.month
        target_year = target_date.year

        # Выбираем вакцинации за целевой месяц
        vaccinations = Vaccination.query.filter(
            db.extract('month', Vaccination.date_administered) == target_month,
            db.extract('year', Vaccination.date_administered) == target_year
        ).all()

        # Собираем уникальных владельцев
        owner_ids = {v.owner_id for v in vaccinations}
        owners = Owner.query.filter(Owner.id.in_(owner_ids)).all()

        # Обрабатываем телефоны
        correct_phones = []
        incorrect_phones = []
        
        for owner in owners:
            result = normalize_phone(owner.phone)
            correct_phones.extend(result['valid'])
            incorrect_phones.extend(result['invalid'])

        # Сортировка и форматирование
        correct_phones = sorted(list(set(correct_phones)))
        incorrect_phones = sorted(list(set(incorrect_phones)))

        # Создаем ZIP архив
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Файл с корректными номерами
            if correct_phones:
                zip_file.writestr(
                    'correct_phones.txt', 
                    '\n'.join(correct_phones).encode('utf-8')
                )
            
            # Файл с некорректными номерами
            if incorrect_phones:
                zip_file.writestr(
                    'incorrect_phones.txt', 
                    '\n'.join(incorrect_phones).encode('utf-8')
                )

        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'vaccination_phones_{target_date:%m_%Y}.zip'
        )
    else:
        flash('Неизвестный тип отчета', 'error')
        return redirect(url_for('vaccinations'))

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
            return render_template('pet_card.html', pet = pet , owner = owner)
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении вакцинации: {str(e)}', 'danger')
            return redirect(request.url)
    else:
        # Обрабатываем GET-параметры
        owner_id = request.args.get('owner_id')
        pet_id = request.args.get('pet_id')
        
        selected_owner = Owner.query.get(owner_id) if owner_id else None
        selected_pet = Pet.query.get(pet_id) if pet_id else None

        return render_template(
            'vaccination_form.html',
            selected_owner=selected_owner,
            selected_pet=selected_pet,
            owner_id=owner_id,
            pet_id=pet_id
        )

@app.route('/vaccination/edit/<int:id>', methods=['GET', 'POST'])
def edit_vaccination(id):
    vaccination = Vaccination.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Обновляем только изменяемые поля
            vaccination.vaccine_name = request.form['vaccine_name']
            vaccination.date_administered = datetime.strptime(request.form['date_administered'], '%Y-%m-%d').date()
            vaccination.vaccination_type = request.form['vaccination_type']
            vaccination.dose_ml = float(request.form['dose_ml']) if request.form['dose_ml'] else None
            
            # Обрабатываем необязательные даты
            vaccination.previous_vaccination_date = datetime.strptime(request.form['previous_vaccination_date'], '%Y-%m-%d').date() if request.form.get('previous_vaccination_date') else None
            vaccination.next_due_date = datetime.strptime(request.form['next_due_date'], '%Y-%m-%d').date() if request.form.get('next_due_date') else None
            
            db.session.commit()
            flash('Вакцинация успешно обновлена!', 'success')
            return redirect(url_for('vaccinations'))
            
        except ValueError as e:
            db.session.rollback()
            flash(f'Ошибка формата даты или числа: {str(e)}', 'danger')
            return redirect(request.url)
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении вакцинации: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('vaccination_form.html', vaccination=vaccination, is_edit=True)

@app.route('/vaccination/delete/<int:id>', methods=['POST'])
def delete_vaccination(id):
    vaccination = Vaccination.query.get_or_404(id)
    pet_id = vaccination.pet_id 
    pet = Pet.query.get_or_404(pet_id)
    owner = Owner.query.get_or_404(vaccination.owner_id)
    db.session.delete(vaccination)
    db.session.commit()

    flash("Запись о вакцинации успешно удалена!")
    return redirect(url_for('owner_card', owner_id=owner.id))

@app.route('/delete_note/<int:note_id>')
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/api/appointments')
def get_appointments():
    appointments = Appointment.query.all()
    events = []
    
    for a in appointments:
        pet = Pet.query.get(a.pet_id)
        owner = Owner.query.get(a.owner_id)

        description = a.description
        
        events.append({
            'id': a.id,
            'title': "",
            'start': f"{a.appointment_date}T{a.time}",
            'end': calculate_end_time(a.appointment_date, a.time, a.duration),
            'extendedProps': {
                'card_number': pet.card_number if pet else "N/A",
                'description': description,
                'owner_name': owner.name if owner else "Неизвестный владелец",
                'pet_name': pet.name if pet else "Без имени"
            }
        })
    
    return jsonify(events)

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
        return redirect(url_for('appointment_details', appointment_id=appointment.id))

    return render_template('appointment_details.html', appointment=appointment, owner=appointment.owner, pet=appointment.pet)


@app.route('/appointment/delete/<int:appointment_id>', methods=['POST'])
def appointment_delete(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    try:
        # Удаляем все связанные назначения
        AppointmentTreatment.query.filter_by(appointment_id=appointment_id).delete()
        
        # Удаляем сам приём
        db.session.delete(appointment)
        db.session.commit()
        flash('Приём успешно удалён!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении приёма: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/appointment/new', methods=['GET', 'POST'])
def new_appointment():
    # Получаем параметры из URL
    owner_id = request.args.get('owner_id')
    pet_id = request.args.get('pet_id')
    date = request.args.get('date', '')
    time = request.args.get('time', '')

    # Если переданы оба ID
    if owner_id and pet_id:
        selected_owner = Owner.query.get(owner_id)
        selected_pet = Pet.query.get(pet_id)
        if not selected_owner or not selected_pet:
            abort(404)
    else:
        selected_owner = None
        selected_pet = None

    if request.method == 'POST':
        # Используем переданные ID или данные из формы
        owner_id = request.form.get('owner_id') or selected_owner.id
        pet_id = request.form.get('pet_id') or selected_pet.id

    if request.method == 'POST':
        # Создание нового приёма
        new_appointment = Appointment(
            appointment_date=request.form['date'],
            time=request.form['time'],
            description=request.form['description'],
            owner_id=request.form['owner_id'],  # Изменили с 'owner' на 'owner_id'
            pet_id=request.form['pet_id'],     # Убедитесь, что в форме поле называется pet_id
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
        return redirect(url_for('appointment_details', appointment_id=new_appointment.id))

    return render_template('appointment_form.html', selected_owner=selected_owner,
        selected_pet=selected_pet,
        date=date,
        time=time)

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
        name = request.form['name'].strip().upper()  # Приводим к верхнему регистру
        address = request.form['address'].strip()
        phone = request.form['phone'].strip()
        
        # Проверяем, что имя не пустое
        if not name:
            flash("Ошибка: ФИО владельца не может быть пустым!", "error")
            return redirect(url_for('add_owner'))
        
        new_owner = Owner(name=name, address=address, phone=phone)
        db.session.add(new_owner)
        db.session.commit()
        
        flash("Карточка владельца успешно добавлена!", "success")
        return redirect(url_for('owner_card', owner_id=new_owner.id))
    
    return render_template('add_owner.html')

@app.route('/owner/<int:owner_id>', methods=['GET', 'POST'])
def owner_card(owner_id):
    page = request.args.get('page', 1, type=int)
    owner = Owner.query.get_or_404(owner_id)
    pets = Pet.query.filter_by(owner_id=owner_id).order_by(Pet.name)
    pagination = pets.paginate(page=page, per_page=10, error_out=False)
    
    if request.method == 'POST':
        try:
            owner.name = request.form['name'].strip().upper()
            owner.address = request.form['address'].strip()
            owner.phone = request.form['phone'].strip()
            
            if not owner.name:
                flash("Ошибка: ФИО владельца не может быть пустым!", 'danger')
                return redirect(url_for('owner_card', owner_id=owner.id))
            
            db.session.commit()
            flash("Данные владельца успешно обновлены!", 'success')
            
            return redirect(url_for('owner_card', owner_id=owner.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении: {str(e)}', 'danger')
    
    return render_template('owner_card.html', owner=owner, pagination=pagination)

@app.route('/api/search_owners_for_transfer')
def search_owners_for_transfer():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    # Ищем по имени, телефону или адресу с более подробной информацией
    owners = Owner.query.filter(
        db.or_(
            Owner.name.ilike(f'%{query}%'),
            Owner.phone.ilike(f'%{query}%'),
            Owner.address.ilike(f'%{query}%')
        )
    ).limit(20).all()
    
    return jsonify([{
        'id': owner.id,
        'name': owner.name,
        'phone': owner.phone,
        'address': owner.address,
        'pets_count': len(owner.pets)
    } for owner in owners])

@app.route('/pets/<int:pet_id>/change_owner', methods=['POST'])
def change_pet_owner(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    new_owner_id = request.form.get('new_owner_id')
    
    if not new_owner_id:
        flash('Не выбран новый владелец', 'danger')
        return redirect(url_for('pet_card', pet_id=pet_id))
    
    new_owner = Owner.query.get_or_404(new_owner_id)
    
    # Меняем владельца
    pet.owner_id = new_owner.id
    db.session.commit()
    
    flash(f'Животное успешно переведено на владельца: {new_owner.name}', 'success')
    return redirect(url_for('owner_card', owner_id=new_owner.id))

@app.route('/owners')
def owners_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    search_name = request.args.get('search_name', '').strip().upper()
    search_pet = request.args.get('search_pet', '').strip().upper()
    search_card = request.args.get('search_card', '').strip().upper()
    search_phone = request.args.get('search_phone', '').strip()

    query = db.session.query(Owner).outerjoin(Pet)

    if search_name:
        # Разбиваем поисковый запрос на части (фамилия, имя)
        search_parts = search_name.split()[:2]  # Берем только первые два слова
        
        # Создаем условия для поиска по фамилии и имени (без отчества)
        conditions = []
        for part in search_parts:
            # Ищем в начале строки (фамилия) или после пробела (имя)
            conditions.append(db.or_(
                Owner.name.like(f'{part} %'),  # Фамилия в начале
                Owner.name.like(f'% {part} %'), # Имя в середине
                Owner.name.like(f'% {part}')    # Имя в конце (если нет отчества)
            ))
        
        # Объединяем условия через AND (и фамилия, и имя должны совпадать)
        query = query.filter(db.and_(*conditions))
    
    if search_pet:
        query = query.filter(Pet.name.contains(search_pet))
    if search_card:
        query = query.filter(Pet.card_number == search_card)
    if search_phone:
        phone_digits = ''.join(filter(str.isdigit, search_phone))
        query = query.filter(Owner.phone.ilike(f'%{phone_digits}%'))

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

@app.route('/add_pet', methods=['POST'])
def add_pet():
    try:
        owner_id = request.form['owner_id']
        owner = Owner.query.get_or_404(owner_id)
        card_number = request.form['card_number'].strip()

        # Предварительная проверка номера карточки
        existing_pet = Pet.query.filter_by(card_number=card_number).first()
        if existing_pet:
            flash(f'Ошибка: Животное с номером карточки {card_number} уже существует!', 'danger')
            return redirect(url_for('owner_card', owner_id=owner_id))

        new_pet = Pet(
            owner_id=owner_id,
            name=request.form['name'],
            card_number=card_number,
            species=request.form['species'],
            gender=request.form['gender'],
            breed=request.form['breed'],
            birth_date=datetime.strptime(
                request.form['birth_date'], 
                '%Y-%m-%d' if '-' in request.form['birth_date'] else '%d-%m-%Y'
            ).date(),
            chronic_diseases=request.form.get('chronic_diseases', ''),
            allergies=request.form.get('allergies', ''),
            coloration=request.form.get('coloration', '')
        )

        db.session.add(new_pet)
        db.session.commit()
        flash('Животное успешно добавлено!', 'success')

    except IntegrityError as e:
        db.session.rollback()
        if 'card_number' in str(e.orig).lower():
            flash(f'Ошибка: Животное с номером карточки {card_number} уже существует!', 'danger')
        else:
            flash('Произошла ошибка при сохранении данных', 'danger')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении животного: {str(e)}', 'danger')

    return redirect(url_for('owner_card', owner_id=request.form['owner_id']))

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
        try:
            # Получаем данные с проверкой наличия
            pet.name = request.form.get('name', pet.name)
            new_card_number = request.form.get('card_number', pet.card_number)
            
            # Проверка уникальности номера карточки
            if new_card_number != pet.card_number:
                if Pet.query.filter_by(card_number=new_card_number).first():
                    flash('Ошибка: номер карточки уже существует!', 'error')
                    return redirect(url_for('owner_card', owner_id=owner.id))
            pet.card_number = new_card_number

            # Обработка остальных полей
            pet.species = request.form.get('species', pet.species)
            pet.gender = request.form.get('gender', pet.gender)
            pet.breed = request.form.get('breed', pet.breed)
            pet.coloration = request.form.get('coloration', pet.coloration)
            pet.allergies = request.form.get('allergies', pet.allergies)
            pet.chronic_diseases = request.form.get('chronic_diseases', pet.chronic_diseases)

            # Обработка даты рождения
            birth_date_str = request.form.get('birth_date')
            if birth_date_str:
                try:
                    pet.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash("Неверный формат даты рождения", 'error')
                    return redirect(url_for('owner_card', owner_id=owner.id))

            db.session.commit()
            flash("Карточка обновлена!", 'success')
            return redirect(url_for('owner_card', owner_id=owner.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка: {str(e)}", 'error')
            return redirect(url_for('owner_card', owner_id=owner.id))

    # GET-запросы обрабатываются отдельной страницей
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
@app.cli.command("uppercase")
def uppercase_all_owner_names():
    """Приводит все имена владельцев (Owner.name) к верхнему регистру."""
    try:
        # Вариант 1: Массовое обновление через один запрос (самый эффективный)
        # updated_count = db.session.query(Owner)\
        #     .filter(Owner.name.isnot(None))\
        #     .update({"name": db.func.upper(Owner.name)},
        #              synchronize_session=False)
        # db.session.commit()
        # print(f"✅ Успешно обновлено {updated_count} записей.")

        # Вариант 2: Альтернативный способ (если первый не работает)
        owners = Owner.query.filter(Owner.name.isnot(None)).all()
        for owner in owners:
            owner.name = owner.name.upper()
        db.session.commit()
        print(f"Успешно обновлено {len(owners)} записей.")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка: {e}")

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

@app.cli.command("import-new-csv")
def import_new_csv_command():
    """Импорт данных из CSV файла"""
    try:
        from csv_importer import import_only_new_pets  # Вынесем импортер в отдельный файл
        import_only_new_pets('animals_temp.csv')
        print("Импорт успешно завершен!")
    except Exception as e:
        print(f"Ошибка импорта: {str(e)}")
        import traceback
        traceback.print_exc()

@app.cli.command("import-owner-csv")
def import_owner_csv_command():
    """Импорт данных из CSV файла"""
    try:
        from csv_importer import import_owners_from_csv  # Вынесем импортер в отдельный файл
        import_owners_from_csv('owners_test.csv')
        print("Импорт успешно завершен!")
    except Exception as e:
        print(f"Ошибка импорта: {str(e)}")
        import traceback
        traceback.print_exc()

@app.cli.command("import-vac-csv")
def import_vac_csv_command():
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

@app.cli.command("normalize-phones")
@click.option('--dry-run', is_flag=True, help="Run without saving changes")
def normalize_phones_command(dry_run):
    """Normalize phone numbers for all owners"""
    from phone_normalizer import normalize_phone_v2
    owners = Owner.query.all()
    
    for owner in owners:
        original = owner.phone
        if not original:
            continue
            
        result = normalize_phone_v2(original)
        new_phone = ', '.join(result['valid']) if result['valid'] else original
        
        if new_phone != original:
            print(f"\nOwner ID: {owner.id}")
            print(f"Original: {original}")
            print(f"Normalized: {new_phone}")
            print(f"Invalid: {', '.join(result['invalid'])}")
            
            if not dry_run:
                owner.phone = new_phone
    
    if not dry_run:
        try:
            db.session.commit()
            print("\nChanges committed to database!")
        except Exception as e:
            db.session.rollback()
            print(f"\nError committing changes: {str(e)}")
    else:
        print("\nDry run complete. No changes saved.")

# ================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ================================

scheduler = init_scheduler()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
