#!/usr/bin/env python3
"""
Запуск тестов
"""

import subprocess
import time
import requests
import json

def run_tests():
    """Запуск тестов"""
    print("Запуск тестов...")
    
    # Проверяем, что модель существует
    import os
    if not os.path.exists('animal_disease_model.pkl'):
        print("ERROR Модель не найдена. Запустите: python train_model.py")
        return False
    
    print("OK Модель найдена")
    
    # Проверяем API
    try:
        data = {"animal_type": "собака", "symptoms": ["температура_повышена", "рвота"]}
        response = requests.post(
            'http://localhost:5000/diagnose',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        print(f"API статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Результат: {result}")
            return True
        else:
            print(f"Ошибка API: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR Сервер не запущен. Запустите: python app.py")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("OK Тесты пройдены")
    else:
        print("ERROR Тесты не пройдены")
