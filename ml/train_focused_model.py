#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обучение фокусированной модели только для собак с основными заболеваниями
"""

from advanced_veterinary_dataset import AdvancedVeterinaryDataset
from ml_model import AnimalDiseaseClassifier
import pandas as pd

def create_focused_dataset():
    """Создание фокусированного датасета только для собак"""
    dataset = AdvancedVeterinaryDataset()
    df = dataset.create_realistic_dataset(n_samples=10000)
    
    # Фильтруем только собак
    dogs_df = df[df['animal_type'] == 'собака'].copy()
    
    # Выбираем только основные заболевания собак
    main_dog_diseases = [
        'парвовирусный_энтерит', 'чума_плотоядных', 'бешенство', 'лептоспироз',
        'пироплазмоз', 'демодекоз', 'саркоптоз', 'пиодермия', 'дерматит',
        'гастроэнтерит', 'панкреатит', 'гепатит', 'нефрит', 'цистит',
        'пиелонефрит', 'дисплазия_тазобедренного_сустава', 'артрит',
        'дилатационная_кардиомиопатия', 'эндокардит', 'аритмия',
        'эпилепсия', 'менингит', 'энцефалит', 'паралич', 'слепота',
        'глухота', 'катаракта', 'глаукома', 'конъюнктивит', 'кератит',
        'отит', 'ринит', 'синусит', 'пневмония', 'плеврит',
        'астма', 'бронхит', 'ларингит', 'фарингит', 'стоматит',
        'гингивит', 'пародонтит', 'кариес', 'абсцесс', 'опухоль',
        'лейкемия', 'лимфома', 'саркома', 'аденокарцинома', 'меланома',
        'диабет', 'гипотиреоз', 'гипертиреоз', 'болезнь_кушинга',
        'болезнь_аддисона', 'ожирение', 'анорексия', 'булимия'
    ]
    
    # Фильтруем только основные заболевания
    focused_df = dogs_df[dogs_df['disease'].isin(main_dog_diseases)].copy()
    
    print(f"Фокусированный датасет:")
    print(f"  Записей: {len(focused_df)}")
    print(f"  Заболеваний: {focused_df['disease'].nunique()}")
    print(f"  Симптомов: {len([col for col in focused_df.columns if col not in ['animal_type', 'disease']])}")
    
    # Проверяем бешенство
    rabies_count = len(focused_df[focused_df['disease'] == 'бешенство'])
    print(f"  Записей с бешенством: {rabies_count}")
    
    return focused_df

def train_focused_model():
    """Обучение фокусированной модели"""
    print("Создаем фокусированный датасет...")
    df = create_focused_dataset()
    
    print("\nОбучаем модель...")
    classifier = AnimalDiseaseClassifier()
    results = classifier.train_models(df)
    
    # Находим лучшую модель
    best_model_name = max(results.keys(), key=lambda x: results[x]['cv_mean'])
    print(f"\nЛучшая модель: {best_model_name}")
    print(f"Точность: {results[best_model_name]['accuracy']:.3f}")
    
    print("\nСохраняем модель...")
    classifier.save_model('focused_dog_disease_model.pkl')
    
    print("\nТестируем модель...")
    test_cases = [
        {
            "name": "Симптомы бешенства",
            "symptoms": ["изменение_поведения", "агрессия", "водобоязнь", "светобоязнь", "гиперсаливация"]
        },
        {
            "name": "Симптомы парвовируса",
            "symptoms": ["лихорадка", "анорексия", "вялость", "рвота", "диарея"]
        },
        {
            "name": "Симптомы чумы",
            "symptoms": ["лихорадка", "анорексия", "вялость", "кашель", "выделения_из_носа"]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        predictions = classifier.predict(test_case['symptoms'], 'собака')
        for i, (disease, prob) in enumerate(predictions, 1):
            print(f"  {i}. {disease}: {prob:.4f} ({prob*100:.1f}%)")

if __name__ == "__main__":
    train_focused_model()
