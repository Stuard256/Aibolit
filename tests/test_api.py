#!/usr/bin/env python3
"""
Тест API диагностики заболеваний
"""

import requests
import json

def test_diagnosis_api():
    """Тестирование API диагностики"""
    url = 'http://localhost:5000/diagnose'
    
    # Тестовые данные
    test_data = {
        "animal_type": "собака",
        "symptoms": ["температура_повышена", "рвота", "диарея", "аппетит_снижен"]
    }
    
    print("Тестирование API диагностики...")
    print(f"URL: {url}")
    print(f"Данные: {json.dumps(test_data, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        
        print(f"Статус ответа: {response.status_code}")
        print(f"Заголовки: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("JSON ответ:")
                print(json.dumps(data, ensure_ascii=False, indent=2))
                
                if data.get('success'):
                    print("\n✓ Диагностика прошла успешно!")
                    predictions = data.get('predictions', [])
                    print("\nРезультаты:")
                    for i, (disease, prob) in enumerate(predictions, 1):
                        print(f"{i}. {disease}: {prob:.3f}")
                else:
                    print(f"\n✗ Ошибка: {data.get('error')}")
                    
            except json.JSONDecodeError as e:
                print(f"✗ Ошибка парсинга JSON: {e}")
                print(f"Сырой ответ: {response.text[:500]}...")
        else:
            print(f"✗ HTTP ошибка: {response.status_code}")
            print(f"Ответ: {response.text[:500]}...")
            
    except requests.exceptions.ConnectionError:
        print("✗ Ошибка подключения. Убедитесь, что сервер запущен на localhost:5000")
    except requests.exceptions.Timeout:
        print("✗ Таймаут запроса")
    except Exception as e:
        print(f"✗ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    test_diagnosis_api()
