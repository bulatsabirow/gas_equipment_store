from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email


class AuthForm(FlaskForm):
    email = StringField('Адрес электронной почты ', validators=[Email()])
    password = PasswordField('Пароль ', validators=[DataRequired()])
    submit = SubmitField(label='Войти')


class RegisterForm(AuthForm):
    name = StringField("Имя ", validators=[DataRequired()])
    submit = SubmitField(label='Зарегистрироваться')
