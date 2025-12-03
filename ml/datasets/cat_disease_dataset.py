#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Датасет заболеваний кошек с учетом частоты и лабораторных анализов
Часть 1: Импорты и класс
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

class CatDiseaseDataset:
    """
    Создание датасета заболеваний кошек с учетом частоты и специфики
    """
    
    def __init__(self):
        self.symptoms = []
        self.diseases = []
        self.animal_type = 'кошка'
        
        # Веса частоты заболеваний кошек (чем больше, тем чаще встречается)
        self.disease_frequency_weights = {
            # Очень частые заболевания
            'панлейкопения': 0.20,
            'калицивироз': 0.18,
            'ринотрахеит': 0.15,
            'хламидиоз': 0.12,
            'микоплазмоз': 0.10,
            'токсоплазмоз': 0.08,
            'бартонеллез': 0.08,
            'хроническая_болезнь_почек': 0.15,
            'мочекаменная_болезнь': 0.12,
            'диабет': 0.10,
            'гипертиреоз': 0.12,
            'астма': 0.08,
            'дерматит': 0.10,
            'конъюнктивит': 0.12,
            'отит': 0.10,
            'стоматит': 0.08,
            'гингивит': 0.10,
            'пародонтит': 0.08,
            'ожирение': 0.12,
            'анорексия': 0.08,
            
            # Частые заболевания
            'инфекционный_перитонит': 0.08,
            'лейкоз': 0.06,
            'иммунодефицит': 0.05,
            'герпесвирус': 0.12,
            'боррелиоз': 0.05,
            'эрлихиоз': 0.05,
            'анаплазмоз': 0.05,
            'бабезиоз': 0.04,
            'криптоспоридиоз': 0.05,
            'изоспороз': 0.05,
            'гиардиоз': 0.06,
            'токсокароз': 0.08,
            'анкилостомоз': 0.06,
            'дипилидиоз': 0.08,
            'эхинококкоз': 0.04,
            'альвеококкоз': 0.03,
            'описторхоз': 0.04,
            'клонорхоз': 0.03,
            'фасциолез': 0.03,
            'дикроцелиоз': 0.03,
            'метагонимоз': 0.03,
            'нанофиетоз': 0.03,
            'гетерофиоз': 0.03,
            'эуритрематоз': 0.03,
            'псевдоамфистомоз': 0.03,
            'стригоидоз': 0.03,
            'цистицеркоз': 0.03,
            'ценуроз': 0.03,
            'саркоцистоз': 0.03,
            'неоспороз': 0.03,
            
            # Редкие заболевания
            'бешенство': 0.08,
            'гастроэнтерит': 0.10,
            'панкреатит': 0.06,
            'гепатит': 0.06,
            'нефрит': 0.06,
            'цистит': 0.08,
            'пиелонефрит': 0.06,
            'артрит': 0.08,
            'дилатационная_кардиомиопатия': 0.06,
            'эндокардит': 0.04,
            'аритмия': 0.06,
            'эпилепсия': 0.06,
            'менингит': 0.04,
            'энцефалит': 0.04,
            'паралич': 0.04,
            'слепота': 0.04,
            'глухота': 0.04,
            'катаракта': 0.06,
            'глаукома': 0.04,
            'кератит': 0.06,
            'ринит': 0.08,
            'синусит': 0.06,
            'пневмония': 0.06,
            'плеврит': 0.04,
            'бронхит': 0.06,
            'ларингит': 0.04,
            'фарингит': 0.04,
            'кариес': 0.06,
            'абсцесс': 0.06,
            'опухоль': 0.04,
            'лейкемия': 0.03,
            'лимфома': 0.03,
            'саркома': 0.03,
            'аденокарцинома': 0.03,
            'меланома': 0.03,
            'гипотиреоз': 0.06,
            'болезнь_кушинга': 0.04,
            'болезнь_аддисона': 0.03,
            'булимия': 0.03,
        }
    def create_comprehensive_symptoms(self):
        """Создание полного списка симптомов для кошек"""
        self.symptoms = [
            # Общие симптомы
            'лихорадка', 'гипотермия', 'анорексия', 'полифагия', 'полидипсия',
            'полиурия', 'слабость', 'вялость', 'депрессия', 'апатия',
            'беспокойство', 'тревога', 'агрессия', 'изменение_поведения',
            
            # Желудочно-кишечные
            'рвота', 'диарея', 'запор', 'метеоризм', 'вздутие_живота',
            'боль_в_животе', 'кровь_в_кале', 'слизь_в_кале', 'черный_кал',
            'светлый_кал', 'жирный_кал', 'непереваренная_пища',
            
            # Дыхательные
            'кашель', 'чихание', 'выделения_из_носа', 'затрудненное_дыхание',
            'одышка', 'хрипы', 'свистящее_дыхание', 'кровь_из_носа',
            
            # Кожные
            'зуд', 'выпадение_шерсти', 'облысение', 'покраснение_кожи',
            'сыпь', 'язвы', 'корочки', 'шелушение', 'жирная_шерсть',
            'тусклая_шерсть', 'перхоть', 'пигментация', 'утолщение_кожи',
            
            # Глазные
            'выделения_из_глаз', 'слезотечение', 'покраснение_глаз',
            'помутнение_глаз', 'светобоязнь', 'боль_в_глазах',
            'снижение_зрения', 'зуд_в_глазах', 'отек_век',
            
            # Ушные
            'боль_в_ушах', 'выделения_из_ушей', 'зуд_в_ушах',
            'покачивание_головой', 'наклон_головы', 'снижение_слуха',
            'неприятный_запах_из_ушей',
            
            # Неврологические
            'судороги', 'паралич', 'нарушение_координации', 'головокружение',
            'потеря_сознания', 'атаксия', 'тремор', 'гиперрефлексия',
            'менингит', 'энцефалит', 'полиневрит', 'дископатия',
            'водобоязнь', 'фотофобия', 'гиперсаливация', 'дисфагия',
            'паралич_глотки', 'паралич_челюсти', 'агрессивность',
            'дезориентация', 'галлюцинации', 'спазмы_глотки',
            'судороги_дыхательных_мышц',
            
            # Мочеполовые
            'частое_мочеиспускание', 'затрудненное_мочеиспускание',
            'кровь_в_моче', 'боль_при_мочеиспускании', 'недержание_мочи',
            'увеличение_живота', 'выделения_из_половых_органов',
            
            # Опорно-двигательные
            'хромота', 'скованность', 'боль_в_суставах', 'отек_суставов',
            'снижение_активности', 'нежелание_двигаться',
            
            # Сердечно-сосудистые
            'учащенное_сердцебиение', 'замедленное_сердцебиение',
            'нерегулярное_сердцебиение', 'обмороки', 'бледность_слизистых',
            'цианоз', 'холодные_конечности',
            
            # Другие
            'потеря_веса', 'увеличение_веса', 'отеки', 'асцит',
            'увеличение_лимфоузлов', 'кровотечения', 'синяки',
            'пена_изо_рта', 'непроизвольное_мочеиспускание', 'слепота'
        ]
        
        # Лабораторные анализы
        lab_tests = [
            'wbc', 'rbc', 'hgb', 'hct', 'plt', 'mcv', 'mch', 'mchc',
            'glucose', 'urea', 'creatinine', 'alt', 'ast', 'alp', 'ggt',
            'total_protein', 'albumin', 'globulin', 'bilirubin_total',
            'bilirubin_direct', 'cholesterol', 'triglycerides',
            'urine_protein', 'urine_glucose', 'urine_ketones',
            'urine_blood', 'urine_leukocytes', 'urine_erythrocytes',
            'urine_specific_gravity', 'urine_ph'
        ]
        
        # Добавляем лабораторные тесты с вариантами
        for test in lab_tests:
            self.symptoms.extend([
                f'lab_{test}_ниже_нормы',
                f'lab_{test}_норма', 
                f'lab_{test}_выше_нормы'
            ])
        
        print(f"Создано {len(self.symptoms)} симптомов для кошек")
    def _assign_symptoms_for_disease(self, disease, symptoms_vector):
        """Назначение симптомов для конкретного заболевания кошки"""
        
        # Панлейкопения
        if disease == 'панлейкопения':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('депрессия')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_кале')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_ниже_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_glucose_ниже_нормы')] = 1
        
        # Калицивироз
        elif disease == 'калицивироз':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('чихание')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_глаз')] = 1
            symptoms_vector[self.symptoms.index('язвы_во_рту')] = 1
            symptoms_vector[self.symptoms.index('слюнотечение')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_ниже_нормы')] = 1
        
        # Ринотрахеит
        elif disease == 'ринотрахеит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('чихание')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_глаз')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_ниже_нормы')] = 1
        
        # Хламидиоз
        elif disease == 'хламидиоз':
            symptoms_vector[self.symptoms.index('выделения_из_глаз')] = 1
            symptoms_vector[self.symptoms.index('слезотечение')] = 1
            symptoms_vector[self.symptoms.index('покраснение_глаз')] = 1
            symptoms_vector[self.symptoms.index('конъюнктивит')] = 1
            symptoms_vector[self.symptoms.index('чихание')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
        
        # Микоплазмоз
        elif disease == 'микоплазмоз':
            symptoms_vector[self.symptoms.index('выделения_из_глаз')] = 1
            symptoms_vector[self.symptoms.index('слезотечение')] = 1
            symptoms_vector[self.symptoms.index('покраснение_глаз')] = 1
            symptoms_vector[self.symptoms.index('конъюнктивит')] = 1
            symptoms_vector[self.symptoms.index('чихание')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
        
        # Токсоплазмоз
        elif disease == 'токсоплазмоз':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('судороги')] = 1
            symptoms_vector[self.symptoms.index('атаксия')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_ниже_нормы')] = 1
        
        # Бартонеллез
        elif disease == 'бартонеллез':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('увеличение_лимфоузлов')] = 1
            symptoms_vector[self.symptoms.index('боль_в_суставах')] = 1
            symptoms_vector[self.symptoms.index('хромота')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Хроническая болезнь почек
        elif disease == 'хроническая_болезнь_почек':
            symptoms_vector[self.symptoms.index('полидипсия')] = 1
            symptoms_vector[self.symptoms.index('полиурия')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('lab_urea_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_creatinine_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_protein_выше_нормы')] = 1
        
        # Мочекаменная болезнь
        elif disease == 'мочекаменная_болезнь':
            symptoms_vector[self.symptoms.index('частое_мочеиспускание')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_мочеиспускание')] = 1
            symptoms_vector[self.symptoms.index('боль_при_мочеиспускании')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_моче')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_erythrocytes_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_protein_выше_нормы')] = 1
        
        # Диабет
        elif disease == 'диабет':
            symptoms_vector[self.symptoms.index('полидипсия')] = 1
            symptoms_vector[self.symptoms.index('полиурия')] = 1
            symptoms_vector[self.symptoms.index('полифагия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('lab_glucose_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_glucose_выше_нормы')] = 1
        
        # Гипертиреоз
        elif disease == 'гипертиреоз':
            symptoms_vector[self.symptoms.index('полифагия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('полидипсия')] = 1
            symptoms_vector[self.symptoms.index('полиурия')] = 1
            symptoms_vector[self.symptoms.index('беспокойство')] = 1
            symptoms_vector[self.symptoms.index('учащенное_сердцебиение')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('lab_glucose_выше_нормы')] = 1
        
        # Астма
        elif disease == 'астма':
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('хрипы')] = 1
            symptoms_vector[self.symptoms.index('свистящее_дыхание')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
        
        # Дерматит
        elif disease == 'дерматит':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            symptoms_vector[self.symptoms.index('шелушение')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('утолщение_кожи')] = 1
            symptoms_vector[self.symptoms.index('язвы')] = 1
        
        # Конъюнктивит
        elif disease == 'конъюнктивит':
            symptoms_vector[self.symptoms.index('выделения_из_глаз')] = 1
            symptoms_vector[self.symptoms.index('слезотечение')] = 1
            symptoms_vector[self.symptoms.index('покраснение_глаз')] = 1
            symptoms_vector[self.symptoms.index('зуд_в_глазах')] = 1
            symptoms_vector[self.symptoms.index('отек_век')] = 1
            symptoms_vector[self.symptoms.index('светобоязнь')] = 1
        
        # Отит
        elif disease == 'отит':
            symptoms_vector[self.symptoms.index('боль_в_ушах')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_ушей')] = 1
            symptoms_vector[self.symptoms.index('зуд_в_ушах')] = 1
            symptoms_vector[self.symptoms.index('покачивание_головой')] = 1
            symptoms_vector[self.symptoms.index('наклон_головы')] = 1
            symptoms_vector[self.symptoms.index('снижение_слуха')] = 1
            symptoms_vector[self.symptoms.index('неприятный_запах_из_ушей')] = 1
        
        # Стоматит
        elif disease == 'стоматит':
            symptoms_vector[self.symptoms.index('боль_во_рту')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_глотание')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('слюнотечение')] = 1
            symptoms_vector[self.symptoms.index('неприятный_запах_изо_рта')] = 1
            symptoms_vector[self.symptoms.index('язвы_во_рту')] = 1
            symptoms_vector[self.symptoms.index('покраснение_десен')] = 1
        
        # Гингивит
        elif disease == 'гингивит':
            symptoms_vector[self.symptoms.index('кровоточивость_десен')] = 1
            symptoms_vector[self.symptoms.index('покраснение_десен')] = 1
            symptoms_vector[self.symptoms.index('отек_десен')] = 1
            symptoms_vector[self.symptoms.index('неприятный_запах_изо_рта')] = 1
            symptoms_vector[self.symptoms.index('боль_во_рту')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
        
        # Пародонтит
        elif disease == 'пародонтит':
            symptoms_vector[self.symptoms.index('кровоточивость_десен')] = 1
            symptoms_vector[self.symptoms.index('покраснение_десен')] = 1
            symptoms_vector[self.symptoms.index('отек_десен')] = 1
            symptoms_vector[self.symptoms.index('неприятный_запах_изо_рта')] = 1
            symptoms_vector[self.symptoms.index('расшатывание_зубов')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
        
        # Ожирение
        elif disease == 'ожирение':
            symptoms_vector[self.symptoms.index('увеличение_веса')] = 1
            symptoms_vector[self.symptoms.index('снижение_активности')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('хромота')] = 1
            symptoms_vector[self.symptoms.index('артрит')] = 1
        
        # Анорексия
        elif disease == 'анорексия':
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('депрессия')] = 1
        # Инфекционный перитонит
        elif disease == 'инфекционный_перитонит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('увеличение_живота')] = 1
            symptoms_vector[self.symptoms.index('асцит')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_total_protein_выше_нормы')] = 1
        
        # Лейкоз
        elif disease == 'лейкоз':
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            symptoms_vector[self.symptoms.index('кровотечения')] = 1
            symptoms_vector[self.symptoms.index('увеличение_лимфоузлов')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_rbc_ниже_нормы')] = 1
        
        # Иммунодефицит
        elif disease == 'иммунодефицит':
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('частые_инфекции')] = 1
            symptoms_vector[self.symptoms.index('медленное_заживление')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_ниже_нормы')] = 1
        
        # Герпесвирус
        elif disease == 'герпесвирус':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('чихание')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_глаз')] = 1
            symptoms_vector[self.symptoms.index('конъюнктивит')] = 1
            symptoms_vector[self.symptoms.index('язвы_во_рту')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
        
        # Бешенство
        elif disease == 'бешенство':
            symptoms_vector[self.symptoms.index('изменение_поведения')] = 1
            symptoms_vector[self.symptoms.index('агрессия')] = 1
            symptoms_vector[self.symptoms.index('водобоязнь')] = 1
            symptoms_vector[self.symptoms.index('светобоязнь')] = 1
            symptoms_vector[self.symptoms.index('гиперсаливация')] = 1
            symptoms_vector[self.symptoms.index('дисфагия')] = 1
            symptoms_vector[self.symptoms.index('паралич_глотки')] = 1
            symptoms_vector[self.symptoms.index('паралич_челюсти')] = 1
            symptoms_vector[self.symptoms.index('дезориентация')] = 1
            symptoms_vector[self.symptoms.index('галлюцинации')] = 1
            symptoms_vector[self.symptoms.index('спазмы_глотки')] = 1
            symptoms_vector[self.symptoms.index('судороги_дыхательных_мышц')] = 1
            symptoms_vector[self.symptoms.index('пена_изо_рта')] = 1
        
        # Гастроэнтерит
        elif disease == 'гастроэнтерит':
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('вздутие_живота')] = 1
            symptoms_vector[self.symptoms.index('метеоризм')] = 1
        
        # Панкреатит
        elif disease == 'панкреатит':
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('lab_alt_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_ast_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_glucose_выше_нормы')] = 1
        
        # Гепатит
        elif disease == 'гепатит':
            symptoms_vector[self.symptoms.index('желтуха')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('увеличение_живота')] = 1
            symptoms_vector[self.symptoms.index('lab_alt_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_ast_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_bilirubin_total_выше_нормы')] = 1
        
        # Нефрит
        elif disease == 'нефрит':
            symptoms_vector[self.symptoms.index('частое_мочеиспускание')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_моче')] = 1
            symptoms_vector[self.symptoms.index('боль_при_мочеиспускании')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('lab_urea_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_creatinine_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_protein_выше_нормы')] = 1
        
        # Цистит
        elif disease == 'цистит':
            symptoms_vector[self.symptoms.index('частое_мочеиспускание')] = 1
            symptoms_vector[self.symptoms.index('боль_при_мочеиспускании')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_моче')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_leukocytes_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_erythrocytes_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_protein_выше_нормы')] = 1
        
        # Пиелонефрит
        elif disease == 'пиелонефрит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_моче')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_leukocytes_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_urine_erythrocytes_выше_нормы')] = 1
        
        # Артрит
        elif disease == 'артрит':
            symptoms_vector[self.symptoms.index('хромота')] = 1
            symptoms_vector[self.symptoms.index('скованность')] = 1
            symptoms_vector[self.symptoms.index('боль_в_суставах')] = 1
            symptoms_vector[self.symptoms.index('отек_суставов')] = 1
            symptoms_vector[self.symptoms.index('снижение_активности')] = 1
            symptoms_vector[self.symptoms.index('нежелание_двигаться')] = 1
        
        # Дилатационная кардиомиопатия
        elif disease == 'дилатационная_кардиомиопатия':
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('обмороки')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('увеличение_живота')] = 1
            symptoms_vector[self.symptoms.index('учащенное_сердцебиение')] = 1
        
        # Эндокардит
        elif disease == 'эндокардит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('учащенное_сердцебиение')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Аритмия
        elif disease == 'аритмия':
            symptoms_vector[self.symptoms.index('учащенное_сердцебиение')] = 1
            symptoms_vector[self.symptoms.index('замедленное_сердцебиение')] = 1
            symptoms_vector[self.symptoms.index('нерегулярное_сердцебиение')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('обмороки')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
        
        # Эпилепсия
        elif disease == 'эпилепсия':
            symptoms_vector[self.symptoms.index('судороги')] = 1
            symptoms_vector[self.symptoms.index('потеря_сознания')] = 1
            symptoms_vector[self.symptoms.index('пена_изо_рта')] = 1
            symptoms_vector[self.symptoms.index('непроизвольное_мочеиспускание')] = 1
            symptoms_vector[self.symptoms.index('дезориентация')] = 1
            symptoms_vector[self.symptoms.index('атаксия')] = 1
        
        # Менингит
        elif disease == 'менингит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('головная_боль')] = 1
            symptoms_vector[self.symptoms.index('ригидность_затылка')] = 1
            symptoms_vector[self.symptoms.index('светобоязнь')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('судороги')] = 1
            symptoms_vector[self.symptoms.index('дезориентация')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Энцефалит
        elif disease == 'энцефалит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('головная_боль')] = 1
            symptoms_vector[self.symptoms.index('судороги')] = 1
            symptoms_vector[self.symptoms.index('дезориентация')] = 1
            symptoms_vector[self.symptoms.index('галлюцинации')] = 1
            symptoms_vector[self.symptoms.index('паралич')] = 1
            symptoms_vector[self.symptoms.index('атаксия')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Паралич
        elif disease == 'паралич':
            symptoms_vector[self.symptoms.index('паралич')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('атаксия')] = 1
            symptoms_vector[self.symptoms.index('недержание_мочи')] = 1
            symptoms_vector[self.symptoms.index('недержание_кала')] = 1
            symptoms_vector[self.symptoms.index('снижение_активности')] = 1
        
        # Слепота
        elif disease == 'слепота':
            symptoms_vector[self.symptoms.index('слепота')] = 1
            symptoms_vector[self.symptoms.index('снижение_зрения')] = 1
            symptoms_vector[self.symptoms.index('дезориентация')] = 1
            symptoms_vector[self.symptoms.index('столкновения_с_предметами')] = 1
            symptoms_vector[self.symptoms.index('расширенные_зрачки')] = 1
        
        # Глухота
        elif disease == 'глухота':
            symptoms_vector[self.symptoms.index('глухота')] = 1
            symptoms_vector[self.symptoms.index('снижение_слуха')] = 1
            symptoms_vector[self.symptoms.index('не_реагирует_на_звуки')] = 1
            symptoms_vector[self.symptoms.index('дезориентация')] = 1
        
        # Катаракта
        elif disease == 'катаракта':
            symptoms_vector[self.symptoms.index('помутнение_глаз')] = 1
            symptoms_vector[self.symptoms.index('снижение_зрения')] = 1
            symptoms_vector[self.symptoms.index('слепота')] = 1
            symptoms_vector[self.symptoms.index('дезориентация')] = 1
        
        # Глаукома
        elif disease == 'глаукома':
            symptoms_vector[self.symptoms.index('боль_в_глазах')] = 1
            symptoms_vector[self.symptoms.index('светобоязнь')] = 1
            symptoms_vector[self.symptoms.index('слезотечение')] = 1
            symptoms_vector[self.symptoms.index('покраснение_глаз')] = 1
            symptoms_vector[self.symptoms.index('снижение_зрения')] = 1
            symptoms_vector[self.symptoms.index('расширенные_зрачки')] = 1
        
        # Кератит
        elif disease == 'кератит':
            symptoms_vector[self.symptoms.index('боль_в_глазах')] = 1
            symptoms_vector[self.symptoms.index('светобоязнь')] = 1
            symptoms_vector[self.symptoms.index('слезотечение')] = 1
            symptoms_vector[self.symptoms.index('покраснение_глаз')] = 1
            symptoms_vector[self.symptoms.index('помутнение_глаз')] = 1
            symptoms_vector[self.symptoms.index('снижение_зрения')] = 1
        
        # Ринит
        elif disease == 'ринит':
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('чихание')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('снижение_обоняния')] = 1
            symptoms_vector[self.symptoms.index('кровь_из_носа')] = 1
        
        # Синусит
        elif disease == 'синусит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('головная_боль')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('боль_в_лице')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Пневмония
        elif disease == 'пневмония':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('хрипы')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Плеврит
        elif disease == 'плеврит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('боль_в_груди')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Бронхит
        elif disease == 'бронхит':
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('хрипы')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Ларингит
        elif disease == 'ларингит':
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('хрипота')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('боль_в_горле')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
        
        # Фарингит
        elif disease == 'фарингит':
            symptoms_vector[self.symptoms.index('боль_в_горле')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_глотание')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
        
        # Кариес
        elif disease == 'кариес':
            symptoms_vector[self.symptoms.index('боль_во_рту')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_глотание')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('неприятный_запах_изо_рта')] = 1
            symptoms_vector[self.symptoms.index('слюнотечение')] = 1
        
        # Абсцесс
        elif disease == 'абсцесс':
            symptoms_vector[self.symptoms.index('отек')] = 1
            symptoms_vector[self.symptoms.index('боль')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Опухоль
        elif disease == 'опухоль':
            symptoms_vector[self.symptoms.index('отек')] = 1
            symptoms_vector[self.symptoms.index('боль')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('увеличение_лимфоузлов')] = 1
        
        # Лейкемия
        elif disease == 'лейкемия':
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            symptoms_vector[self.symptoms.index('кровотечения')] = 1
            symptoms_vector[self.symptoms.index('увеличение_лимфоузлов')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
            symptoms_vector[self.symptoms.index('lab_rbc_ниже_нормы')] = 1
        
        # Лимфома
        elif disease == 'лимфома':
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('увеличение_лимфоузлов')] = 1
            symptoms_vector[self.symptoms.index('отек')] = 1
            symptoms_vector[self.symptoms.index('lab_wbc_выше_нормы')] = 1
        
        # Саркома
        elif disease == 'саркома':
            symptoms_vector[self.symptoms.index('отек')] = 1
            symptoms_vector[self.symptoms.index('боль')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('хромота')] = 1
        
        # Аденокарцинома
        elif disease == 'аденокарцинома':
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_кале')] = 1
            symptoms_vector[self.symptoms.index('увеличение_живота')] = 1
        
        # Меланома
        elif disease == 'меланома':
            symptoms_vector[self.symptoms.index('пигментация')] = 1
            symptoms_vector[self.symptoms.index('изменение_цвета_кожи')] = 1
            symptoms_vector[self.symptoms.index('отек')] = 1
            symptoms_vector[self.symptoms.index('боль')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
        
        # Гипотиреоз
        elif disease == 'гипотиреоз':
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('увеличение_веса')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('сухая_кожа')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('lab_glucose_ниже_нормы')] = 1
        
        # Болезнь Кушинга
        elif disease == 'болезнь_кушинга':
            symptoms_vector[self.symptoms.index('полидипсия')] = 1
            symptoms_vector[self.symptoms.index('полиурия')] = 1
            symptoms_vector[self.symptoms.index('полифагия')] = 1
            symptoms_vector[self.symptoms.index('увеличение_веса')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('тонкая_кожа')] = 1
            symptoms_vector[self.symptoms.index('lab_glucose_выше_нормы')] = 1
        
        # Болезнь Аддисона
        elif disease == 'болезнь_аддисона':
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('lab_glucose_ниже_нормы')] = 1
        
        # Булимия
        elif disease == 'булимия':
            symptoms_vector[self.symptoms.index('полифагия')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
    def create_weighted_dataset(self, n_samples=30000):
        """Создание взвешенного датасета для кошек"""
        print(f"Создание датасета для кошек с {n_samples} образцами...")
        
        # Создаем списки симптомов и заболеваний
        self.create_comprehensive_symptoms()
        self.diseases = list(self.disease_frequency_weights.keys())
        
        print(f"Количество заболеваний: {len(self.diseases)}")
        print(f"Количество симптомов: {len(self.symptoms)}")
        
        # Нормализуем веса
        total_weight = sum(self.disease_frequency_weights.values())
        normalized_weights = {k: v/total_weight for k, v in self.disease_frequency_weights.items()}
        
        # Создаем данные
        data = []
        for _ in range(n_samples):
            # Выбираем заболевание на основе весов
            disease = np.random.choice(self.diseases, p=list(normalized_weights.values()))
            
            # Создаем вектор симптомов
            symptoms_vector = np.zeros(len(self.symptoms))
            
            # Назначаем симптомы для заболевания
            self._assign_symptoms_for_disease(disease, symptoms_vector)
            
            # Добавляем случайный шум (не все симптомы могут проявляться)
            noise_mask = np.random.random(len(self.symptoms)) < 0.1
            symptoms_vector[noise_mask] = 1 - symptoms_vector[noise_mask]
            
            # Создаем запись
            record = {
                'animal_type': self.animal_type,
                'disease': disease
            }
            
            # Добавляем симптомы
            for i, symptom in enumerate(self.symptoms):
                record[symptom] = int(symptoms_vector[i])
            
            data.append(record)
        
        df = pd.DataFrame(data)
        print(f"Создан датасет с {len(df)} записями")
        print(f"Распределение по заболеваниям:")
        disease_counts = df['disease'].value_counts()
        for disease, count in disease_counts.head(10).items():
            print(f"  {disease}: {count} ({count/len(df)*100:.1f}%)")
        
        return df

    def get_disease_info(self, disease):
        """Получение информации о заболевании"""
        if disease in self.disease_frequency_weights:
            weight = self.disease_frequency_weights[disease]
            return {
                'disease': disease,
                'frequency_weight': weight,
                'is_common': weight > 0.1
            }
        return None

if __name__ == "__main__":
    # Тестирование датасета
    dataset = CatDiseaseDataset()
    df = dataset.create_weighted_dataset(1000)
    print(f"\nПервые 5 записей:")
    print(df[['animal_type', 'disease']].head())
    print(f"\nСтатистика симптомов:")
    symptom_counts = df.drop(['animal_type', 'disease'], axis=1).sum()
    print(symptom_counts.head(10))
