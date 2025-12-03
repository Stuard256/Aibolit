#!/usr/bin/env python3
"""
Проверка состояния сервера
"""

import requests
import json

def check_server():
    """Проверка сервера"""
    print("Проверка сервера...")
    
    # Проверяем главную страницу
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        print(f"Главная страница: {response.status_code}")
    except Exception as e:
        print(f"Ошибка подключения к серверу: {e}")
        return False
    
    # Проверяем страницу диагностики
    try:
        response = requests.get('http://localhost:5000/diagnosis', timeout=5)
        print(f"Страница диагностики: {response.status_code}")
    except Exception as e:
        print(f"Ошибка страницы диагностики: {e}")
        return False
    
    # Проверяем API
    try:
        data = {"animal_type": "собака", "symptoms": ["температура_повышена"]}
        response = requests.post(
            'http://localhost:5000/diagnose',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        print(f"API диагностики: {response.status_code}")
        if response.status_code != 200:
            print(f"Ответ API: {response.text[:200]}...")
    except Exception as e:
        print(f"Ошибка API: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_server()
    if success:
        print("OK Сервер работает")
    else:
        print("ERROR Проблемы с сервером")
