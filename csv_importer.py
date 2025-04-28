from datetime import datetime
from collections import defaultdict
import csv
from sqlalchemy.exc import IntegrityError
from models import db, Owner, Pet , Vaccination

def import_csv(filename):
    owners_data = defaultdict(lambda: {'phones': [], 'addresses': []})
    pets_temp_data = []
    
    species_mapping = {'1': 'Собака', '2': 'Кот', '3': 'Птица', '4': 'Грызун', '5': 'Лиса'}
    sex_mapping = {'1': 'М', '2': 'Ж', '3': 'КМ', '4': 'КЖ'}

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',')
        
        for row in reader:
            owner_id = row['id']
            owner_name = ' '.join(word.capitalize() for word in row['owner_name'].lower().split())
            
            # Собираем данные владельца
            if row['type'] == '9981':
                owners_data[owner_id]['phones'].append(row['value'].strip())
            elif row['type'] == '9975':
                owners_data[owner_id]['addresses'].append(row['value'].strip())
            owners_data[owner_id]['name'] = owner_name
            
            # Обработка животного с проверкой даты
            card_num = row['actual_card_num']
            if not any(p['card_number'] == card_num for p in pets_temp_data):
                birth_date = None
                try:
                    # Пробуем разные форматы даты
                    birth_date_str = row['birth_date']
                    for fmt in ('%Y%m%d', '%d%m%Y', '%Y-%m-%d', '%d-%m-%Y'):
                        try:
                            birth_date = datetime.strptime(birth_date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                except (ValueError, KeyError) as e:
                    print(f"Ошибка в дате для {card_num}: {e}")
                    continue

                if not birth_date:
                    print(f"Неверный формат даты для карточки {card_num}: {row['birth_date']}")
                    continue

                # Обработка полей животного
                pet_name = ' '.join(word.capitalize() for word in row['name'].lower().split())
                breed = row['breed_name'].strip().lower()
                color = row['color'].strip().lower()

                pets_temp_data.append({
                    'card_number': card_num,
                    'owner_id': owner_id,
                    'species': species_mapping.get(row['species'], 'Неизвестно'),
                    'breed': breed,
                    'color': color,
                    'name': pet_name,  # Кличка с заглавной буквы в каждом слове
                    'gender': sex_mapping.get(row['sex'], 'Неизвестно'),
                    'birth_date': birth_date
                })

    # Создаем владельцев
    for owner_id, data in owners_data.items():
        with db.session.no_autoflush:
            owner = Owner.query.get(owner_id)
            if not owner:
                owner = Owner(
                    id=owner_id,
                    name=data['name'],
                    phone=' '.join(data['phones']),
                    address=' '.join(data['addresses'])
                )
                db.session.add(owner)
    
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"Ошибка владельцев: {e}")
        return

    # Создаем животных
    for pet_data in pets_temp_data:
        with db.session.no_autoflush:
            if not Pet.query.filter_by(card_number=pet_data['card_number']).first():
                pet = Pet(
                    owner_id=pet_data['owner_id'],
                    name=pet_data['name'],
                    card_number=pet_data['card_number'],
                    species=pet_data['species'],
                    gender=pet_data['gender'],
                    breed=pet_data['breed'],
                    coloration=pet_data['color'],
                    birth_date=pet_data['birth_date'],
                    chronic_diseases='',  # Пустая строка
                    allergies=''          # Пустая строка
                )
                db.session.add(pet)

    try:
        db.session.commit()
        print(f"Успешно импортировано: {len(owners_data)} владельцев, {len(pets_temp_data)} животных")
    except IntegrityError as e:
        db.session.rollback()
        print(f"Ошибка животных: {e}")

def import_only_new_pets(filename):
    # Маппинги для преобразования значений
    species_mapping = {'1': 'Собака', '2': 'Кот', '3': 'Птица', '4': 'Грызун', '5': 'Лиса'}
    sex_mapping = {'1': 'М', '2': 'Ж', '3': 'КМ', '4': 'КЖ'}

    # Находим владельца Муху Андрея Леонидовича
    owner_name = "МУХА АНДРЕЙ ЛЕОНИДОВИЧ"
    owner = Owner.query.filter_by(name=owner_name).first()
    
    if not owner:
        print(f"Владелец {owner_name} не найден в базе данных!")
        return

    new_pets_count = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',')
        
        for row in reader:
            card_num = row['actual_card_num']
            
            # Проверяем, существует ли уже животное с таким номером карточки
            if Pet.query.filter_by(card_number=card_num).first():
                continue  # Пропускаем существующих животных
                
            # Обработка даты рождения
            birth_date = None
            try:
                birth_date_str = row['birth_date']
                for fmt in ('%Y%m%d', '%d%m%Y', '%Y-%m-%d', '%d-%m-%Y'):
                    try:
                        birth_date = datetime.strptime(birth_date_str, fmt).date()
                        break
                    except ValueError:
                        continue
            except (ValueError, KeyError) as e:
                print(f"Ошибка в дате для карточки {card_num}: {e}")
                continue

            if not birth_date:
                print(f"Неверный формат даты для карточки {card_num}: {row['birth_date']}")
                continue

            # Обработка полей животного
            pet_name = ' '.join(word.capitalize() for word in row['name'].lower().split())
            breed = row['breed_name'].strip().lower()
            color = row['color'].strip().lower()

            # Создаем новое животное
            pet = Pet(
                owner_id=owner.id,
                name=pet_name,
                card_number=card_num,
                species=species_mapping.get(row['species'], 'Неизвестно'),
                gender=sex_mapping.get(row['sex'], 'Неизвестно'),
                breed=breed,
                coloration=color,
                birth_date=birth_date,
                chronic_diseases='',
                allergies=''
            )
            
            db.session.add(pet)
            new_pets_count += 1

    try:
        db.session.commit()
        print(f"Успешно добавлено {new_pets_count} новых животных для владельца {owner_name}")
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при добавлении животных: {e}")

def import_vaccinations(filename):
    # Словарь для временного хранения и обработки данных
    temp_data = defaultdict(list)
    
    # Маппинг типов вакцин
    vaccine_type_mapping = {
        '8219': 'Бешенство',
        '8220': 'Вирусные',
        '8221': 'Грибковые'
    }
    
    # Исключения для правила 3 (вакцины, которые могут быть разных типов)
    exceptions = ['МУЛЬТИКАН 8', 'БИОФЕЛ PCHR', 'НОБИВАК RL', 'NOBIVAC RL']
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',')
        
        for row in reader:
            actual_card_num = row['actual_card_num']
            vac_type = row['vac_type']
            vac_date = row['vac_date']
            name = row['name'].strip().upper()
            comment = row['comment'].strip().upper()
            
            # Парсим дату (пробуем разные форматы)
            try:
                parsed_date = datetime.strptime(vac_date, '%Y%m%d').date()
            except ValueError:
                try:
                    parsed_date = datetime.strptime(vac_date, '%Y-%m-%d').date()
                except ValueError:
                    print(f"Неверный формат даты для карточки {actual_card_num}: {vac_date}")
                    continue
            
            # Нормализуем название вакцины
            normalized_comment = ' '.join(comment.split())  # Удаляем лишние пробелы
            
            # Добавляем во временное хранилище
            temp_data[(actual_card_num, parsed_date)].append({
                'actual_card_num': actual_card_num,
                'vac_date': parsed_date,
                'type': vac_type,
                'name': name,
                'comment': normalized_comment,
                'type_name': vaccine_type_mapping.get(vac_type, 'Неизвестно')
            })
    
    # Обрабатываем данные для устранения дубликатов
    processed_data = []
    
    for (actual_card_num, vac_date), vaccines in temp_data.items():
        # Словарь для хранения уникальных комбинаций тип+название
        unique_vaccines = {}
        
        for vaccine in vaccines:
            key = (vaccine['type'], vaccine['comment'])
            
            # Проверяем, нужно ли сохранять эту вакцину
            if key not in unique_vaccines:
                # Для исключений проверяем полное совпадение
                if any(exc in vaccine['comment'] for exc in exceptions):
                    # Ищем полное совпадение (тип и название)
                    if not any(v['type'] == vaccine['type'] and v['comment'] == vaccine['comment'] 
                              for v in unique_vaccines.values()):
                        unique_vaccines[key] = vaccine
                else:
                    # Для обычных вакцин проверяем только название
                    if not any(v['comment'] == vaccine['comment'] 
                              for v in unique_vaccines.values()):
                        unique_vaccines[key] = vaccine
        
        # Добавляем уникальные вакцины в обработанные данные
        processed_data.extend(unique_vaccines.values())
    
    # Удаляем существующие дубли перед импортом
    print("Поиск и удаление дубликатов вакцинаций...")
    duplicates_found = 0
    
    # Сначала проверяем и удаляем дубли в базе данных
    all_vaccinations = Vaccination.query.all()
    vaccination_keys = set()
    
    for vac in all_vaccinations:
        key = (
            vac.vaccine_name,
            vac.date_administered,
            vac.vaccination_type,
            vac.pet_id,
            vac.dose_ml
        )
        
        if key in vaccination_keys:
            # Нашли дубликат - удаляем
            db.session.delete(vac)
            duplicates_found += 1
        else:
            vaccination_keys.add(key)
    
    if duplicates_found > 0:
        try:
            db.session.commit()
            print(f"Удалено {duplicates_found} дубликатов вакцинаций")
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при удалении дубликатов: {e}")
    
    # Импортируем в базу данных, проверяя существующие записи
    imported_count = 0
    skipped_count = 0
    
    for vaccine in processed_data:
        # Находим животное по номеру карточки
        pet = Pet.query.filter_by(card_number=vaccine['actual_card_num']).first()
        if not pet:
            print(f"Животное с картой {vaccine['actual_card_num']} не найдено")
            skipped_count += 1
            continue
        
        # Проверяем, существует ли уже такая вакцинация
        existing = Vaccination.query.filter_by(
            vaccine_name=vaccine['comment'],
            date_administered=vaccine['vac_date'],
            vaccination_type=vaccine['type_name'],
            pet_id=pet.id
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # Создаем запись о вакцинации
        try:
            vaccination = Vaccination(
                vaccine_name=vaccine['comment'],
                date_administered=vaccine['vac_date'],
                vaccination_type=vaccine['type_name'],
                pet_id=pet.id,
                owner_id=pet.owner_id,
                dose_ml=1,  # Можно добавить логику для дозы, если есть данные
                previous_vaccination_date=None,
                next_due_date=None,
                owner_name=pet.owner.name,
                owner_address=pet.owner.address,
                pet_species=pet.species,
                pet_breed=pet.breed,
                pet_card_number=pet.card_number,
                pet_age=pet.pet_age()
            )
            
            db.session.add(vaccination)
            imported_count += 1
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при создании вакцинации: {e}")
            continue
    
    try:
        db.session.commit()
        print(f"Импорт завершен. Добавлено: {imported_count}, пропущено (уже существует): {skipped_count}")
    except IntegrityError as e:
        db.session.rollback()
        print(f"Ошибка при сохранении вакцинаций: {e}")

def import_owners_from_csv(filename):
    """
    Импорт владельцев из CSV файла с проверкой на дубликаты по ФИО в ВЕРХНЕМ РЕГИСТРЕ.
    Сохраняет только первый адрес и первый телефон для каждого владельца.
    Формат CSV: owner_name, value, type (9975 - адрес, 9981 - телефон)
    """
    # Словарь для временного хранения данных владельцев
    owners_data = defaultdict(lambda: {'phones': [], 'addresses': []})
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Приводим ФИО к верхнему регистру и удаляем лишние пробелы
            owner_name = ' '.join(word.upper() for word in row['owner_name'].strip().split())
            value = row['value'].strip()
            record_type = row['type']
            
            # Добавляем данные, только если соответствующего типа еще нет
            if record_type == '9975' and not owners_data[owner_name]['addresses']:  # Только первый адрес
                owners_data[owner_name]['addresses'].append(value)
            elif record_type == '9981' and not owners_data[owner_name]['phones']:  # Только первый телефон
                owners_data[owner_name]['phones'].append(value)
    
    # Импортируем в базу данных
    imported_count = 0
    skipped_count = 0
    
    for owner_name_upper, data in owners_data.items():
        # Проверяем, существует ли уже владелец с таким ФИО (в верхнем регистре)
        existing_owner = Owner.query.filter(
            db.func.upper(Owner.name) == owner_name_upper
        ).first()
        
        if existing_owner:
            skipped_count += 1
            continue
        
        # Создаем нового владельца
        try:
            # Берем первый адрес и первый телефон (или значения по умолчанию)
            address = data['addresses'][0] if data['addresses'] else 'НЕ УКАЗАН'
            phone = data['phones'][0] if data['phones'] else 'НЕ УКАЗАН'
            
            owner = Owner(
                name=owner_name_upper,  # Сохраняем в верхнем регистре
                address=address,
                phone=phone
            )
            
            db.session.add(owner)
            imported_count += 1
        except Exception as e:
            db.session.rollback()
            print(f"ОШИБКА ПРИ СОЗДАНИИ ВЛАДЕЛЬЦА {owner_name_upper}: {e}")
            continue
    
    try:
        db.session.commit()
        print(f"ИМПОРТ ЗАВЕРШЕН. ДОБАВЛЕНО: {imported_count}, ПРОПУЩЕНО (УЖЕ СУЩЕСТВУЕТ): {skipped_count}")
        return True
    except IntegrityError as e:
        db.session.rollback()
        print(f"ОШИБКА ПРИ СОХРАНЕНИИ ВЛАДЕЛЬЦЕВ: {e}")
        return False