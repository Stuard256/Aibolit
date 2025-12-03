#!/usr/bin/env python3
"""
Проверка загруженной ML модели
"""

import os
import joblib
import numpy as np

def check_model():
    """Проверка модели"""
    print("Проверка ML модели...")
    print("=" * 40)
    
    # Проверяем существование файла
    if not os.path.exists('animal_disease_model.pkl'):
        print("ERROR Файл animal_disease_model.pkl не найден")
        print("Запустите: python train_model.py")
        return False
    
    print("OK Файл модели найден")
    
    try:
        # Загружаем модель
        model_data = joblib.load('animal_disease_model.pkl')
        print("OK Модель загружена успешно")
        
        # Проверяем структуру
        if isinstance(model_data, dict):
            print("OK Модель загружена как словарь")
            
            required_keys = ['model', 'label_encoder', 'scaler', 'symptoms', 'diseases']
            for key in required_keys:
                if key in model_data:
                    print(f"OK Ключ '{key}' найден")
                else:
                    print(f"ERROR Ключ '{key}' отсутствует")
                    return False
            
            # Проверяем модель
            model = model_data['model']
            print(f"OK Модель: {type(model).__name__}")
            
            # Проверяем симптомы
            symptoms = model_data['symptoms']
            print(f"OK Симптомов: {len(symptoms)}")
            
            # Проверяем заболевания
            diseases = model_data['diseases']
            print(f"OK Заболеваний: {len(diseases)}")
            
            # Тестируем предсказание
            print("\nТестирование предсказания...")
            
            # Создаем тестовый вектор
            features = np.zeros(len(symptoms) + 1)
            features[0] = 0  # собака
            features[1] = 1  # температура_повышена
            features[2] = 1  # рвота
            features[3] = 1  # диарея
            
            try:
                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(features.reshape(1, -1))[0]
                    classes = model.classes_
                    print("OK Предсказание успешно")
                    print(f"  Классов: {len(classes)}")
                    print(f"  Вероятности: {probabilities[:3]}...")
                else:
                    print("ERROR Модель не поддерживает predict_proba")
                    return False
                    
            except Exception as e:
                print(f"ERROR Ошибка при предсказании: {e}")
                return False
                
        else:
            print("OK Модель загружена как объект")
            # Это старая версия модели
            if hasattr(model_data, 'predict_diseases'):
                print("OK Метод predict_diseases найден")
            else:
                print("ERROR Метод predict_diseases не найден")
                return False
        
        print("\nOK Модель готова к использованию!")
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка при загрузке модели: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_model()
    if success:
        print("\n🎉 Модель работает корректно!")
    else:
        print("\n❌ Проблемы с моделью. Проверьте обучение.")
