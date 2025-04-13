from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, NumberRange, ValidationError

def validate_vaccine_types(form, field):
    if form.category.data == 'vaccines':
        if not any([form.rabies_vaccine.data, form.viral_vaccine.data, form.fungal_vaccine.data]):
            raise ValidationError('Выберите хотя бы один тип вакцины')


class TreatmentCalculatorForm(FlaskForm):
    treatment_search = StringField('Поиск назначения', validators=[DataRequired()])
    quantity = FloatField('Количество', validators=[DataRequired(), NumberRange(min=0.1)])
    add_another = SubmitField('Добавить ещё')
    save_to_pet = SubmitField('Сохранить в карточку')

class TreatmentForm(FlaskForm):
    name = StringField('Название назначения', validators=[DataRequired()])
    category = SelectField('Категория', choices=[
        ('medication', 'Лекарство'),
        ('anesthesia', 'Наркоз'),
        ('suture_materials', 'Шовный'),
        ('gels_sprays', 'Гели / Спреи'),
        ('external_solutions', 'Наружные растворы'),
        ('suppositories', 'Свечи'),
        ('eye_ear_drops', 'Глазные / ушные мази и капли'),
        ('consumables', 'Вспомогательные материалы'),
        ('castration_sterilization', 'Кастрация, стерилизация'),
        ('lab_tests', 'Лабораторные исследования'),
        ('blood_chemistry', 'Биохимический анализ крови'),
        ('vaccines', 'Вакцины'),
        ('general_services', 'Общие услуги'),
        ('surgery', 'Хирургия'),
        ('dentistry', 'Стоматология'),
        ('dermatology', 'Дерматология'),
        ('ent', 'Отоларингология'),
        ('ophthalmology', 'Офтальмология'),
        ('urology', 'Урология'),
        ('gynecology', 'Гинекология')
    ], validators=[DataRequired()])
    dosage = StringField('Стандартная дозировка')
    unit = StringField('Единица измерения', validators=[DataRequired()])
    price = FloatField('Цена за единицу', validators=[DataRequired(), NumberRange(min=0)])
    rabies_vaccine = BooleanField('Бешенство')
    viral_vaccine = BooleanField('Вирусные')
    fungal_vaccine = BooleanField('Грибковые')
    description = TextAreaField('Описание')
    submit = SubmitField('Добавить назначение', validators=[validate_vaccine_types])