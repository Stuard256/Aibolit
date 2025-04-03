from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange

class TreatmentCalculatorForm(FlaskForm):
    treatment_search = StringField('Поиск назначения', validators=[DataRequired()])
    quantity = FloatField('Количество', validators=[DataRequired(), NumberRange(min=0.1)])
    add_another = SubmitField('Добавить ещё')
    save_to_pet = SubmitField('Сохранить в карточку')

class TreatmentForm(FlaskForm):
    name = StringField('Название назначения', validators=[DataRequired()])
    category = SelectField('Категория', choices=[
        ('medicine', 'Лекарство'),
        ('anesthesia', 'Наркоз'),
        ('surgical_supplies', 'Шовный'),
        ('gels_sprays', 'Гели / Спреи'),
        ('topical_solutions', 'Наружные растворы'),
        ('suppositories', 'Свечи'),
        ('eye_ear_ointments_drops', 'Глазные / ушные мази и капли'),
        ('medical_supplies', 'Вспомогательные материалы'),
        ('sterilization', 'Кастрация, стерилизация'),
        ('lab_tests', 'Лабораторные исследования'),
        ('blood_chemistry', 'Биохимический анализ крови'),
        ('vaccines', 'Вакцины'),
        ('general_services', 'Общие услуги'),
        ('surgery', 'Хирургия'),
        ('dentistry', 'Стоматология'),
        ('dermatology', 'Дерматология'),
        ('otolaryngology', 'Отоларингология'),
        ('ophthalmology', 'Офтальмология'),
        ('urology', 'Урология'),
        ('gynecology', 'Гинекология')

    ], validators=[DataRequired()])
    dosage = StringField('Стандартная дозировка')
    unit = StringField('Единица измерения', validators=[DataRequired()])
    price = FloatField('Цена за единицу', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Описание')
    submit = SubmitField('Добавить назначение')
    