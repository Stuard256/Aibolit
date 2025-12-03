# Документация проекта Aibolit - Ветеринарная клиника

## Обзор проекта
Aibolit - это веб-приложение для управления ветеринарной клиникой с системой машинного обучения для диагностики заболеваний животных.

## Основные компоненты

### 1. Основные файлы приложения
- **app.py** - Главный файл Flask приложения, содержит все маршруты, логику работы с базой данных, систему диагностики заболеваний
- **models.py** - Модели базы данных SQLAlchemy (Owner, Pet, Appointment, Treatment, Vaccination, Note)
- **forms.py** - Формы Flask-WTF для обработки пользовательского ввода
- **requirements.txt** - Зависимости Python для проекта

### 2. Статические файлы и шаблоны
- **static/css/styles.css** - CSS стили для веб-интерфейса
- **templates/** - HTML шаблоны Jinja2 для всех страниц приложения:
  - base.html - базовый шаблон
  - index.html - главная страница
  - diagnosis_extended.html - расширенная диагностика с ML
  - owners.html, pets.html - управление владельцами и питомцами
  - appointments.html, treatments.html - записи и лечение
  - vaccinations.html - вакцинации
  - statistics.html - статистика клиники

### 3. База данных
- **instance/vet_clinic.db** - SQLite база данных с данными клиники
- **database_backups/** - автоматические резервные копии БД

### 4. Система машинного обучения (ml/)

#### Активные файлы:
- **ml/datasets/dog_disease_dataset.py** - Генератор датасета заболеваний собак с симптомами и лабораторными анализами
- **ml/datasets/cat_disease_dataset.py** - Генератор датасета заболеваний кошек с симптомами и лабораторными анализами
- **ml/models/weighted_animal_disease_model.pkl** - Обученная ML модель для диагностики (используется в app.py)
- **ml/docs/** - Документация по ML системе

#### Удаленные файлы (не использовались):
- Все старые генераторы датасетов (advanced_veterinary_dataset.py, comprehensive_veterinary_dataset.py, real_veterinary_dataset.py, weighted_veterinary_dataset.py)
- Все старые модели (animal_disease_model.pkl, focused_dog_disease_model.pkl, improved_animal_disease_model.pkl)
- Вся директория ml/scripts/ с тестовыми и обучающими скриптами
- Неиспользуемые CSV и TXT файлы

### 5. Утилиты и скрипты
- **csv_importer.py** - Импорт данных из CSV файлов
- **phone_normalizer.py** - Нормализация телефонных номеров
- **aibolit.bat** - Запуск приложения
- **setup.bat** - Настройка окружения
- **reset_db.bat** - Сброс базы данных
- **load_cards_in_db.bat** - Загрузка карточек в БД
- **load_vaccines_in_db.bat** - Загрузка вакцин в БД

## Архитектура системы

### База данных
- SQLite с таблицами: owners, pets, appointments, treatments, vaccinations, notes
- Автоматическое резервное копирование каждые 2 часа
- Связи между таблицами через внешние ключи

### Система диагностики
- ML модель на основе Random Forest
- Поддержка симптомов и лабораторных анализов
- Раздельные модели для собак и кошек (в разработке)
- API endpoint /diagnose для получения диагнозов

### Веб-интерфейс
- Flask приложение с Bootstrap стилями
- Адаптивный дизайн
- Формы с валидацией
- Экспорт в PDF и Word

## Запуск проекта
1. Установить зависимости: `pip install -r requirements.txt`
2. Запустить приложение: `python app.py` или `aibolit.bat`
3. Открыть браузер: http://localhost:5000

## Текущее состояние ML системы
- Используется взвешенная модель weighted_animal_disease_model.pkl
- Поддерживает диагностику по симптомам и лабораторным анализам
- В разработке: отдельные модели для собак и кошек
- Планируется: увеличение точности и добавление новых заболеваний
