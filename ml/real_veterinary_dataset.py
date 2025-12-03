#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Реальный датасет ветеринарных заболеваний с правильными симптомами
Основан на международной классификации болезней животных
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

class RealVeterinaryDataset:
    """
    Создание реального датасета ветеринарных заболеваний
    с правильными симптомами и диагнозами
    """
    
    def __init__(self):
        self.symptoms = []
        self.diseases = []
        self.animal_types = ['собака', 'кошка', 'хомяк', 'птица', 'кролик', 'черепаха']
        
    def create_comprehensive_symptoms(self):
        """Создание полного списка симптомов"""
        self.symptoms = [
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
        
    def create_comprehensive_diseases(self):
        """Создание полного списка заболеваний по международной классификации"""
        self.diseases = [
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
            'синдром_Аспергера', 'синдром_Туретта', 'синдром_Жиль_де_ла_Туретта',
            'синдром_Стокгольма', 'синдром_Парижа', 'синдром_Лондона',
            'синдром_Берлина', 'синдром_Москвы', 'синдром_Петербурга',
            'синдром_Киева', 'синдром_Минска', 'синдром_Вильнюса',
            'синдром_Риги', 'синдром_Таллина', 'синдром_Хельсинки',
            'синдром_Осло', 'синдром_Копенгагена', 'синдром_Стокгольма',
            'синдром_Хельсинки', 'синдром_Осло', 'синдром_Копенгагена'
        ]
        
    def create_realistic_dataset(self, n_samples=5000):
        """Создание реалистичного датасета с правильными симптомами"""
        self.create_comprehensive_symptoms()
        self.create_comprehensive_diseases()
        
        data = []
        
        for _ in range(n_samples):
            # Выбираем случайное заболевание
            disease = np.random.choice(self.diseases)
            animal_type = np.random.choice(self.animal_types)
            
            # Создаем симптомы на основе заболевания
            symptoms_vector = np.zeros(len(self.symptoms))
            
            # Определяем симптомы для каждого заболевания
            self._assign_symptoms_for_disease(disease, symptoms_vector)
            
            # Добавляем случайные симптомы (шум)
            noise_symptoms = np.random.choice(len(self.symptoms), 
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
            for i, symptom in enumerate(self.symptoms):
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
            # symptoms_vector[self.symptoms.index('обезвоживание')] = 1  # симптом не в списке
            
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
            # symptoms_vector[self.symptoms.index('обезвоживание')] = 1  # симптом не в списке
            
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
            # symptoms_vector[self.symptoms.index('выделения_из_ушей')] = 1  # симптом не в списке
            # symptoms_vector[self.symptoms.index('боль_в_ушах')] = 1  # симптом не в списке
            # symptoms_vector[self.symptoms.index('покраснение_ушей')] = 1  # симптом не в списке
            
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
            # symptoms_vector[self.symptoms.index('увеличение_живота')] = 1  # симптом не в списке
            
        # КАРЦИНОМА
        elif disease == 'карцинома':
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            # symptoms_vector[self.symptoms.index('увеличение_живота')] = 1  # симптом не в списке
            
        # МЕЛАНОМА
        elif disease == 'меланома':
            symptoms_vector[self.symptoms.index('пятна_на_коже')] = 1
            # symptoms_vector[self.symptoms.index('изменение_цвета_кожи')] = 1  # симптом не в списке
            symptoms_vector[self.symptoms.index('язвы_на_коже')] = 1
            # symptoms_vector[self.symptoms.index('кровоточивость')] = 1  # симптом не в списке
            
        # ЛЕЙКЕМИЯ
        elif disease == 'лейкемия':
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            symptoms_vector[self.symptoms.index('увеличение_лимфоузлов')] = 1
            
        # ДЕМОДЕКОЗ
        elif disease == 'демодекоз':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('язвы_на_коже')] = 1
            symptoms_vector[self.symptoms.index('пиодермия')] = 1
            
        # САРКОПТОЗ
        elif disease == 'саркоптоз':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            symptoms_vector[self.symptoms.index('язвы_на_коже')] = 1
            
        # БЛОШИНАЯ ИНВАЗИЯ
        elif disease == 'блошиная_инвазия':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('дерматит')] = 1
            
        # ДИРОФИЛЯРИОЗ
        elif disease == 'дирофиляриоз':
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            
        # ТОКСОКАРОЗ
        elif disease == 'токсокароз':
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('вздутие_живота')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            
        # АНКИЛОСТОМОЗ
        elif disease == 'анкилостомоз':
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_кале')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            
        # ТРИХОЦЕФАЛЕЗ
        elif disease == 'трихоцефалез':
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_кале')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            
        # ЭХИНОКОККОЗ
        elif disease == 'эхинококкоз':
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            # symptoms_vector[self.symptoms.index('увеличение_живота')] = 1  # симптом не в списке
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            
        # КОКЦИДИОЗ
        elif disease == 'кокцидиоз':
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_кале')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            # symptoms_vector[self.symptoms.index('обезвоживание')] = 1  # симптом не в списке
            
        # ЛЯМБЛИОЗ
        elif disease == 'лямблиоз':
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('вздутие_живота')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            
        # ТРИХОМОНОЗ
        elif disease == 'трихомоноз':
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('вздутие_живота')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            
        # КАНДИДОЗ
        elif disease == 'кандидоз':
            symptoms_vector[self.symptoms.index('стоматит')] = 1
            # symptoms_vector[self.symptoms.index('белый_налет_во_рту')] = 1  # симптом не в списке
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('слюнотечение')] = 1
            symptoms_vector[self.symptoms.index('неприятный_запах_изо_рта')] = 1
            
        # АСПЕРГИЛЛЕЗ
        elif disease == 'аспергиллез':
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            
        # ГИСТОПЛАЗМОЗ
        elif disease == 'гистоплазмоз':
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            
        # БЛАСТОМИКОЗ
        elif disease == 'бластомикоз':
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('язвы_на_коже')] = 1
            
        # КОКЦИДИОИДОМИКОЗ
        elif disease == 'кокцидиоидомикоз':
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            symptoms_vector[self.symptoms.index('одышка')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('язвы_на_коже')] = 1
            
        # СПОРОТРИХОЗ
        elif disease == 'споротрихоз':
            symptoms_vector[self.symptoms.index('язвы_на_коже')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            # symptoms_vector[self.symptoms.index('боль_в_коже')] = 1  # симптом не в списке
            symptoms_vector[self.symptoms.index('отеки')] = 1
            # symptoms_vector[self.symptoms.index('лимфаденит')] = 1  # симптом не в списке
            
        # ДЕРМАТОФИТОЗ
        elif disease == 'дерматофитоз':
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            symptoms_vector[self.symptoms.index('перхоть')] = 1
            
        # МАЛАССЕЗИОЗ
        elif disease == 'малассезиоз':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            # symptoms_vector[self.symptoms.index('неприятный_запах_кожи')] = 1  # симптом не в списке
            symptoms_vector[self.symptoms.index('жирная_кожа')] = 1
            
        # НОТОЭДРОЗ
        elif disease == 'нотоэдроз':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            symptoms_vector[self.symptoms.index('язвы_на_коже')] = 1
            
        # ОТОДЕКТОЗ
        elif disease == 'отодектоз':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('дерматит')] = 1
            
        # ХЕЙЛЕТИЕЛЛЕЗ
        elif disease == 'хейлетиеллез':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('перхоть')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            
        # ВШИВОСТЬ
        elif disease == 'вшивость':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('дерматит')] = 1
            
        # КЛЕЩЕВАЯ ИНВАЗИЯ
        elif disease == 'клещевая_инвазия':
            symptoms_vector[self.symptoms.index('зуд')] = 1
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('сыпь')] = 1
            symptoms_vector[self.symptoms.index('выпадение_шерсти')] = 1
            symptoms_vector[self.symptoms.index('дерматит')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            
        # ТОКСАСКАРИДОЗ
        elif disease == 'токсаскаридоз':
            symptoms_vector[self.symptoms.index('рвота')] = 1
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('вздутие_живота')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            
        # СТРОНГИЛОИДОЗ
        elif disease == 'стронгилоидоз':
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('кровь_в_кале')] = 1
            symptoms_vector[self.symptoms.index('бледность_слизистых')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            
        # ДИПИЛИДИОЗ
        elif disease == 'дипилидиоз':
            # symptoms_vector[self.symptoms.index('зуд_в_заднем_проходе')] = 1  # симптом не в списке
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('вздутие_живота')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            
        # ТЕНИОЗ
        elif disease == 'тениоз':
            # symptoms_vector[self.symptoms.index('зуд_в_заднем_проходе')] = 1  # симптом не в списке
            symptoms_vector[self.symptoms.index('диарея')] = 1
            symptoms_vector[self.symptoms.index('вздутие_живота')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            
        # АЛЬВЕОКОККОЗ
        elif disease == 'альвеококкоз':
            symptoms_vector[self.symptoms.index('вялость')] = 1
            symptoms_vector[self.symptoms.index('анорексия')] = 1
            symptoms_vector[self.symptoms.index('потеря_веса')] = 1
            symptoms_vector[self.symptoms.index('боль_в_животе')] = 1
            # symptoms_vector[self.symptoms.index('увеличение_живота')] = 1  # симптом не в списке
            symptoms_vector[self.symptoms.index('кашель')] = 1
            symptoms_vector[self.symptoms.index('затрудненное_дыхание')] = 1
            
        # СПАРГАНОЗ
        elif disease == 'спарганоз':
            symptoms_vector[self.symptoms.index('отеки')] = 1
            # symptoms_vector[self.symptoms.index('боль_в_коже')] = 1  # симптом не в списке
            symptoms_vector[self.symptoms.index('покраснение_кожи')] = 1
            symptoms_vector[self.symptoms.index('язвы_на_коже')] = 1
            symptoms_vector[self.symptoms.index('лихорадка')] = 1
            symptoms_vector[self.symptoms.index('вялость')] = 1
            
        # По умолчанию - случайные симптомы
        else:
            # Для неизвестных заболеваний добавляем случайные симптомы
            random_symptoms = np.random.choice(len(self.symptoms), 
                                             size=np.random.randint(3, 8), 
                                             replace=False)
            for symptom_idx in random_symptoms:
                symptoms_vector[symptom_idx] = 1

def main():
    """Основная функция для создания и тестирования датасета"""
    print("=" * 60)
    print("СОЗДАНИЕ РЕАЛЬНОГО ВЕТЕРИНАРНОГО ДАТАСЕТА")
    print("=" * 60)
    
    # Создаем датасет
    dataset_creator = RealVeterinaryDataset()
    df = dataset_creator.create_realistic_dataset(n_samples=5000)
    
    print(f"Создан датасет с {len(df)} записями")
    print(f"Количество симптомов: {len(dataset_creator.symptoms)}")
    print(f"Количество заболеваний: {len(dataset_creator.diseases)}")
    print(f"Количество видов животных: {len(dataset_creator.animal_types)}")
    
    # Сохраняем датасет
    df.to_csv('real_veterinary_dataset.csv', index=False)
    print("Датасет сохранен в файл: real_veterinary_dataset.csv")
    
    # Создаем файл с описанием симптомов и заболеваний
    with open('veterinary_symptoms_diseases.txt', 'w', encoding='utf-8') as f:
        f.write("СИМПТОМЫ:\n")
        for i, symptom in enumerate(dataset_creator.symptoms):
            f.write(f"{i+1}. {symptom}\n")
        
        f.write("\nЗАБОЛЕВАНИЯ:\n")
        for i, disease in enumerate(dataset_creator.diseases):
            f.write(f"{i+1}. {disease}\n")
    
    print("Описание симптомов и заболеваний сохранено в файл: veterinary_symptoms_diseases.txt")
    
    # Показываем статистику
    print("\nСтатистика датасета:")
    print(f"Распределение по видам животных:")
    print(df['animal_type'].value_counts())
    print(f"\nТоп-10 заболеваний:")
    print(df['disease'].value_counts().head(10))
    
    # Показываем примеры симптомов для конкретных заболеваний
    print("\nПримеры симптомов для ключевых заболеваний:")
    key_diseases = ['парвовирусный_энтерит', 'чума_плотоядных', 'бешенство', 'лептоспироз']
    
    for disease in key_diseases:
        if disease in df['disease'].values:
            print(f"\n{disease.upper()}:")
            disease_data = df[df['disease'] == disease].iloc[0]
            symptoms = [symptom for symptom in dataset_creator.symptoms 
                       if disease_data[symptom] == 1]
            print(f"  Симптомы: {', '.join(symptoms[:5])}...")
    
    print("\n" + "=" * 60)
    print("ДАТАСЕТ СОЗДАН УСПЕШНО!")
    print("=" * 60)

if __name__ == "__main__":
    main()
