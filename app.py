#coding=utf-8
# Стандартные библиотеки
import io
import locale
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta

# Установка UTF-8 кодировки для консоли Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Для старых версий Python
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def check_and_install_dependencies():
    """
    Проверяет наличие необходимых зависимостей и устанавливает их при необходимости
    """
    # Список обязательных модулей для проверки
    required_modules = {
        'click': 'click',
        'joblib': 'joblib',
        'numpy': 'numpy',
        'pdfkit': 'pdfkit',
        'apscheduler': 'APScheduler',
        'dateutil': 'python-dateutil',
        'docxtpl': 'docxtpl',
        'flask': 'Flask',
        'flask_wtf': 'Flask-WTF',
        'sqlalchemy': 'SQLAlchemy',
        'pandas': 'pandas',
        'sklearn': 'scikit-learn'
    }
    
    missing_modules = []
    
    # Проверяем каждый модуль
    for module_name, package_name in required_modules.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append(package_name)
    
    # Если есть отсутствующие модули, устанавливаем их
    if missing_modules:
        print("[ВНИМАНИЕ] Обнаружены отсутствующие зависимости:")
        for module in missing_modules:
            print("  - {}".format(module))
        print()
        print("Устанавливаю недостающие зависимости...")
        print()
        
        try:
            # Определяем команду pip
            python_cmd = sys.executable
            pip_cmd = [python_cmd, '-m', 'pip', 'install', '--upgrade']
            
            # Сначала пытаемся установить из requirements.txt
            if os.path.exists('requirements.txt'):
                print("Устанавливаю зависимости из requirements.txt...")
                result = subprocess.run(
                    pip_cmd + ['-r', 'requirements.txt'],
                    check=False
                )
                if result.returncode == 0:
                    print("[OK] Зависимости из requirements.txt установлены")
                else:
                    print("[ВНИМАНИЕ] Ошибка при установке из requirements.txt")
            
            # Затем устанавливаем ML зависимости, если файл существует
            if os.path.exists('requirements_ml.txt'):
                print("Устанавливаю ML зависимости из requirements_ml.txt...")
                result = subprocess.run(
                    pip_cmd + ['-r', 'requirements_ml.txt'],
                    check=False
                )
                if result.returncode == 0:
                    print("[OK] ML зависимости установлены")
                else:
                    print("[ВНИМАНИЕ] Ошибка при установке ML зависимостей")
            
            # Проверяем еще раз, что ли модули установлены
            still_missing = []
            for module_name, package_name in required_modules.items():
                try:
                    __import__(module_name)
                except ImportError:
                    still_missing.append(package_name)
            
            # Если что-то все еще отсутствует, устанавливаем отдельно
            if still_missing:
                print("Устанавливаю оставшиеся модули: {}".format(', '.join(still_missing)))
                result = subprocess.run(
                    pip_cmd + still_missing,
                    check=False
                )
                if result.returncode != 0:
                    print("[ОШИБКА] Не удалось установить некоторые зависимости")
                    print()
                    print("Попробуйте установить вручную:")
                    print("  pip install -r requirements.txt")
                    print("  pip install -r requirements_ml.txt")
                    sys.exit(1)
            
            print()
            print("[OK] Все зависимости установлены. Перезапускаю приложение...")
            print()
            
            # Перезапускаем скрипт после установки зависимостей
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except Exception as e:
            print("[ОШИБКА] Не удалось установить зависимости: {}".format(e))
            print()
            print("Пожалуйста, установите зависимости вручную:")
            print("  pip install -r requirements.txt")
            print("  pip install -r requirements_ml.txt")
            sys.exit(1)

# Проверяем и устанавливаем зависимости перед импортом
check_and_install_dependencies()

# Сторонние зависимости 
import click
import joblib
import numpy as np
import pdfkit
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.relativedelta import relativedelta
from docxtpl import DocxTemplate
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, url_for, abort)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

# Локальные импорты
from forms import TreatmentCalculatorForm, TreatmentForm
from models import (Appointment, AppointmentTreatment, Note, Owner, Pet,
                    Treatment, Vaccination, db)

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Конфигурация для PDF генерации (опционально)
config = None
try:
    wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    if os.path.exists(wkhtmltopdf_path):
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        print("[OK] wkhtmltopdf найден - генерация PDF отчётов доступна")
    else:
        print("[ВНИМАНИЕ] wkhtmltopdf не найден - генерация PDF отчетов недоступна")
        print("           Скачайте с: https://wkhtmltopdf.org/downloads.html")
except Exception as e:
    error_msg = "[ВНИМАНИЕ] Ошибка инициализации wkhtmltopdf: {}".format(e)
    print(error_msg)
    print("           Генерация PDF отчетов будет недоступна")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vet_clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'your_secret_key'  # Замените на надёжное значение
db.init_app(app)  # Инициализируем db с Flask
csrf = CSRFProtect(app)

# Глобальная переменная для ML модели
ml_model = None
ml_enabled = False  # По умолчанию ML выключена

def load_ml_model():
    """Загрузка ML модели для диагностики заболеваний"""
    global ml_model
    try:
        # Пробуем загрузить взвешенную модель
        if os.path.exists('ml/models/weighted_animal_disease_model.pkl'):
            print("DEBUG: Загружаем взвешенную ML модель...")
            model_data = joblib.load('ml/models/weighted_animal_disease_model.pkl')
            ml_model = model_data
            print("DEBUG: Взвешенная модель загружена")
            print("[OK] ML модель успешно загружена")
            return True
        elif os.path.exists('ml/models/improved_animal_disease_model.pkl'):
            print("DEBUG: Загружаем улучшенную ML модель...")
            model_data = joblib.load('ml/models/improved_animal_disease_model.pkl')
            ml_model = model_data
            print("DEBUG: Улучшенная модель загружена")
            print("[OK] ML модель успешно загружена")
            return True
        elif os.path.exists('ml/models/animal_disease_model.pkl'):
            print("DEBUG: Загружаем стандартную ML модель...")
            model_data = joblib.load('ml/models/animal_disease_model.pkl')
            
            # Проверяем структуру загруженных данных
            if isinstance(model_data, dict):
                ml_model = model_data
                print("DEBUG: Модель загружена как словарь")
            else:
                # Если это старая версия модели
                ml_model = model_data
                print("DEBUG: Модель загружена как объект")
            
            print("[OK] ML модель успешно загружена")
            return True
        else:
            print("[ВНИМАНИЕ] ML модель не найдена. Создайте модель с помощью ml/train_model.py")
            return False
    except Exception as e:
        error_msg = "[ВНИМАНИЕ] Ошибка при загрузке ML модели: {}".format(e)
        print(error_msg)
        import traceback
        traceback.print_exc()
        return False

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
        backup_file = os.path.join(backup_dir, 'vet_clinic_backup_{}.db'.format(timestamp))
        
        shutil.copy2(db_file, backup_file)
        
        # Удаляем старые бэкапы
        backups = sorted(os.listdir(backup_dir), reverse=True)
        for old_backup in backups[10:]:
            os.remove(os.path.join(backup_dir, old_backup))
            
        app.logger.info("Backup created: {}".format(backup_file))
        return {'status': 'success', 'message': 'Backup created: {}'.format(backup_file)}
    except Exception as e:
        app.logger.error("Backup failed: {}".format(str(e)))
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
        
        # Создаем вакцинации для вакцин (до commit)
        appointment = Appointment.query.get(appointment_id)
        create_vaccinations_for_appointment(appointment)
        
        # Коммитим все изменения вместе (treatments + vaccinations)
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
            flash('Ошибка при обновлении назначения: {}'.format(str(e)), 'danger')
    
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
        flash('Ошибка при удалении назначения: {}'.format(str(e)), 'danger')
    
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

                # Автоматическое создание вакцинаций (до commit)
                if any(t['category'] == 'vaccines' for t in treatments):
                    try:
                        create_vaccinations_for_appointment(appointment)
                    except Exception as vaccine_error:
                        flash('Ошибка при создании вакцинаций: {}'.format(str(vaccine_error)), 'warning')

                # Коммитим все изменения вместе (appointment + treatments + vaccinations)
                db.session.commit()

                flash('Назначения успешно сохранены', 'success')
                return redirect(url_for('appointment_details', appointment_id=appointment.id))

            except Exception as e:
                db.session.rollback()
                flash('Ошибка при сохранении: {}'.format(str(e)), 'error')
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
            
            if treatment.category == 'vaccines' and treatment.vaccine_types:
                # Создаем отдельную запись для каждого типа вакцины
                for vaccine_type in treatment.vaccine_types:
                    vaccination = Vaccination(
                        vaccine_name="{} ({})".format(treatment.name, vaccine_type),
                        vaccination_type=vaccine_type,
                        date_administered=datetime.strptime(appointment.appointment_date, '%Y-%m-%d').date() if isinstance(appointment.appointment_date, str) else appointment.appointment_date,
                        next_due_date=(datetime.strptime(appointment.appointment_date, '%Y-%m-%d').date() + relativedelta(years=1)) if isinstance(appointment.appointment_date, str) else appointment.appointment_date + relativedelta(years=1),
                        pet_id=appointment.pet_id,
                        owner_id=appointment.owner_id,
                        dose_ml=treatment_rel.quantity,
                        previous_vaccination_date=get_previous_vaccination_date(appointment.pet, treatment.name, vaccine_type),
                        owner_name=appointment.pet.owner.name,
                        owner_address=appointment.pet.owner.address,
                        pet_species=appointment.pet.species,
                        pet_breed=appointment.pet.breed,
                        pet_card_number=appointment.pet.card_number,
                        pet_age=appointment.pet.pet_age()
                    )
                    db.session.add(vaccination)
            elif treatment.category == 'vaccines':
                # Если нет типов вакцин, создаем одну запись
                vaccination = Vaccination(
                    vaccine_name=treatment.name,
                    vaccination_type='Общая',
                    date_administered=datetime.strptime(appointment.appointment_date, '%Y-%m-%d').date() if isinstance(appointment.appointment_date, str) else appointment.appointment_date,
                    next_due_date=(datetime.strptime(appointment.appointment_date, '%Y-%m-%d').date() + relativedelta(years=1)) if isinstance(appointment.appointment_date, str) else appointment.appointment_date + relativedelta(years=1),
                    pet_id=appointment.pet_id,
                    owner_id=appointment.owner_id,
                    dose_ml=treatment_rel.quantity,
                    previous_vaccination_date=get_previous_vaccination_date(appointment.pet, treatment.name, 'Общая'),
                    owner_name=appointment.pet.owner.name,
                    owner_address=appointment.pet.owner.address,
                    pet_species=appointment.pet.species,
                    pet_breed=appointment.pet.breed,
                    pet_card_number=appointment.pet.card_number,
                    pet_age=appointment.pet.pet_age()
                )
                db.session.add(vaccination)
        
        # Не делаем commit здесь - пусть вызывающий код управляет транзакцией
    except Exception as e:
        db.session.rollback()
        raise e

@app.route('/treatment_search')
def treatment_search():
    term = request.args.get('term', '')
    treatments = Treatment.query.filter(
        Treatment.name.ilike('%{}%'.format(term))
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
        Pet.name.ilike('%{}%'.format(term)) | 
        Pet.card_number.ilike('%{}%'.format(term))
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
                        vaccine_name="{} ({})".format(treatment_obj.name, vaccine_type),
                        vaccination_type=vaccine_type,
                        date_administered=appointment.appointment_date,
                        next_due_date=appointment.appointment_date + relativedelta(years=1),
                        pet_id=pet.id,
                        owner_id=pet.owner_id,
                        dose_ml=at.quantity,
                        previous_vaccination_date=get_previous_vaccination_date(pet, treatment_obj.name, vaccine_type),
                        owner_name=pet.owner.name,
                        owner_address=pet.owner.address,
                        pet_species=pet.species,
                        pet_breed=pet.breed,
                        pet_card_number=pet.card_number,
                        pet_age=pet.pet_age()
                    )
                    db.session.add(vaccination)
            elif treatment_obj.category == 'vaccines':
                # Если нет типов вакцин, создаем одну запись
                vaccination = Vaccination(
                    vaccine_name=treatment_obj.name,
                    vaccination_type='Общая',
                    date_administered=appointment.appointment_date,
                    next_due_date=appointment.appointment_date + relativedelta(years=1),
                    pet_id=pet.id,
                    owner_id=pet.owner_id,
                    dose_ml=at.quantity,
                    previous_vaccination_date=get_previous_vaccination_date(pet, treatment_obj.name, 'Общая'),
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


def get_previous_vaccination_date(pet, vaccine_name, vaccine_type):
    last_vaccination = Vaccination.query.filter_by(
        pet_id=pet.id,
        vaccination_type=vaccine_type
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
            app.logger.info("Добавлено новое назначение: {} (ID: {})".format(treatment.name, treatment.id))
            return redirect(url_for('list_treatments'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'Ошибка при добавлении назначения: {}'.format(str(e))
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
                'dose': "{}".format(vacc.dose_ml or 1.0)
            })
        # Формируем HTML отчета с альбомной ориентацией
        report_html = render_template(
            'rabies_report.html',
            report_data=report_data,
            start_date=start_date.strftime('%d.%m.%Y'),
            end_date=end_date.strftime('%d.%m.%Y')
        )
        
        # Проверяем, доступна ли генерация PDF
        if config is None:
            flash('Генерация PDF недоступна. Установите wkhtmltopdf с https://wkhtmltopdf.org/downloads.html', 'error')
            return redirect(url_for('vaccinations'))
        
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
        response.headers['Content-Disposition'] = 'inline; filename=rabies_report_{}_{}.pdf'.format(start_date.date(), end_date.date())
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
            download_name='vaccination_phones_{}.zip'.format(target_date.strftime('%m_%Y'))
        )
    else:
        flash('Неизвестный тип отчета', 'error')
        return redirect(url_for('vaccinations'))

@app.route('/vaccinations')
def vaccinations():
    """Страница отчётов"""
    return render_template('vaccinations.html')

@app.route('/vaccinations/list')
def vaccinations_list():
    """Просмотр всех вакцинаций"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Vaccination.query
    
    if search:
        query = query.filter(
            Vaccination.vaccine_name.ilike('%{}%'.format(search)) |
            Vaccination.owner_name.ilike('%{}%'.format(search))
        )
    
    vaccinations = query.order_by(Vaccination.date_administered.desc()).paginate(page=page, per_page=20)
    
    return render_template('vaccinations_list.html', vaccinations=vaccinations)

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
            return redirect(url_for('owner_card', owner_id=vaccination.owner_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при добавлении вакцинации: {}'.format(str(e)), 'danger')
            return redirect(request.url)
    else:
        # Обрабатываем GET-параметры
        owner_id = request.args.get('owner_id')
        pet_id = request.args.get('pet_id')

        if not owner_id or not pet_id:
            flash('Не указаны ID владельца или животного', 'error')
        
        selected_owner = Owner.query.get(owner_id) if owner_id else None
        selected_pet = Pet.query.get(pet_id) if pet_id else None

        if not selected_owner or not selected_pet:
            flash('Владелец или животное не найдены', 'error')

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
            return redirect(url_for('owner_card', owner_id=vaccination.owner_id))
            
        except ValueError as e:
            db.session.rollback()
            flash('Ошибка формата даты или числа: {}'.format(str(e)), 'danger')
            return redirect(request.url)
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при обновлении вакцинации: {}'.format(str(e)), 'danger')
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
            'start': "{}T{}".format(a.appointment_date, a.time),
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
    start_datetime = datetime.strptime("{} {}".format(appointment_date, start_time), "%Y-%m-%d %H:%M")
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
        flash('Ошибка при удалении приёма: {}'.format(str(e)), 'danger')
    
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

@app.route('/statistics')
def statistics():
    """Страница статистики с графиками по вакцинациям, возрасту и виду животных"""
    from sqlalchemy import func, extract, case, and_, or_
    
    # Получаем параметры фильтрации
    period = request.args.get('period', 'year')  # year, 6months, 3months, month
    compare_with_previous = request.args.get('compare', 'false').lower() == 'true'
    
    # Определяем период анализа
    current_date = datetime.now().date()
    if period == 'year':
        start_date = current_date.replace(year=current_date.year - 1)
        period_name = "за последний год"
    elif period == '6months':
        start_date = current_date - timedelta(days=180)
        period_name = "за последние 6 месяцев"
    elif period == '3months':
        start_date = current_date - timedelta(days=90)
        period_name = "за последние 3 месяца"
    elif period == 'month':
        start_date = current_date - timedelta(days=30)
        period_name = "за последний месяц"
    else:
        start_date = current_date.replace(year=current_date.year - 1)
        period_name = "за последний год"
    
    # Для сравнения с предыдущим периодом
    if compare_with_previous:
        period_days = (current_date - start_date).days
        prev_start_date = start_date - timedelta(days=period_days)
        prev_end_date = start_date
    else:
        prev_start_date = None
        prev_end_date = None
    
    # === ОСНОВНАЯ СТАТИСТИКА ===
    
    # Статистика по вакцинациям по месяцам
    vaccination_stats = db.session.query(
        extract('month', Vaccination.date_administered).label('month'),
        extract('year', Vaccination.date_administered).label('year'),
        func.count(Vaccination.id).label('count')
    ).filter(
        Vaccination.date_administered >= start_date
    ).group_by(
        extract('month', Vaccination.date_administered),
        extract('year', Vaccination.date_administered)
    ).order_by(
        extract('year', Vaccination.date_administered),
        extract('month', Vaccination.date_administered)
    ).all()
    vaccination_stats = [
        {
            'month': int(row.month),
            'year': int(row.year),
            'count': int(row.count)
        } for row in vaccination_stats
    ]
    
    # Статистика по типам вакцинаций (за всё время)
    vaccination_types = db.session.query(
        Vaccination.vaccination_type,
        func.count(Vaccination.id).label('count')
    ).group_by(Vaccination.vaccination_type).all()
    vaccination_types = [
        {
            'vaccination_type': row.vaccination_type or 'Не указано',
            'count': int(row.count)
        } for row in vaccination_types
    ]
    
    # Статистика по типам вакцинаций по месяцам (за всё время)
    vaccination_types_monthly = db.session.query(
        extract('month', Vaccination.date_administered).label('month'),
        extract('year', Vaccination.date_administered).label('year'),
        Vaccination.vaccination_type,
        func.count(Vaccination.id).label('count')
    ).group_by(
        extract('month', Vaccination.date_administered),
        extract('year', Vaccination.date_administered),
        Vaccination.vaccination_type
    ).order_by(
        extract('year', Vaccination.date_administered),
        extract('month', Vaccination.date_administered),
        Vaccination.vaccination_type
    ).all()
    vaccination_types_monthly = [
        {
            'month': int(row.month),
            'year': int(row.year),
            'vaccination_type': row.vaccination_type or 'Не указано',
            'count': int(row.count)
        } for row in vaccination_types_monthly
    ]
    
    # Статистика по видам животных
    species_stats = db.session.query(
        Pet.species,
        func.count(Pet.id).label('count')
    ).group_by(Pet.species).all()
    species_stats = [
        {
            'species': row.species or 'Не указано',
            'count': int(row.count)
        } for row in species_stats
    ]
    
    
    # Статистика по возрасту животных
    age_stats = db.session.query(
        case(
            (
                Pet.birth_date >= current_date.replace(year=current_date.year - 1),
                'до 1 года'
            ),
            (
                Pet.birth_date >= current_date.replace(year=current_date.year - 3),
                '1-3 года'
            ),
            (
                Pet.birth_date >= current_date.replace(year=current_date.year - 7),
                '3-7 лет'
            ),
            (
                Pet.birth_date >= current_date.replace(year=current_date.year - 12),
                '7-12 лет'
            ),
            else_='старше 12 лет'
        ).label('age_group'),
        func.count(Pet.id).label('count')
    ).group_by('age_group').all()
    age_stats = [
        {
            'age_group': row.age_group,
            'count': int(row.count)
        } for row in age_stats
    ]
    
    
    # === СТАТИСТИКА ПО ПРИЁМАМ ===
    
    # Статистика по приёмам по месяцам
    appointment_stats = db.session.query(
        extract('month', Appointment.appointment_date).label('month'),
        extract('year', Appointment.appointment_date).label('year'),
        func.count(Appointment.id).label('count')
    ).filter(
        Appointment.appointment_date >= start_date.strftime('%Y-%m-%d')
    ).group_by(
        extract('month', Appointment.appointment_date),
        extract('year', Appointment.appointment_date)
    ).order_by(
        extract('year', Appointment.appointment_date),
        extract('month', Appointment.appointment_date)
    ).all()
    appointment_stats = [
        {
            'month': int(row.month),
            'year': int(row.year),
            'count': int(row.count)
        } for row in appointment_stats
    ]
    
    # Статистика по стоимости приёмов
    appointment_costs = db.session.query(
        extract('month', Appointment.appointment_date).label('month'),
        extract('year', Appointment.appointment_date).label('year'),
        func.sum(AppointmentTreatment.total_price).label('total_cost')
    ).join(AppointmentTreatment).filter(
        Appointment.appointment_date >= start_date.strftime('%Y-%m-%d')
    ).group_by(
        extract('month', Appointment.appointment_date),
        extract('year', Appointment.appointment_date)
    ).order_by(
        extract('year', Appointment.appointment_date),
        extract('month', Appointment.appointment_date)
    ).all()
    appointment_costs = [
        {
            'month': int(row.month),
            'year': int(row.year),
            'total_cost': float(row.total_cost or 0)
        } for row in appointment_costs
    ]
    
    
    # Статистика по популярным услугам/назначениям
    popular_treatments = db.session.query(
        Treatment.name,
        Treatment.category,
        func.count(AppointmentTreatment.id).label('count'),
        func.sum(AppointmentTreatment.total_price).label('total_revenue')
    ).join(AppointmentTreatment).join(Appointment).filter(
        Appointment.appointment_date >= start_date.strftime('%Y-%m-%d')
    ).group_by(Treatment.id, Treatment.name, Treatment.category).order_by(
        func.count(AppointmentTreatment.id).desc()
    ).limit(15).all()
    popular_treatments = [
        {
            'name': row.name,
            'category': row.category,
            'count': int(row.count),
            'total_revenue': float(row.total_revenue or 0)
        } for row in popular_treatments
    ]
    
    # Статистика по категориям услуг
    treatment_categories = db.session.query(
        Treatment.category,
        func.count(AppointmentTreatment.id).label('count'),
        func.sum(AppointmentTreatment.total_price).label('total_revenue')
    ).join(AppointmentTreatment).join(Appointment).filter(
        Appointment.appointment_date >= start_date.strftime('%Y-%m-%d')
    ).group_by(Treatment.category).all()
    
    # Функция для перевода категорий на русский
    def translate_category(category):
        translations = {
            'general_services': 'Общие услуги',
            'lab_tests': 'Лабораторные анализы',
            'vaccines': 'Вакцинации',
            'surgery': 'Хирургия',
            'dental': 'Стоматология',
            'emergency': 'Экстренная помощь',
            'consultation': 'Консультации',
            'diagnostics': 'Диагностика',
            'treatment': 'Лечение',
            'prevention': 'Профилактика',
            'grooming': 'Груминг',
            'boarding': 'Передержка',
            'pharmacy': 'Аптека',
            'other': 'Прочее'
        }
        return translations.get(category, category)
    
    treatment_categories = [
        {
            'category': translate_category(row.category),
            'count': int(row.count),
            'total_revenue': float(row.total_revenue or 0)
        } for row in treatment_categories
    ]
    
    # === СРАВНЕНИЕ С ПРЕДЫДУЩИМ ПЕРИОДОМ ===
    prev_vaccination_stats = []
    prev_appointment_stats = []
    prev_appointment_costs = []
    
    if compare_with_previous and prev_start_date and prev_end_date:
        # Предыдущий период - вакцинации
        prev_vaccination_stats = db.session.query(
            extract('month', Vaccination.date_administered).label('month'),
            extract('year', Vaccination.date_administered).label('year'),
            func.count(Vaccination.id).label('count')
        ).filter(
            Vaccination.date_administered >= prev_start_date,
            Vaccination.date_administered < prev_end_date
        ).group_by(
            extract('month', Vaccination.date_administered),
            extract('year', Vaccination.date_administered)
        ).order_by(
            extract('year', Vaccination.date_administered),
            extract('month', Vaccination.date_administered)
        ).all()
        prev_vaccination_stats = [
            {
                'month': int(row.month),
                'year': int(row.year),
                'count': int(row.count)
            } for row in prev_vaccination_stats
        ]
        
        # Предыдущий период - приёмы
        prev_appointment_stats = db.session.query(
            extract('month', Appointment.appointment_date).label('month'),
            extract('year', Appointment.appointment_date).label('year'),
            func.count(Appointment.id).label('count')
        ).filter(
            Appointment.appointment_date >= prev_start_date.strftime('%Y-%m-%d'),
            Appointment.appointment_date < prev_end_date.strftime('%Y-%m-%d')
        ).group_by(
            extract('month', Appointment.appointment_date),
            extract('year', Appointment.appointment_date)
        ).order_by(
            extract('year', Appointment.appointment_date),
            extract('month', Appointment.appointment_date)
        ).all()
        prev_appointment_stats = [
            {
                'month': int(row.month),
                'year': int(row.year),
                'count': int(row.count)
            } for row in prev_appointment_stats
        ]
        
        # Предыдущий период - доходы
        prev_appointment_costs = db.session.query(
            extract('month', Appointment.appointment_date).label('month'),
            extract('year', Appointment.appointment_date).label('year'),
            func.sum(AppointmentTreatment.total_price).label('total_cost')
        ).join(AppointmentTreatment).filter(
            Appointment.appointment_date >= prev_start_date.strftime('%Y-%m-%d'),
            Appointment.appointment_date < prev_end_date.strftime('%Y-%m-%d')
        ).group_by(
            extract('month', Appointment.appointment_date),
            extract('year', Appointment.appointment_date)
        ).order_by(
            extract('year', Appointment.appointment_date),
            extract('month', Appointment.appointment_date)
        ).all()
        prev_appointment_costs = [
            {
                'month': int(row.month),
                'year': int(row.year),
                'total_cost': float(row.total_cost or 0)
            } for row in prev_appointment_costs
        ]
    
    # === ОБЩАЯ СТАТИСТИКА ===
    total_pets = Pet.query.count()
    total_owners = Owner.query.count()
    total_vaccinations = Vaccination.query.count()
    total_appointments = Appointment.query.count()
    
    # Статистика за период
    period_vaccinations = Vaccination.query.filter(Vaccination.date_administered >= start_date).count()
    period_appointments = Appointment.query.filter(Appointment.appointment_date >= start_date.strftime('%Y-%m-%d')).count()
    
    # Средний чек
    avg_check = db.session.query(func.avg(AppointmentTreatment.total_price)).join(Appointment).filter(
        Appointment.appointment_date >= start_date.strftime('%Y-%m-%d')
    ).scalar() or 0
    
    # Общий доход за период
    total_revenue = db.session.query(func.sum(AppointmentTreatment.total_price)).join(Appointment).filter(
        Appointment.appointment_date >= start_date.strftime('%Y-%m-%d')
    ).scalar() or 0
    
    # === СТАТИСТИКА ПО ВАКЦИНАМ ЗА ВЫБРАННЫЙ МЕСЯЦ ===
    
    # Получаем параметры выбора месяца/года или используем текущий месяц
    selected_vaccine_month = request.args.get('vaccine_month', type=int, default=current_date.month)
    selected_vaccine_year = request.args.get('vaccine_year', type=int, default=current_date.year)
    
    # Форматируем название месяца на русском
    month_names_ru = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    last_month_name = "{} {}".format(month_names_ru[selected_vaccine_month], selected_vaccine_year)
    
    # Получаем список доступных годов из базы данных
    vaccine_years_query = db.session.query(
        func.distinct(extract('year', Vaccination.date_administered)).label('year')
    ).order_by(extract('year', Vaccination.date_administered).desc()).all()
    vaccine_years = [int(row.year) for row in vaccine_years_query if row.year]
    
    # Если нет данных, добавляем текущий год
    if not vaccine_years:
        vaccine_years = [current_date.year]
    
    # Определяем границы выбранного месяца
    from calendar import monthrange
    _, last_day = monthrange(selected_vaccine_year, selected_vaccine_month)
    month_start = date(selected_vaccine_year, selected_vaccine_month, 1)
    month_end = date(selected_vaccine_year, selected_vaccine_month, last_day)
    
    # Подсчёт вакцинаций по типам за выбранный месяц
    last_month_vaccinations = db.session.query(
        Vaccination.vaccination_type,
        func.count(Vaccination.id).label('count')
    ).filter(
        Vaccination.date_administered >= month_start,
        Vaccination.date_administered <= month_end
    ).group_by(Vaccination.vaccination_type).all()
    
    last_month_vaccinations = [
        {
            'vaccination_type': row.vaccination_type or 'Не указано',
            'count': int(row.count)
        } for row in last_month_vaccinations
    ]
    
    # Подсчёт по названиям вакцин за выбранный месяц
    last_month_vaccines_detail = db.session.query(
        Vaccination.vaccine_name,
        Vaccination.vaccination_type,
        func.count(Vaccination.id).label('count')
    ).filter(
        Vaccination.date_administered >= month_start,
        Vaccination.date_administered <= month_end
    ).group_by(Vaccination.vaccine_name, Vaccination.vaccination_type).order_by(
        func.count(Vaccination.id).desc()
    ).all()
    
    last_month_vaccines_detail = [
        {
            'vaccine_name': row.vaccine_name or 'Не указано',
            'vaccination_type': row.vaccination_type or 'Не указано',
            'count': int(row.count)
        } for row in last_month_vaccines_detail
    ]
    
    last_month_date = month_start
    
    # === СТАТИСТИКА ПО ГОДАМ ЗА ПОСЛЕДНИЕ 5 ЛЕТ ===
    current_year = current_date.year
    years_list = list(range(current_year - 4, current_year + 1))  # Последние 5 лет
    
    # Статистика по животным по годам (по дате первого приёма или первой вакцинации)
    # Для каждого животного находим минимальную дату приёма
    first_appointment_dates = db.session.query(
        Appointment.pet_id,
        func.min(Appointment.appointment_date).label('first_date')
    ).group_by(Appointment.pet_id).subquery()
    
    yearly_pets = db.session.query(
        extract('year', first_appointment_dates.c.first_date).label('year'),
        func.count(first_appointment_dates.c.pet_id).label('count')
    ).filter(
        extract('year', first_appointment_dates.c.first_date).in_(years_list)
    ).group_by(extract('year', first_appointment_dates.c.first_date)).all()
    
    yearly_pets_dict = {int(row.year): int(row.count) for row in yearly_pets}
    
    # Добавляем животных, у которых есть только вакцинации (без приёмов)
    pets_with_appointments = db.session.query(Appointment.pet_id).distinct()
    
    first_vacc_dates = db.session.query(
        Vaccination.pet_id,
        func.min(Vaccination.date_administered).label('first_date')
    ).filter(
        ~Vaccination.pet_id.in_(pets_with_appointments)
    ).group_by(Vaccination.pet_id).subquery()
    
    pets_with_only_vacc = db.session.query(
        extract('year', first_vacc_dates.c.first_date).label('year'),
        func.count(first_vacc_dates.c.pet_id).label('count')
    ).filter(
        extract('year', first_vacc_dates.c.first_date).in_(years_list)
    ).group_by(extract('year', first_vacc_dates.c.first_date)).all()
    
    for row in pets_with_only_vacc:
        year = int(row.year)
        yearly_pets_dict[year] = yearly_pets_dict.get(year, 0) + int(row.count)
    
    yearly_pets_stats = [
        {'year': year, 'count': yearly_pets_dict.get(year, 0)} 
        for year in years_list
    ]
    
    # Статистика по приёмам по годам
    yearly_appointments = db.session.query(
        extract('year', Appointment.appointment_date).label('year'),
        func.count(Appointment.id).label('count')
    ).filter(
        extract('year', Appointment.appointment_date).in_(years_list)
    ).group_by(extract('year', Appointment.appointment_date)).all()
    
    yearly_appointments_dict = {int(row.year): int(row.count) for row in yearly_appointments}
    yearly_appointments_stats = [
        {'year': year, 'count': yearly_appointments_dict.get(year, 0)} 
        for year in years_list
    ]
    
    # Статистика по вакцинациям по годам
    yearly_vaccinations = db.session.query(
        extract('year', Vaccination.date_administered).label('year'),
        func.count(Vaccination.id).label('count')
    ).filter(
        extract('year', Vaccination.date_administered).in_(years_list)
    ).group_by(extract('year', Vaccination.date_administered)).all()
    
    yearly_vaccinations_dict = {int(row.year): int(row.count) for row in yearly_vaccinations}
    yearly_vaccinations_stats = [
        {'year': year, 'count': yearly_vaccinations_dict.get(year, 0)} 
        for year in years_list
    ]
    
    # Статистика по вакцинациям по месяцам за последние 5 лет
    five_years_ago = date(current_year - 4, 1, 1)
    monthly_vaccinations = db.session.query(
        extract('year', Vaccination.date_administered).label('year'),
        extract('month', Vaccination.date_administered).label('month'),
        func.count(Vaccination.id).label('count')
    ).filter(
        Vaccination.date_administered >= five_years_ago
    ).group_by(
        extract('year', Vaccination.date_administered),
        extract('month', Vaccination.date_administered)
    ).order_by(
        extract('year', Vaccination.date_administered),
        extract('month', Vaccination.date_administered)
    ).all()
    
    # Создаем словарь для быстрого доступа
    monthly_vaccinations_dict = {}
    for row in monthly_vaccinations:
        key = "{}-{:02d}".format(int(row.year), int(row.month))
        monthly_vaccinations_dict[key] = int(row.count)
    
    # Создаем полный список всех месяцев за последние 5 лет
    monthly_vaccinations_full = []
    for year in years_list:
        for month in range(1, 13):
            key = "{}-{:02d}".format(year, month)
            month_date = date(year, month, 1)
            if month_date <= current_date:
                monthly_vaccinations_full.append({
                    'year': year,
                    'month': month,
                    'count': monthly_vaccinations_dict.get(key, 0),
                    'label': "{:02d}.{}".format(month, year)
                })
    
    # Статистика по доходам по годам
    yearly_revenue = db.session.query(
        extract('year', Appointment.appointment_date).label('year'),
        func.sum(AppointmentTreatment.total_price).label('total_revenue')
    ).join(AppointmentTreatment).filter(
        extract('year', Appointment.appointment_date).in_(years_list)
    ).group_by(extract('year', Appointment.appointment_date)).all()
    
    yearly_revenue_dict = {int(row.year): float(row.total_revenue or 0) for row in yearly_revenue}
    yearly_revenue_stats = [
        {'year': year, 'total_revenue': yearly_revenue_dict.get(year, 0)} 
        for year in years_list
    ]
    
    # Средний чек по годам
    yearly_avg_check = []
    for year in years_list:
        year_avg = db.session.query(
            func.avg(AppointmentTreatment.total_price)
        ).join(Appointment).filter(
            extract('year', Appointment.appointment_date) == year
        ).scalar() or 0
        yearly_avg_check.append({
            'year': year,
            'avg_check': float(year_avg)
        })
    
    # Общее количество животных на конец каждого года (накопленное)
    # Используем дату первого приёма или первой вакцинации как дату регистрации
    yearly_total_pets = []
    for year in years_list:
        year_end = date(year, 12, 31)
        year_end_str = year_end.strftime('%Y-%m-%d')
        
        # Находим уникальных животных, у которых был хотя бы один приём до конца года
        pets_with_appts = db.session.query(Appointment.pet_id).distinct().filter(
            Appointment.appointment_date <= year_end_str
        ).subquery()
        
        # Находим животных без приёмов, у которых была хотя бы одна вакцинация до конца года
        pets_with_vacc_only = db.session.query(Vaccination.pet_id).distinct().filter(
            Vaccination.date_administered <= year_end_str,
            ~Vaccination.pet_id.in_(db.session.query(pets_with_appts.c.pet_id))
        ).subquery()
        
        # Считаем общее количество уникальных животных
        total_appts = db.session.query(func.count(func.distinct(pets_with_appts.c.pet_id))).scalar() or 0
        total_vacc_only = db.session.query(func.count(func.distinct(pets_with_vacc_only.c.pet_id))).scalar() or 0
        total = total_appts + total_vacc_only
        
        yearly_total_pets.append({
            'year': year,
            'total': int(total)
        })
    
    return render_template('statistics.html',
                         # Основные данные
                         vaccination_stats=vaccination_stats,
                         vaccination_types=vaccination_types,
                         vaccination_types_monthly=vaccination_types_monthly,
                         species_stats=species_stats,
                         age_stats=age_stats,
                         appointment_stats=appointment_stats,
                         appointment_costs=appointment_costs,
                         popular_treatments=popular_treatments,
                         treatment_categories=treatment_categories,
                         
                         # Сравнение с предыдущим периодом
                         prev_vaccination_stats=prev_vaccination_stats,
                         prev_appointment_stats=prev_appointment_stats,
                         prev_appointment_costs=prev_appointment_costs,
                         
                         # Общая статистика
                         total_pets=total_pets,
                         total_owners=total_owners,
                         total_vaccinations=total_vaccinations,
                         total_appointments=total_appointments,
                         period_vaccinations=period_vaccinations,
                         period_appointments=period_appointments,
                         avg_check=float(avg_check),
                         total_revenue=float(total_revenue),
                         
                         # Статистика по вакцинам за последний месяц
                         last_month_vaccinations=last_month_vaccinations,
                         last_month_vaccines_detail=last_month_vaccines_detail,
                         last_month_date=last_month_date,
                         last_month_name=last_month_name,
                         vaccine_years=vaccine_years,
                         selected_vaccine_month=selected_vaccine_month,
                         selected_vaccine_year=selected_vaccine_year,
                         
                         # Параметры фильтрации
                         period=period,
                         period_name=period_name,
                         compare_with_previous=compare_with_previous,
                         
                         # Статистика по годам
                         yearly_pets_stats=yearly_pets_stats,
                         yearly_appointments_stats=yearly_appointments_stats,
                         yearly_vaccinations_stats=yearly_vaccinations_stats,
                         monthly_vaccinations_full=monthly_vaccinations_full,
                         yearly_revenue_stats=yearly_revenue_stats,
                         yearly_avg_check=yearly_avg_check,
                         yearly_total_pets=yearly_total_pets,
                         years_list=years_list)

@app.route('/settings')
def settings():
    """Страница настроек приложения"""
    return render_template('settings.html')

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
    
    return jsonify([{'id': p.id, 'text': "{} ({})".format(p.name, p.card_number)} for p in pets])

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
    
    # Преобразуем поисковый запрос к верхнему регистру для сравнения, так как в БД имена хранятся в верхнем регистре
    # Используем func.upper() для надежного регистронезависимого поиска
    owners = Owner.query.filter(
        db.func.upper(Owner.name).like('%{}%'.format(search_term.upper()))
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
    card_number = request.args.get('card_number', '').strip()
    highlight_pet = request.args.get('highlight', type=int)
    
    owner = Owner.query.get_or_404(owner_id)
    
    # Базовый запрос для животных владельца
    pets_query = Pet.query.filter_by(owner_id=owner_id).order_by(Pet.name)
    
    # Если указан номер карточки для поиска
    if card_number:
        pet = pets_query.filter_by(card_number=card_number).first()
        if pet:
            # Вычисляем на какой странице находится это животное
            all_pets = pets_query.all()
            try:
                index = all_pets.index(pet)
                page = (index // 10) + 1  # 10 - количество элементов на странице
                return redirect(url_for('owner_card', owner_id=owner_id, page=page, highlight=pet.id))
            except ValueError:
                pass
    
    # Пагинация с учетом возможного фильтра
    pagination = pets_query.paginate(page=page, per_page=10, error_out=False)
    
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
            flash('Ошибка при обновлении: {}'.format(str(e)), 'danger')
    
    return render_template(
        'owner_card.html', 
        owner=owner, 
        pagination=pagination,
        highlight_pet=highlight_pet,
        search_card_number=card_number if card_number else None
    )

@app.route('/api/search_owners_for_transfer')
def search_owners_for_transfer():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    # Ищем по имени, телефону или адресу с более подробной информацией
    # Для имени используем func.upper() так как в БД имена хранятся в верхнем регистре
    query_upper = query.upper()
    owners = Owner.query.filter(
        db.or_(
            db.func.upper(Owner.name).like('%{}%'.format(query_upper)),
            Owner.phone.ilike('%{}%'.format(query)),
            Owner.address.ilike('%{}%'.format(query))
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
    
    flash('Животное успешно переведено на владельца: {}'.format(new_owner.name), 'success')
    return redirect(url_for('owner_card', owner_id=new_owner.id))

@app.route('/problematic_owners')
def problematic_owners():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Основной запрос
    query = db.session.query(Owner).options(selectinload(Owner.pets))

    # 1. Ищем дубли по имени владельца
    duplicate_names = db.session.query(Owner.name)\
        .group_by(Owner.name)\
        .having(db.func.count(Owner.id) > 1)\
        .all()
    duplicate_names = {name for (name,) in duplicate_names}

    # 2. Ищем владельцев с очень старыми животными (старше 20 лет)
    today = datetime.today().date()
    twenty_years_ago = today.replace(year=today.year - 20)

    old_pet_owner_ids = db.session.query(Pet.owner_id)\
        .filter(Pet.birth_date <= twenty_years_ago)\
        .distinct()\
        .all()
    old_pet_owner_ids = {owner_id for (owner_id,) in old_pet_owner_ids}

    # 3. Фильтруем владельцев
    query = query.filter(
        db.or_(
            Owner.name.in_(duplicate_names),
            Owner.id.in_(old_pet_owner_ids)
        )
    )

    owners_pagination = query.order_by(Owner.name)\
                           .paginate(page=page, per_page=per_page, error_out=False)

    # Передадим в шаблон информацию о дублях и старых животных
    problematic_owner_ids = {
        'duplicate_names': duplicate_names,
        'old_pet_owner_ids': old_pet_owner_ids
    }

    return render_template(
        'owners.html',
        owners=owners_pagination.items,
        pagination=owners_pagination,
        search_name='',
        search_pet='',
        search_card='',
        search_phone='',
        problematic_owner_ids=problematic_owner_ids
    )

@app.route('/owners')
def owners_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    search_name = request.args.get('search_name', '').strip().upper()
    search_pet = request.args.get('search_pet', '').strip()
    search_card = request.args.get('search_card', '').strip()
    search_phone = request.args.get('search_phone', '').strip()
    search_address = request.args.get('search_address', '').strip().upper()

    query = db.session.query(Owner).outerjoin(Pet).distinct()
    #query = db.session.query(Owner).options(selectinload(Owner.pets))


    if search_name:
        # Разбиваем поисковый запрос на части (фамилия, имя)
        search_parts = search_name.split()[:2]  # Берем только первые два слова
        
        # Создаем условия для поиска по фамилии и имени (без отчества)
        conditions = []
        for part in search_parts:
            # Ищем в начале строки (фамилия) или после пробела (имя)
            conditions.append(db.or_(
                Owner.name.ilike('{} %'.format(part)),  # Фамилия в начале
                Owner.name.ilike('% {} %'.format(part)), # Имя в середине
                Owner.name.ilike('% {}'.format(part))    # Имя в конце (если нет отчества)
            ))
        
        # Объединяем условия через AND (и фамилия, и имя должны совпадать)
        query = query.filter(db.and_(*conditions))
    
    if search_pet:
        query = query.filter(Pet.name.ilike('%{}%'.format(search_pet)))
    if search_card:
        query = query.filter(Pet.card_number == search_card)
    if search_phone:
        phone_digits = ''.join(filter(str.isdigit, search_phone))
        query = query.filter(Owner.phone.ilike('%{}%'.format(phone_digits)))
    if search_address:
        query = query.filter(Owner.address.ilike('%{}%'.format(search_address)))

    owners_pagination = query.order_by(Owner.name)\
                           .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'owners.html',
        owners=owners_pagination.items,
        pagination=owners_pagination,
        search_name=search_name,
        search_pet=search_pet,
        search_card=search_card,
        search_phone=search_phone,
        search_address=search_address,
        problematic_owner_ids=None
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
        flash('Ошибка при удалении: {}'.format(str(e)), 'danger')
    
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
            flash('Ошибка: Животное с номером карточки {} уже существует!'.format(card_number), 'danger')
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
            flash('Ошибка: Животное с номером карточки {} уже существует!'.format(card_number), 'danger')
        else:
            flash('Произошла ошибка при сохранении данных', 'danger')

    except Exception as e:
        db.session.rollback()
        flash('Ошибка при добавлении животного: {}'.format(str(e)), 'danger')

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
            flash("Ошибка: {}".format(str(e)), 'error')
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
    response.headers['Content-Disposition'] = 'attachment; filename=pet_card_{}.docx'.format(pet.id)
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
        print("Успешно обновлено {} записей.".format(len(owners)))

    except Exception as e:
        db.session.rollback()
        print("Ошибка: {}".format(e))

@app.cli.command("import-csv")
def import_csv_command():
    """Импорт данных из CSV файла"""
    try:
        from csv_importer import import_csv  # Вынесем импортер в отдельный файл
        import_csv('data/test_.csv')
        print("Импорт успешно завершен!")
    except Exception as e:
        print("Ошибка импорта: {}".format(str(e)))
        import traceback
        traceback.print_exc()

@app.cli.command("import-new-csv")
def import_new_csv_command():
    """Импорт данных из CSV файла"""
    try:
        from csv_importer import import_only_new_pets  # Вынесем импортер в отдельный файл
        import_only_new_pets('data/animals_temp.csv')
        print("Импорт успешно завершен!")
    except Exception as e:
        print("Ошибка импорта: {}".format(str(e)))
        import traceback
        traceback.print_exc()

@app.cli.command("import-owner-csv")
def import_owner_csv_command():
    """Импорт данных из CSV файла"""
    try:
        from csv_importer import import_owners_from_csv  # Вынесем импортер в отдельный файл
        import_owners_from_csv('data/owners_test.csv')
        print("Импорт успешно завершен!")
    except Exception as e:
        print("Ошибка импорта: {}".format(str(e)))
        import traceback
        traceback.print_exc()

@app.cli.command("import-vac-csv")
def import_vac_csv_command():
    """Импорт данных о вакцинах из CSV файла"""
    try:
        from csv_importer import import_vaccinations  # Вынесем импортер в отдельный файл
        import_vaccinations('data/vac_for_test2.csv')
        print("Импорт успешно завершен!")
    except Exception as e:
        print("Ошибка импорта: {}".format(str(e)))
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
        print("Ошибка: {}".format(str(e)))
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
            print("\nOwner ID: {}".format(owner.id))
            print("Original: {}".format(original))
            print("Normalized: {}".format(new_phone))
            print("Invalid: {}".format(', '.join(result['invalid'])))
            
            if not dry_run:
                owner.phone = new_phone
    
    if not dry_run:
        try:
            db.session.commit()
            print("\nChanges committed to database!")
        except Exception as e:
            db.session.rollback()
            print("\nError committing changes: {}".format(str(e)))
    else:
        print("\nDry run complete. No changes saved.")

# ================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ================================

# ================================
# МАРШРУТЫ ДЛЯ ML ДИАГНОСТИКИ
# ================================

@app.route('/diagnosis')
def diagnosis_page():
    """Страница диагностики заболеваний"""
    return render_template('diagnosis_extended.html')

@app.route('/diagnose', methods=['POST'])
@csrf.exempt
def diagnose():
    """API для диагностики заболеваний"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Пустые данные'}), 400
        
        animal_type = data.get('animal_type')
        symptoms = data.get('symptoms', [])
        lab_analyses = data.get('lab_analyses', {})
        
        if not animal_type:
            return jsonify({'success': False, 'error': 'Не указан вид животного'}), 400
        
        if not symptoms:
            return jsonify({'success': False, 'error': 'Не указаны симптомы'}), 400
        
        # Проверяем, включена ли ML диагностика
        if not ml_enabled:
            return jsonify({'success': False, 'error': 'ML диагностика выключена. Включите её в настройках.'}), 403
        
        # Проверяем, загружена ли модель
        if ml_model is None:
            # Пытаемся загрузить модель, если она не загружена
            if not load_ml_model():
                return jsonify({'success': False, 'error': 'ML модель не найдена или не может быть загружена'}), 500
        
        # Получаем предсказания
        if isinstance(ml_model, dict):
            # Проверяем, это взвешенная модель или другая
            if 'animal_type_encoder' in ml_model:
                # Взвешенная модель
                model = ml_model['model']
                scaler = ml_model['scaler']
                feature_selector = ml_model['feature_selector']
                label_encoder = ml_model['label_encoder']
                animal_type_encoder = ml_model['animal_type_encoder']
                feature_names = ml_model['feature_names']
                
                # Создаем вектор признаков на основе feature_names
                features = np.zeros(len(feature_names))
                
                # Устанавливаем симптомы
                for symptom in symptoms:
                    if symptom in feature_names:
                        idx = feature_names.index(symptom)
                        features[idx] = 1
                
                # Устанавливаем лабораторные анализы
                for lab_name, lab_value in lab_analyses.items():
                    lab_feature = "lab_{}_{}".format(lab_name, lab_value)
                    if lab_feature in feature_names:
                        idx = feature_names.index(lab_feature)
                        features[idx] = 1
                
                # Устанавливаем тип животного
                if 'animal_type_encoded' in feature_names:
                    try:
                        animal_type_encoded = animal_type_encoder.transform([animal_type])[0]
                        idx = feature_names.index('animal_type_encoded')
                        features[idx] = animal_type_encoded
                    except:
                        pass  # Если тип животного не найден, пропускаем
                
                # Масштабирование признаков
                features_scaled = scaler.transform([features])
                
                # Выбор признаков
                features_selected = feature_selector.transform(features_scaled)
                
                # Предсказание
                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(features_selected)[0]
                    classes = model.classes_
                else:
                    # Fallback
                    prediction = model.predict(features_selected)[0]
                    probabilities = np.zeros(len(classes))
                    if prediction in classes:
                        idx = list(classes).index(prediction)
                        probabilities[idx] = 1.0
                
                # Получение топ-5 предсказаний
                top_indices = np.argsort(probabilities)[::-1][:5]
                predictions = []
                for idx in top_indices:
                    disease = label_encoder.inverse_transform([classes[idx]])[0]
                    probability = probabilities[idx]
                    predictions.append([disease, probability])
                    
            elif 'feature_selector' in ml_model:
                # Улучшенная модель
                model = ml_model['model']
                scaler = ml_model['scaler']
                feature_selector = ml_model['feature_selector']
                label_encoder = ml_model['label_encoder']
                feature_names = ml_model['feature_names']
                
                # Создаем вектор признаков на основе feature_names
                features = np.zeros(len(feature_names))
                
                # Устанавливаем симптомы
                for symptom in symptoms:
                    if symptom in feature_names:
                        idx = feature_names.index(symptom)
                        features[idx] = 1
                
                # Устанавливаем лабораторные анализы
                for lab_name, lab_value in lab_analyses.items():
                    lab_feature = "lab_{}_{}".format(lab_name, lab_value)
                    if lab_feature in feature_names:
                        idx = feature_names.index(lab_feature)
                        features[idx] = 1
                
                # Масштабирование признаков
                features_scaled = scaler.transform([features])
                
                # Выбор признаков
                features_selected = feature_selector.transform(features_scaled)
                
                # Предсказание
                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(features_selected)[0]
                    classes = model.classes_
                else:
                    # Fallback
                    prediction = model.predict(features_selected)[0]
                    probabilities = np.zeros(len(classes))
                    if prediction in classes:
                        idx = list(classes).index(prediction)
                        probabilities[idx] = 1.0
                
                # Получение топ-5 предсказаний
                top_indices = np.argsort(probabilities)[::-1][:5]
                predictions = []
                for idx in top_indices:
                    disease = classes[idx]
                    probability = probabilities[idx]
                    predictions.append([disease, probability])
                    
            else:
                # Стандартная модель
                model = ml_model['model']
                scaler = ml_model['scaler']
                symptoms_list = ml_model['symptoms']
                diseases_list = ml_model['diseases']
                feature_names = ml_model['feature_names']
                
                # Создаем вектор признаков на основе feature_names
                features = np.zeros(len(feature_names))
                
                # Устанавливаем симптомы
                for symptom in symptoms:
                    if symptom in feature_names:
                        idx = feature_names.index(symptom)
                        features[idx] = 1
                
                # Устанавливаем лабораторные анализы
                for lab_name, lab_value in lab_analyses.items():
                    if lab_name in feature_names:
                        idx = feature_names.index(lab_name)
                        features[idx] = 1
                
                # Масштабирование признаков
                features_scaled = scaler.transform([features])
                
                # Предсказание
                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(features_scaled)[0]
                    classes = model.classes_
                else:
                    # Для моделей без predict_proba
                    if hasattr(model, 'decision_function'):
                        scores = model.decision_function(features_scaled)[0]
                        probabilities = np.exp(scores) / np.sum(np.exp(scores))
                        classes = model.classes_
                    else:
                        # Fallback
                        probabilities = np.ones(len(diseases_list)) / len(diseases_list)
                        classes = diseases_list
                
                # Сортируем по вероятности
                disease_probs = list(zip(classes, probabilities))
                disease_probs.sort(key=lambda x: x[1], reverse=True)
                predictions = disease_probs[:5]
        else:
            # Если модель - объект класса
            predictions = ml_model.predict_diseases(animal_type, symptoms)
        
        return jsonify({
            'success': True,
            'predictions': predictions
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

scheduler = init_scheduler()
# ML модель НЕ загружается по умолчанию - только при включении в настройках
# load_ml_model()  # Загружаем ML модель при запуске - ОТКЛЮЧЕНО

@app.route('/api/enable_ml', methods=['POST'])
@csrf.exempt
def enable_ml():
    """API для включения/выключения ML модели"""
    global ml_model, ml_enabled
    try:
        data = request.json
        enabled = data.get('enabled', False)
        
        if enabled:
            # Включаем ML - загружаем модель
            if ml_model is None:
                success = load_ml_model()
                if success:
                    ml_enabled = True
                    return jsonify({'success': True, 'message': 'ML модель загружена'})
                else:
                    return jsonify({'success': False, 'error': 'Не удалось загрузить ML модель'}), 500
            else:
                ml_enabled = True
                return jsonify({'success': True, 'message': 'ML модель уже загружена'})
        else:
            # Выключаем ML - освобождаем память
            ml_model = None
            ml_enabled = False
            return jsonify({'success': True, 'message': 'ML модель выгружена'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ml_status', methods=['GET'])
def ml_status():
    """API для проверки статуса ML модели"""
    global ml_model, ml_enabled
    return jsonify({
        'enabled': ml_enabled,
        'loaded': ml_model is not None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
