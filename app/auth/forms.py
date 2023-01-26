import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.auth.models import User


class LoginForm(FlaskForm):
    next = HiddenField()
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Length(1, 64),
            Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(1, 100),
            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                   'Usernames must have only letters, numbers, dots or '
                   'underscores')])
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Length(1, 64),
            Email()
        ])
    info = StringField(
        'Info',
        validators=[
            DataRequired(),
            Length(1, 100)
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            EqualTo('password_repeat', message='Passwords must match.')
        ])
    password_repeat = PasswordField(
        'Confirm password',
        validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.select().where(User.email == field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.select().where(User.name == field.data).first():
            raise ValidationError('Username already in use.')

    def validate_password(self, field):
        length_error = len(field.data) < 8
        digit_error = re.search(r"\d", field.data) is None
        uppercase_error = re.search(r"[A-Z]", field.data) is None
        lowercase_error = re.search(r"[a-z]", field.data) is None
        symbol_error = re.search(r"[ !#$%&'()*+,-./[\\\]^_`{|}~" + r'"]', field.data) is None

        password_error = any([length_error, digit_error, uppercase_error, lowercase_error, symbol_error])

        if password_error:
            raise ValidationError('Password must be at least 8 chars include Upper, Lower, Digit, Punctuation')
