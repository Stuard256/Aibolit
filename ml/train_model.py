#!/usr/bin/env python3
"""
Скрипт для обучения модели классификации заболеваний животных
Запуск: python train_model.py
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_model import AnimalDiseaseClassifier

def main():
    print("=" * 60)
    print("ОБУЧЕНИЕ МОДЕЛИ КЛАССИФИКАЦИИ ЗАБОЛЕВАНИЙ ЖИВОТНЫХ")
    print("=" * 60)
    print()
    
    try:
        # Создаем и обучаем модель
        classifier = AnimalDiseaseClassifier()
        
        # Создаем датасет
        print("1. Создание датасета...")
        df = classifier.create_dataset()
        print(f"   OK Создан датасет с {len(df)} записями")
        print(f"   OK Количество симптомов: {len(classifier.symptoms)}")
        print(f"   OK Количество заболеваний: {len(classifier.diseases)}")
        print()
        
        # Обучаем модели
        print("2. Обучение и сравнение моделей...")
        results = classifier.train_models(df)
        print()
        
        # Сохраняем модель
        print("3. Сохранение модели...")
        classifier.save_model()
        print()
        
        # Тестируем модель
        print("4. Тестирование модели:")
        print("-" * 40)
        
        # Примеры тестирования
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
            
            print("Результаты:")
            for j, (disease, prob) in enumerate(predictions, 1):
                print(f"  {j}. {disease.replace('_', ' ').title()}: {prob:.3f}")
            print()
        
        print("=" * 60)
        print("ОБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("=" * 60)
        print("Модель сохранена в файл: animal_disease_model.pkl")
        print("Теперь можно использовать диагностику на сайте!")
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
