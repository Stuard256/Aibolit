#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система машинного обучения для диагностики заболеваний животных
с реальными симптомами и заболеваниями
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
import joblib

class AnimalDiseaseClassifier:
    """
    Классификатор заболеваний животных с использованием машинного обучения
    """
    
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.symptoms = []
        self.diseases = []
        self.feature_names = []
        
    def create_dataset(self):
        """
        Создание датасета с реальными симптомами и заболеваниями животных
        """
        # Импортируем расширенный датасет
        try:
            from advanced_veterinary_dataset import AdvancedVeterinaryDataset
            advanced_dataset = AdvancedVeterinaryDataset()
            df = advanced_dataset.create_realistic_dataset(n_samples=5000)
            
            # Извлекаем симптомы и заболевания
            self.symptoms = advanced_dataset.symptoms
            self.diseases = advanced_dataset.diseases
            
            return df
            
        except ImportError:
            print("Ошибка: Не удалось импортировать advanced_veterinary_dataset.py")
            print("Пробуем базовый датасет...")
            try:
                from real_veterinary_dataset import RealVeterinaryDataset
                real_dataset = RealVeterinaryDataset()
                df = real_dataset.create_realistic_dataset(n_samples=5000)
                
                # Извлекаем симптомы и заболевания
                self.symptoms = real_dataset.symptoms
                self.diseases = real_dataset.diseases
                
                return df
                
            except ImportError:
                print("Ошибка: Не удалось импортировать real_veterinary_dataset.py")
                print("Создаем базовый датасет...")
                return self._create_basic_dataset()
    
    def _create_basic_dataset(self):
        """Создание базового датасета если реальный недоступен"""
        # Симптомы (признаки) - базовый список
        symptoms = [
            # Общие симптомы
            'лихорадка', 'гипотермия', 'анорексия', 'полифагия', 'вялость', 
            'слабость', 'депрессия', 'беспокойство', 'агрессия', 'изменение_поведения',
            
            # Желудочно-кишечные
            'рвота', 'диарея', 'запор', 'вздутие_живота', 'боль_в_животе',
            'слюнотечение', 'тошнота', 'кровь_в_кале', 'черный_стул', 'мелена',
            'асцит', 'увеличение_печени', 'желтуха', 'бледность_слизистых',
            
            # Дыхательные
            'кашель', 'чихание', 'выделения_из_носа', 'затрудненное_дыхание',
            'учащенное_дыхание', 'хрипы', 'одышка', 'кровь_из_носа', 'цианоз',
            'пневмония', 'плеврит', 'ринит', 'синусит',
            
            # Кожа и шерсть
            'зуд', 'выпадение_шерсти', 'покраснение_кожи', 'сыпь', 'язвы_на_коже',
            'сухая_кожа', 'жирная_кожа', 'перхоть', 'пятна_на_коже', 'алопеция',
            'дерматит', 'экзема', 'пиодермия', 'фурункулез',
            
            # Глаза
            'выделения_из_глаз', 'покраснение_глаз', 'помутнение_глаз', 'слезотечение',
            'светобоязнь', 'косоглазие', 'выпячивание_глаз', 'конъюнктивит',
            'кератит', 'увеит', 'катаракта', 'глаукома',
            
            # Неврологические
            'судороги', 'паралич', 'нарушение_координации', 'головокружение',
            'потеря_сознания', 'атаксия', 'тремор', 'гиперрефлексия',
            'менингит', 'энцефалит', 'полиневрит', 'дископатия',
            
            # Мочеполовые
            'частое_мочеиспускание', 'редкое_мочеиспускание', 'кровь_в_моче',
            'болезненное_мочеиспускание', 'недержание_мочи', 'полиурия',
            'олигурия', 'анурия', 'протеинурия', 'гематурия',
            
            # Опорно-двигательные
            'хромота', 'скованность_движений', 'боль_в_суставах', 'мышечная_слабость',
            'деформация_конечностей', 'нежелание_двигаться', 'артрит', 'миозит',
            'остеопороз', 'переломы', 'вывихи', 'растяжения',
            
            # Сердечно-сосудистые
            'учащенное_сердцебиение', 'замедленное_сердцебиение', 'аритмия',
            'отеки', 'бледность_слизистых', 'синюшность_слизистых', 
            'холодные_конечности', 'кардиомиопатия', 'сердечная_недостаточность',
            'гипертония', 'гипотония', 'тромбоэмболия',
            
            # Другие
            'увеличение_лимфоузлов', 'потеря_веса', 'увеличение_веса', 'жажда',
            'полидипсия', 'неприятный_запах_изо_рта', 'кровоточивость_десен',
            'стоматит', 'гингивит', 'пародонтит', 'кариес',
            
            # Специфические инфекционные
            'водобоязнь', 'светобоязнь', 'фотофобия', 'гиперсаливация',
            'дисфагия', 'паралич_глотки', 'паралич_челюсти', 'агрессивность',
            'дезориентация', 'галлюцинации', 'спазмы_глотки', 'судороги_дыхательных_мышц'
        ]
        
        # Заболевания - базовый список
        diseases = [
            # ИНФЕКЦИОННЫЕ ЗАБОЛЕВАНИЯ СОБАК
            'парвовирусный_энтерит', 'чума_плотоядных', 'бешенство', 'лептоспироз',
            'инфекционный_гепатит', 'аденовирусная_инфекция', 'коронавирусная_инфекция',
            'бордетеллез', 'микоплазмоз', 'хламидиоз', 'риккетсиоз', 'эрлихиоз',
            'анаплазмоз', 'бабезиоз', 'лейшманиоз', 'токсоплазмоз', 'криптоспоридиоз',
            'кокцидиоз', 'лямблиоз', 'трихомоноз', 'кандидоз', 'аспергиллез',
            'гистоплазмоз', 'бластомикоз', 'кокцидиоидомикоз', 'споротрихоз',
            'дерматофитоз', 'малассезиоз', 'демодекоз', 'саркоптоз', 'нотоэдроз',
            'отодектоз', 'хейлетиеллез', 'блошиная_инвазия', 'вшивость',
            'клещевая_инвазия', 'дирофиляриоз', 'токсокароз', 'токсаскаридоз',
            'анкилостомоз', 'стронгилоидоз', 'трихоцефалез', 'дипилидиоз',
            'тениоз', 'эхинококкоз', 'альвеококкоз', 'спарганоз',
            
            # ИНФЕКЦИОННЫЕ ЗАБОЛЕВАНИЯ КОШЕК
            'панлейкопения', 'калицивироз', 'ринотрахеит', 'вирусный_перитонит',
            'вирусная_лейкемия', 'вирусный_иммунодефицит', 'коронавирусная_инфекция_кошек',
            'бордетеллез_кошек', 'микоплазмоз_кошек', 'хламидиоз_кошек',
            'бартонеллез', 'риккетсиоз_кошек', 'эрлихиоз_кошек', 'анаплазмоз_кошек',
            'бабезиоз_кошек', 'лейшманиоз_кошек', 'токсоплазмоз_кошек',
            'криптоспоридиоз_кошек', 'кокцидиоз_кошек', 'лямблиоз_кошек',
            'трихомоноз_кошек', 'кандидоз_кошек', 'аспергиллез_кошек',
            'гистоплазмоз_кошек', 'бластомикоз_кошек', 'кокцидиоидомикоз_кошек',
            'споротрихоз_кошек', 'дерматофитоз_кошек', 'малассезиоз_кошек',
            'демодекоз_кошек', 'саркоптоз_кошек', 'нотоэдроз_кошек',
            'отодектоз_кошек', 'хейлетиеллез_кошек', 'блошиная_инвазия_кошек',
            'вшивость_кошек', 'клещевая_инвазия_кошек', 'дирофиляриоз_кошек',
            'токсокароз_кошек', 'токсаскаридоз_кошек', 'анкилостомоз_кошек',
            'стронгилоидоз_кошек', 'трихоцефалез_кошек', 'дипилидиоз_кошек',
            'тениоз_кошек', 'эхинококкоз_кошек', 'альвеококкоз_кошек',
            
            # НЕИНФЕКЦИОННЫЕ ЗАБОЛЕВАНИЯ
            'гастроэнтерит', 'панкреатит', 'гепатит', 'цирроз_печени', 'энтерит',
            'колит', 'язва_желудка', 'непроходимость_кишечника', 'заворот_кишок',
            'пневмония', 'бронхит', 'астма', 'плеврит', 'ринит', 'синусит',
            'ларингит', 'трахеит', 'дерматит', 'экзема', 'аллергический_дерматит',
            'себорея', 'лишай', 'пиодермия', 'эпилепсия', 'инсульт', 'менингит',
            'энцефалит', 'полиневрит', 'дископатия', 'вестибулярный_синдром',
            'когнитивная_дисфункция', 'сердечная_недостаточность', 'кардиомиопатия',
            'аритмия', 'гипертония', 'гипотония', 'тромбоэмболия', 'анемия',
            'лейкоз', 'почечная_недостаточность', 'цистит', 'пиелонефрит',
            'мочекаменная_болезнь', 'простатит', 'эндометрит', 'мастит',
            'диабет', 'гипотиреоз', 'гипертиреоз', 'синдром_кушинга',
            'болезнь_аддисона', 'ожирение', 'кахексия', 'конъюнктивит',
            'кератит', 'катаракта', 'глаукома', 'увеит', 'отслоение_сетчатки',
            'слепота', 'отит', 'отит_наружный', 'отит_средний', 'отит_внутренний',
            'глухота', 'стоматит', 'гингивит', 'пародонтит', 'кариес',
            'абсцесс_зуба', 'лимфома', 'саркома', 'карцинома', 'меланома',
            'лейкемия', 'артрит', 'остеоартрит', 'ревматоидный_артрит',
            'остеопороз', 'остеомаляция', 'рахит', 'гиперпаратиреоз',
            'гипопаратиреоз', 'акромегалия', 'гипопитуитаризм', 'несахарный_диабет',
            'синдром_неадекватной_секреции_АДГ', 'феохромоцитома', 'инсулинома',
            'глюкагонома', 'соматостатинома', 'гастринома', 'випома',
            'карциноидный_синдром', 'синдром_Золлингера_Эллисона',
            'синдром_Вернера_Моррисона', 'синдром_Карциноида',
            'синдром_Маллори_Вейсса', 'синдром_Бурхаве', 'синдром_Боаса',
            'синдром_Рейно', 'синдром_Марфана', 'синдром_Элерса_Данлоса',
            'синдром_Дауна', 'синдром_Тернера', 'синдром_Клайнфельтера',
            'синдром_Прадера_Вилли', 'синдром_Ангельмана', 'синдром_Ретта',
            'синдром_Аспергера', 'синдром_Туретта', 'синдром_Жиль_де_ла_Туретта'
        ]
        
        # Виды животных
        animal_types = ['собака', 'кошка', 'хомяк', 'птица', 'кролик', 'черепаха']
        
        # Сохраняем для использования в классе
        self.symptoms = symptoms
        self.diseases = diseases
        
        # Создаем синтетический датасет
        data = []
        
        for _ in range(5000):
            # Выбираем случайное заболевание
            disease = np.random.choice(diseases)
            animal_type = np.random.choice(animal_types)
            
            # Создаем симптомы на основе заболевания
            symptoms_vector = np.zeros(len(symptoms))
            
            # Определяем симптомы для каждого заболевания
            self._assign_symptoms_for_disease(disease, symptoms_vector)
            
            # Добавляем случайные симптомы (шум)
            noise_symptoms = np.random.choice(len(symptoms), 
                                            size=np.random.randint(0, 3), 
                                            replace=False)
            for symptom_idx in noise_symptoms:
                if symptoms_vector[symptom_idx] == 0:
                    symptoms_vector[symptom_idx] = np.random.choice([0, 1], 
                                                                   p=[0.7, 0.3])
            
            # Создаем запись
            record = {
                'animal_type': animal_type,
                'disease': disease
            }
            
            # Добавляем симптомы
            for i, symptom in enumerate(symptoms):
                record[symptom] = symptoms_vector[i]
            
            data.append(record)
        
        return pd.DataFrame(data)
    
    def _assign_symptoms_for_disease(self, disease, symptoms_vector):
        """Присвоение симптомов для конкретного заболевания"""
        
        # ПАРВОВИРУСНЫЙ ЭНТЕРИТ
        if disease == 'парвовирусный_энтерит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_кале')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            
        # ЧУМА ПЛОТОЯДНЫХ
        elif disease == 'чума_плотоядных':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('конъюнктивит')] = 1
            symptoms_vector[self.symptoms.index('судороги')] = 1
            symptoms_vector[self.symptoms.index('паралич')] = 1
            symptoms_vector[self.symptoms.index('атаксия')] = 1
            
        # БЕШЕНСТВО
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
            
        # ЛЕПТОСПИРОЗ
        elif disease == 'лептоспироз':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('желтуха')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('мышечная_слабость')] = 1
            
        # ИНФЕКЦИОННЫЙ ГЕПАТИТ
        elif disease == 'инфекционный_гепатит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('желтуха')] = 1
            symptoms_vector[self.symptoms.index('увеличение_печени')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            
        # КОРОНАВИРУСНАЯ ИНФЕКЦИЯ
        elif disease == 'коронавирусная_инфекция':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('конъюнктивит')] = 1
            
        # ПАНЛЕЙКОПЕНИЯ КОШЕК
        elif disease == 'панлейкопения':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_кале')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            
        # КАЛИЦИВИРОЗ
        elif disease == 'калицивироз':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('чихание')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('конъюнктивит')] = 1
            symptoms_vector[self.symptoms.index('стоматит')] = 1
            
        # РИНОТРАХЕИТ
        elif disease == 'ринотрахеит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('чихание')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_носа')] = 1
            symptoms_vector[self.symptoms.index('конъюнктивит')] = 1
            symptoms_vector[self.symptoms.index('слезотечение')] = 1
            
        # ВИРУСНЫЙ ПЕРИТОНИТ КОШЕК
        elif disease == 'вирусный_перитонит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('асцит')] = 1
            symptoms_vector[self.symptoms.index('желтуха')] = 1
            symptoms_vector[self.symptoms.index('увеличение_печени')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            
        # ГАСТРОЭНТЕРИТ
        elif disease == 'гастроэнтерит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('вздутие_живота')] = 1
            
        # ПНЕВМОНИЯ
        elif disease == 'пневмония':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('учащенное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('хрипы')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            
        # ДЕРМАТИТ
        elif disease == 'дерматит':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            
        # ЭПИЛЕПСИЯ
        elif disease == 'эпилепсия':
            symptoms_vector[self.symptoms.index('судороги')] = 1
            symptoms_vector[self.symptoms.index('потеря_сознания')] = 1
            symptoms_vector[self.symptoms.index('атаксия')] = 1
            symptoms_vector[self.symptoms.index('тремор')] = 1
            
        # СЕРДЕЧНАЯ НЕДОСТАТОЧНОСТЬ
        elif disease == 'сердечная_недостаточность':
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('учащенное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('отеки')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('цианоз')] = 1
            
        # ДИАБЕТ
        elif disease == 'диабет':
            symptoms_vector[self.symptoms.index('полифагия')] = 1
            symptoms_vector[self.symptoms.index('полиурия')] = 1
            symptoms_vector[self.symptoms.index('полидипсия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            
        # ПОЧЕЧНАЯ НЕДОСТАТОЧНОСТЬ
        elif disease == 'почечная_недостаточность':
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('полиурия')] = 1
            symptoms_vector[self.symptoms.index('полидипсия')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            
        # КОНЪЮНКТИВИТ
        elif disease == 'конъюнктивит':
            symptoms_vector[self.symptoms.index('выделения_из_глаз')] = 1
            symptoms_vector[self.symptoms.index('покраснение_глаз')] = 1
            symptoms_vector[self.symptoms.index('слезотечение')] = 1
            symptoms_vector[self.symptoms.index('зуд')] = 1
            
        # ОТИТ
        elif disease == 'отит':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('выделения_из_ушей')] = 1
            symptoms_vector[self.symptoms.index('боль_в_ушах')] = 1
            symptoms_vector[self.symptoms.index('покраснение_ушей')] = 1
            
        # СТОМАТИТ
        elif disease == 'стоматит':
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('слюнотечение')] = 1
            symptoms_vector[self.symptoms.index('неприятный_запах_изо_рта')] = 1
            symptoms_vector[self.symptoms.index('кровоточивость_десен')] = 1
            
        # АНЕМИЯ
        elif disease == 'анемия':
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('холодные_конечности')] = 1
            
        # ГИПОТИРЕОЗ
        elif disease == 'гипотиреоз':
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('увеличение_веса')] = 1
            symptoms_vector[self.symptoms.index('отеки')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            
        # ГИПЕРТИРЕОЗ
        elif disease == 'гипертиреоз':
            symptoms_vector[self.symptoms.index('полифагия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('беспокойство')] = 1
            symptoms_vector[self.symptoms.index('учащенное_сердцебиение')] = 1
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            
        # ЦИСТИТ
        elif disease == 'цистит':
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('частое_мочеиспускание')] = 1
            symptoms_vector[self.symptoms.index('болезненное_мочеиспускание')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_моче')] = 1
            symptoms_vector[self.symptoms.index('недержание_мочи')] = 1
            
        # МОЧЕКАМЕННАЯ БОЛЕЗНЬ
        elif disease == 'мочекаменная_болезнь':
            symptoms_vector[self.symptoms.index('частое_мочеиспускание')] = 1
            symptoms_vector[self.symptoms.index('болезненное_мочеиспускание')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_моче')] = 1
            symptoms_vector[self.symptoms.index('недержание_мочи')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            
        # АРТРИТ
        elif disease == 'артрит':
            symptoms_vector[self.symptoms.index('хромота')] = 1
            symptoms_vector[self.symptoms.index('скованность_движений')] = 1
            symptoms_vector[self.symptoms.index('боль_в_суставах')] = 1
            symptoms_vector[self.symptoms.index('нежелание_двигаться')] = 1
            symptoms_vector[self.symptoms.index('отеки')] = 1
            
        # ОЖИРЕНИЕ
        elif disease == 'ожирение':
            symptoms_vector[self.symptoms.index('увеличение_веса')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('нежелание_двигаться')] = 1
            
        # КАХЕКСИЯ
        elif disease == 'кахексия':
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('слабость')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            
        # ЛИМФОМА
        elif disease == 'лимфома':
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('увеличение_лимфоузлов')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            
        # САРКОМА
        elif disease == 'саркома':
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('увеличение_живота')] = 1
            
        # КАРЦИНОМА
        elif disease == 'карцинома':
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('увеличение_живота')] = 1
            
        # МЕЛАНОМА
        elif disease == 'меланома':
            symptoms_vector[self.symptoms.index('пятна_на_коже')] = 1
            symptoms_vector[self.symptoms.index('изменение_цвета_кожи')] = 1
            symptoms_vector[self.symptoms.index('язвы_на_коже')] = 1
            symptoms_vector[self.symptoms.index('кровоточивость')] = 1
            
        # ЛЕЙКЕМИЯ
        elif disease == 'лейкемия':
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            symptoms_vector[self.symptoms.index('увеличение_лимфоузлов')] = 1
            
        # По умолчанию - случайные симптомы
        else:
            # Для неизвестных заболеваний добавляем случайные симптомы
            random_symptoms = np.random.choice(len(self.symptoms), 
                                             size=np.random.randint(3, 8), 
                                             replace=False)
            for symptom_idx in random_symptoms:
                symptoms_vector[symptom_idx] = 1
    
    def train_models(self, df):
        """
        Обучение и сравнение различных моделей машинного обучения
        """
        # Подготовка данных
        X = df.drop(['animal_type', 'disease'], axis=1)
        y = df['disease']
        
        # Сохраняем названия признаков
        self.feature_names = X.columns.tolist()
        
        # Инициализируем label_encoder для заболеваний
        self.label_encoder.fit(y)
        
        # Разделение на обучающую и тестовую выборки
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Масштабирование признаков
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Определение моделей для сравнения (оставляем только быстрые)
        models = {
            'Random Forest': RandomForestClassifier(n_estimators=50, random_state=42),
            'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
            'SVM': SVC(random_state=42, probability=True)
        }
        
        results = {}
        
        # Обучение и оценка каждой модели
        for name, model in models.items():
            print(f"Обучение {name}...")
            
            # Обучение модели
            model.fit(X_train_scaled, y_train)
            
            # Предсказание на тестовой выборке
            y_pred = model.predict(X_test_scaled)
            
            # Оценка точности
            accuracy = accuracy_score(y_test, y_pred)
            
            # Кросс-валидация
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
            
            print(f"{name}:")
            print(f"  Точность: {accuracy:.3f}")
            print(f"  CV среднее: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
            print()
        
        # Выбор лучшей модели
        best_model_name = max(results.keys(), key=lambda x: results[x]['cv_mean'])
        best_model = results[best_model_name]['model']
        
        print(f"Лучшая модель: {best_model_name}")
        print(f"Точность: {results[best_model_name]['accuracy']:.3f}")
        
        # Сохранение лучшей модели
        self.model = best_model
        self.feature_names = X.columns.tolist()
        
        return results
    
    def save_model(self, filename='animal_disease_model.pkl'):
        """
        Сохранение обученной модели и связанных данных
        """
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'symptoms': self.symptoms,
            'diseases': self.diseases,
            'feature_names': self.feature_names
        }
        
        joblib.dump(model_data, filename)
        print(f"Модель сохранена в файл: {filename}")
    
    def load_model(self, filename='animal_disease_model.pkl'):
        """
        Загрузка обученной модели
        """
        try:
            model_data = joblib.load(filename)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.symptoms = model_data['symptoms']
            self.diseases = model_data['diseases']
            self.feature_names = model_data['feature_names']
            print(f"Модель загружена из файла: {filename}")
            return True
        except FileNotFoundError:
            print(f"Файл {filename} не найден")
            return False
    
    def predict(self, animal_type, symptoms):
        """
        Предсказание заболевания на основе симптомов
        """
        if self.model is None:
            print("Модель не обучена или не загружена")
            return None
        
        # Создание вектора симптомов на основе feature_names
        symptom_vector = np.zeros(len(self.feature_names))
        
        for symptom in symptoms:
            if symptom in self.feature_names:
                symptom_vector[self.feature_names.index(symptom)] = 1
        
        # Масштабирование
        symptom_vector_scaled = self.scaler.transform([symptom_vector])
        
        # Предсказание
        probabilities = self.model.predict_proba(symptom_vector_scaled)[0]
        
        # Получение топ-5 предсказаний
        top_indices = np.argsort(probabilities)[::-1][:5]
        
        predictions = []
        for idx in top_indices:
            disease = self.label_encoder.inverse_transform([idx])[0]
            probability = probabilities[idx]
            predictions.append([disease, probability])
        
        return predictions

def main():
    """
    Основная функция для обучения модели
    """
    print("=" * 60)
    print("ОБУЧЕНИЕ МОДЕЛИ ДИАГНОСТИКИ ЗАБОЛЕВАНИЙ ЖИВОТНЫХ")
    print("=" * 60)
    
    # Создание классификатора
    classifier = AnimalDiseaseClassifier()
    
    # Создание датасета
    print("1. Создание датасета...")
    df = classifier.create_dataset()
    print(f"   OK Создан датасет с {len(df)} записями")
    print(f"   OK Количество симптомов: {len(classifier.symptoms)}")
    print(f"   OK Количество заболеваний: {len(classifier.diseases)}")
    print()
    
    # Обучение моделей
    print("2. Обучение и сравнение моделей...")
    results = classifier.train_models(df)
    
    # Сохранение модели
    print("3. Сохранение модели...")
    classifier.save_model()
    
    # Тестирование модели
    print("4. Тестирование модели:")
    print("-" * 40)
    
    # Тест 1: Парвовирусный энтерит
    test_symptoms = ['лихорадка', 'рвота', 'диарея', 'анорексия']
    predictions = classifier.predict('собака', test_symptoms)
    print("Тест 1: Парвовирусный энтерит")
    print(f"Симптомы: {', '.join(test_symptoms)}")
    print("Предсказания:")
    for i, (disease, prob) in enumerate(predictions):
        print(f"  {i+1}. {disease}: {prob:.3f}")
    print()
    
    # Тест 2: Бешенство
    test_symptoms = ['изменение_поведения', 'агрессия', 'водобоязнь']
    predictions = classifier.predict('собака', test_symptoms)
    print("Тест 2: Бешенство")
    print(f"Симптомы: {', '.join(test_symptoms)}")
    print("Предсказания:")
    for i, (disease, prob) in enumerate(predictions):
        print(f"  {i+1}. {disease}: {prob:.3f}")
    print()
    
    # Тест 3: Дерматит
    test_symptoms = ['зуд', 'выпадение_шерсти']
    predictions = classifier.predict('кошка', test_symptoms)
    print("Тест 3: Дерматит")
    print(f"Симптомы: {', '.join(test_symptoms)}")
    print("Предсказания:")
    for i, (disease, prob) in enumerate(predictions):
        print(f"  {i+1}. {disease}: {prob:.3f}")
    print()
    
    print("=" * 60)
    print("ОБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    print("=" * 60)
    print("Модель сохранена в файл: animal_disease_model.pkl")
    print("Теперь можно использовать диагностику на сайте!")

if __name__ == "__main__":
    main()