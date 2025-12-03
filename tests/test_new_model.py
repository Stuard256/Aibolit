#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование новой модели с расширенным датасетом
"""

from ml_model import AnimalDiseaseClassifier

def test_model():
    """Тестирование обученной модели"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ НОВОЙ МОДЕЛИ С РАСШИРЕННЫМ ДАТАСЕТОМ")
    print("=" * 60)
    
    # Загружаем модель
    classifier = AnimalDiseaseClassifier()
    if not classifier.load_model():
        print("Ошибка: Не удалось загрузить модель")
        return
    
    print(f"Модель загружена успешно!")
    print(f"Количество симптомов: {len(classifier.symptoms)}")
    print(f"Количество заболеваний: {len(classifier.diseases)}")
    print(f"Количество признаков: {len(classifier.feature_names)}")
    print()
    
    # Тестовые случаи
    test_cases = [
        {
            'animal': 'собака',
            'symptoms': ['лихорадка', 'рвота', 'диарея', 'анорексия'],
            'description': 'Парвовирусный энтерит'
        },
        {
            'animal': 'собака',
            'symptoms': ['изменение_поведения', 'агрессия', 'водобоязнь'],
            'description': 'Бешенство'
        },
        {
            'animal': 'кошка',
            'symptoms': ['зуд', 'выпадение_шерсти'],
            'description': 'Дерматит'
        },
        {
            'animal': 'собака',
            'symptoms': ['лихорадка', 'частое_мочеиспускание', 'болезненное_мочеиспускание', 'кровь_в_моче'],
            'description': 'Цистит'
        },
        {
            'animal': 'собака',
            'symptoms': ['лихорадка', 'боль_в_области_поясницы', 'кровь_в_моче', 'моча_как_мясные_помои'],
            'description': 'Пиелонефрит'
        },
        {
            'animal': 'кошка',
            'symptoms': ['полифагия', 'полиурия', 'полидипсия', 'потеря_веса', 'жажда'],
            'description': 'Диабет'
        },
        {
            'animal': 'собака',
            'symptoms': ['выпячивание_глаз', 'повышение_внутриглазного_давления', 'светобоязнь'],
            'description': 'Глаукома'
        },
        {
            'animal': 'собака',
            'symptoms': ['бак_глюкоза_выше_нормы', 'бам_глюкоза_выше_нормы', 'полиурия', 'полидипсия'],
            'description': 'Диабет с лабораторными анализами'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Тест {i}: {test_case['description']}")
        print(f"Животное: {test_case['animal']}")
        print(f"Симптомы: {', '.join(test_case['symptoms'])}")
        
        predictions = classifier.predict(
            test_case['animal'], 
            test_case['symptoms']
        )
        
        if predictions:
            print("Результаты:")
            for j, (disease, prob) in enumerate(predictions, 1):
                print(f"  {j}. {disease.replace('_', ' ').title()}: {prob:.3f}")
        else:
            print("  Ошибка: Не удалось получить предсказания")
        print()
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("=" * 60)

if __name__ == "__main__":
    test_model()
