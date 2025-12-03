#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест диагностики бешенства
"""

import requests
import json

def test_rabies_diagnosis():
    """Тестирование диагностики бешенства"""
    url = "http://localhost:5000/diagnose"
    
    # Симптомы бешенства
    test_cases = [
        {
            "name": "Классические симптомы бешенства",
            "animal_type": "собака",
            "symptoms": ["изменение_поведения", "агрессия", "водобоязнь", "светобоязнь", "гиперсаливация"]
        },
        {
            "name": "Симптомы бешенства + неврологические",
            "animal_type": "собака", 
            "symptoms": ["изменение_поведения", "агрессия", "водобоязнь", "светобоязнь", "гиперсаливация", "дисфагия", "паралич_глотки", "дезориентация"]
        },
        {
            "name": "Симптомы бешенства + лабораторные анализы",
            "animal_type": "собака",
            "symptoms": ["изменение_поведения", "агрессия", "водобоязнь", "светобоязнь", "гиперсаливация"],
            "lab_analyses": {
                "lab_wbc": "выше_нормы",
                "lab_glucose": "норма"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"ТЕСТ {i}: {test_case['name']}")
        print(f"{'='*60}")
        
        try:
            response = requests.post(url, json=test_case, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    print("OK Диагностика успешна")
                    print("\nПредсказания:")
                    for j, (disease, prob) in enumerate(data['predictions'], 1):
                        print(f"  {j}. {disease}: {prob:.4f} ({prob*100:.1f}%)")
                    
                    # Проверяем, есть ли бешенство в топ-5
                    diseases = [pred[0] for pred in data['predictions']]
                    if 'бешенство' in diseases:
                        print("НАЙДЕНО БЕШЕНСТВО в предсказаниях!")
                    else:
                        print("Бешенство НЕ найдено в предсказаниях")
                else:
                    print(f"Ошибка: {data['error']}")
            else:
                print(f"HTTP ошибка: {response.status_code}")
                print(f"Ответ: {response.text}")
                
        except Exception as e:
            print(f"Ошибка запроса: {e}")

if __name__ == "__main__":
    test_rabies_diagnosis()
