from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, \
    SelectField, FileField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Email


from ORM import CATEGORY_CHOICES, BRAND_CHOICES


class AuthForm(FlaskForm):
    email = StringField('Адрес электронной почты ', validators=[Email(message='Адрес электронной почты недействителен')],
                        render_kw={'class': ''})
    password = PasswordField('Пароль ', validators=[DataRequired()])
    submit = SubmitField(label='Войти', render_kw={'class': 'btn btn-primary'})


class RegisterForm(AuthForm):
    name = StringField("Имя ", validators=[DataRequired()])
    submit = SubmitField(label='Зарегистрироваться')


class ProductForm(FlaskForm):
    title = StringField("Название товара", validators=[DataRequired()])
    description = TextAreaField('Описание товара', validators=[DataRequired()])
    price = DecimalField('Цена', validators=[DataRequired()])
    category = SelectField('Категория', choices=[item for item in CATEGORY_CHOICES])
    brand = SelectField('Бренд', choices=[item for item in BRAND_CHOICES])
    image = FileField('Фотография', name='file')
    count = IntegerField('Количество', render_kw={'min': 1})


class AddProductForm(ProductForm):
    submit = SubmitField(label='Добавить товар')


class EditProductForm(ProductForm):
    submit = SubmitField(label='Изменить товар')

