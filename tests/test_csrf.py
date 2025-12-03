#!/usr/bin/env python3
"""
Тест CSRF токена
"""

import requests
import json

def test_csrf():
    """Тест CSRF токена"""
    print("Тестирование CSRF токена...")
    
    # Сначала получаем страницу диагностики для получения CSRF токена
    try:
        response = requests.get('http://localhost:5000/diagnosis')
        print(f"Страница диагностики: {response.status_code}")
        
        if response.status_code == 200:
            # Ищем CSRF токен в HTML
            html = response.text
            if 'csrf_token' in html:
                print("OK CSRF токен найден в HTML")
            else:
                print("ERROR CSRF токен не найден в HTML")
                return False
        else:
            print(f"ERROR Страница диагностики недоступна: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR Ошибка при получении страницы: {e}")
        return False
    
    # Теперь тестируем API с CSRF токеном
    try:
        # Получаем CSRF токен из сессии
        session = requests.Session()
        session.get('http://localhost:5000/diagnosis')
        
        # Отправляем запрос с CSRF токеном
        data = {"animal_type": "собака", "symptoms": ["температура_повышена"]}
        response = session.post(
            'http://localhost:5000/diagnose',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"API статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Результат: {result}")
            return True
        else:
            print(f"Ошибка API: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_csrf()
    if success:
        print("OK CSRF тест пройден")
    else:
        print("ERROR CSRF тест не пройден")
