#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка данных по бешенству в датасете
"""

from advanced_veterinary_dataset import AdvancedVeterinaryDataset
import pandas as pd

def check_rabies_data():
    """Проверка данных по бешенству"""
    print("Создаем датасет...")
    dataset = AdvancedVeterinaryDataset()
    df = dataset.create_realistic_dataset(n_samples=5000)
    
    print(f"Общее количество записей: {len(df)}")
    print(f"Количество заболеваний: {df['disease'].nunique()}")
    
    # Проверяем бешенство
    rabies_data = df[df['disease'] == 'бешенство']
    print(f"\nКоличество записей с бешенством: {len(rabies_data)}")
    
    if len(rabies_data) > 0:
        print("Примеры записей с бешенством:")
        for i, (idx, row) in enumerate(rabies_data.head(3).iterrows()):
            print(f"\nПример {i+1}:")
            print(f"  Тип животного: {row['animal_type']}")
            print(f"  Заболевание: {row['disease']}")
            
            # Показываем активные симптомы
            active_symptoms = []
            for col in df.columns:
                if col not in ['animal_type', 'disease'] and row[col] == 1:
                    active_symptoms.append(col)
            
            print(f"  Активные симптомы ({len(active_symptoms)}): {active_symptoms[:10]}...")
    else:
        print("БЕШЕНСТВО НЕ НАЙДЕНО в датасете!")
    
    # Проверяем распределение по типам животных
    print(f"\nРаспределение по типам животных:")
    animal_counts = df['animal_type'].value_counts()
    print(animal_counts)
    
    # Проверяем топ-10 заболеваний
    print(f"\nТоп-10 заболеваний:")
    disease_counts = df['disease'].value_counts().head(10)
    print(disease_counts)

if __name__ == "__main__":
    check_rabies_data()
