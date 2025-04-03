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
        ('Лекарство', 'Лекарство'),
        ('Наркоз', 'Наркоз'),
        ('Шовный', 'Шовный'),
        ('Гели / Спреи', 'Гели / Спреи'),
        ('Наружные растворы', 'Наружные растворы'),
        ('Свечи', 'Свечи'),
        ('Глазные / ушные мази и капли', 'Глазные / ушные мази и капли'),
        ('Вспомогательные материалы', 'Вспомогательные материалы'),
        ('Кастрация, стерилизация', 'Кастрация, стерилизация'),
        ('Лабораторные исследования', 'Лабораторные исследования'),
        ('Биохимический анализ крови', 'Биохимический анализ крови'),
        ('Вакцины', 'Вакцины'),
        ('Общие услуги', 'Общие услуги'),
        ('Хирургия', 'Хирургия'),
        ('Стоматология', 'Стоматология'),
        ('Дерматология', 'Дерматология'),
        ('Отоларингология', 'Отоларингология'),
        ('Офтальмология', 'Офтальмология'),
        ('Урология', 'Урология'),
        ('Гинекология', 'Гинекология')

    ], validators=[DataRequired()])
    dosage = StringField('Стандартная дозировка')
    unit = StringField('Единица измерения', validators=[DataRequired()])
    price = FloatField('Цена за единицу', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Описание')
    submit = SubmitField('Добавить назначение')
    