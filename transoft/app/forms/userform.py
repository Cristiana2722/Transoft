from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password_check = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Create user')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class AccountForm(FlaskForm):
    username = StringField('Username', render_kw={'readonly': True})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password_check = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Delete')


class EditAccountForm(FlaskForm):
    username = StringField('Username', render_kw={'readonly': True})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password_check = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Save')


class ChangePasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    password_check = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Save')


class AdminEditAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password_check = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Save')


