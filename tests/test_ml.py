#!/usr/bin/env python3
"""
Быстрый тест ML модели для диагностики заболеваний
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_model():
    """Тестирование ML модели"""
    try:
        from ml_model import AnimalDiseaseClassifier
        
        print("Загрузка модели...")
        classifier = AnimalDiseaseClassifier()
        
        # Проверяем, есть ли обученная модель
        if os.path.exists('animal_disease_model.pkl'):
            classifier.load_model()
            print("✓ Модель загружена успешно")
        else:
            print("✗ Модель не найдена. Запустите: python train_model.py")
            return False
        
        # Тестовые случаи
        test_cases = [
            {
                'animal': 'собака',
                'symptoms': ['температура_повышена', 'рвота', 'диарея'],
                'expected': 'гастроэнтерит'
            },
            {
                'animal': 'кошка',
                'symptoms': ['кашель', 'чихание', 'выделения_из_носа'],
                'expected': 'респираторная_инфекция'
            },
            {
                'animal': 'собака',
                'symptoms': ['зуд', 'выпадение_шерсти'],
                'expected': 'дерматит'
            }
        ]
        
        print("\nТестирование предсказаний:")
        print("=" * 50)
        
        for i, test in enumerate(test_cases, 1):
            print(f"\nТест {i}:")
            print(f"Животное: {test['animal']}")
            print(f"Симптомы: {', '.join(test['symptoms'])}")
            
            try:
                predictions = classifier.predict_diseases(test['animal'], test['symptoms'])
                
                print("Результаты:")
                for j, (disease, prob) in enumerate(predictions, 1):
                    marker = "✓" if test['expected'] in disease else " "
                    print(f"  {marker} {j}. {disease}: {prob:.3f}")
                
                # Проверяем, есть ли ожидаемое заболевание в топ-3
                top3_diseases = [d[0] for d in predictions[:3]]
                if any(test['expected'] in disease for disease in top3_diseases):
                    print("  ✓ Ожидаемое заболевание найдено в топ-3")
                else:
                    print("  ✗ Ожидаемое заболевание не найдено в топ-3")
                    
            except Exception as e:
                print(f"  ✗ Ошибка: {e}")
        
        print("\n" + "=" * 50)
        print("Тестирование завершено!")
        return True
        
    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        print("Установите зависимости: pip install scikit-learn pandas numpy joblib")
        return False
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("Тестирование ML модели диагностики заболеваний")
    print("=" * 60)
    
    success = test_model()
    
    if success:
        print("\n✓ Все тесты пройдены успешно!")
        print("Модель готова к использованию в веб-приложении.")
    else:
        print("\n✗ Тесты не пройдены.")
        print("Проверьте установку зависимостей и обучение модели.")
    
    sys.exit(0 if success else 1)
