from datetime import datetime
from collections import defaultdict
import csv
from sqlalchemy.exc import IntegrityError
from models import db, Owner, Pet

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
                    continue  # Пропускаем запись с невалидной датой

                if not birth_date:
                    print(f"Неверный формат даты для карточки {card_num}: {row['birth_date']}")
                    continue

                pets_temp_data.append({
                    'card_number': card_num,
                    'owner_id': owner_id,
                    'species': species_mapping.get(row['species'], 'Неизвестно'),
                    'breed': row['breed_name'],
                    'color': row['color'],
                    'name': row['name'],
                    'gender': sex_mapping.get(row['sex'], 'Неизвестно'),
                    'birth_date': birth_date
                })

    # Создаем владельцев
    for owner_id, data in owners_data.items():
        with db.session.no_autoflush:  # Отключаем автофлаш
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

    # Создаем животных с проверкой даты
    for pet_data in pets_temp_data:
        with db.session.no_autoflush:  # Отключаем автофлаш
            if not Pet.query.filter_by(card_number=pet_data['card_number']).first():
                if not pet_data['birth_date']:
                    print(f"Пропуск животного {pet_data['card_number']} - нет даты рождения")
                    continue
                    
                pet = Pet(
                    owner_id=pet_data['owner_id'],
                    name=pet_data['name'],
                    card_number=pet_data['card_number'],
                    species=pet_data['species'],
                    gender=pet_data['gender'],
                    breed=pet_data['breed'],
                    coloration=pet_data['color'],
                    birth_date=pet_data['birth_date']
                )
                db.session.add(pet)

    try:
        db.session.commit()
        print(f"Успешно импортировано: {len(owners_data)} владельцев, {len(pets_temp_data)} животных")
    except IntegrityError as e:
        db.session.rollback()
        print(f"Ошибка животных: {e}")