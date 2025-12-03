#!/usr/bin/env python3
"""
Простой тест для проверки API
"""

import requests
import json

def test_simple():
    """Простой тест API"""
    url = 'http://localhost:5000/diagnose'
    
    # Простые данные
    data = {
        "animal_type": "собака",
        "symptoms": ["температура_повышена", "рвота"]
    }
    
    print("Тестирование API...")
    print(f"URL: {url}")
    print(f"Данные: {data}")
    
    try:
        response = requests.post(
            url, 
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Статус: {response.status_code}")
        print(f"Заголовки: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Результат: {result}")
        else:
            print(f"Ошибка: {response.text}")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_simple()
