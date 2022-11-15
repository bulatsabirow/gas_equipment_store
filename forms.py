from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, \
    SelectField, FileField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Email


from ORM import CATEGORY_CHOICES, BRAND_CHOICES


class AuthForm(FlaskForm):
    email = StringField('Адрес электронной почты ', validators=[Email(message='Адрес электронной почты недействителен')])
    password = PasswordField('Пароль ', validators=[DataRequired()])
    submit = SubmitField(label='Войти', render_kw={'class': 'btn btn-primary'})


class RegisterForm(AuthForm):
    name = StringField("Имя ", validators=[DataRequired(message='Введите, пожалуйста, имя')])
    submit = SubmitField(label='Зарегистрироваться', render_kw={'class': 'btn btn-primary'})


class EditProfileForm(RegisterForm):
    password = PasswordField('Пароль ')
    submit = SubmitField(label='Изменить', render_kw={'class': 'btn btn-primary'})


class ProductForm(FlaskForm):
    title = StringField("Название товара", validators=[DataRequired()])
    description = TextAreaField('Описание товара', validators=[DataRequired()])
    price = DecimalField('Цена', render_kw={'min': 1,  'step': '0.01'}, validators=[DataRequired()])
    category = SelectField('Категория', choices=[item for item in CATEGORY_CHOICES])
    brand = SelectField('Бренд', choices=[item for item in BRAND_CHOICES])
    image = FileField('Фотография', name='file')
    count = IntegerField('Количество', render_kw={'min': 1}, validators=[DataRequired()])


class AddProductForm(ProductForm):
    submit = SubmitField(label='Добавить товар', render_kw={'class': 'btn btn-success'})


class EditProductForm(ProductForm):
    submit = SubmitField(label='Изменить товар', render_kw={'class': 'btn btn-warning'})

