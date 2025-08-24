from flask_wtf import FlaskForm
from wtforms import SubmitField, DecimalField, StringField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, InputRequired


class FuelForm(FlaskForm):
    plate_number = StringField('Număr înmatriculare', validators=[DataRequired(), Length(max=10)])
    fuel_date = DateField('Dată alimentare', validators=[DataRequired()])
    km = IntegerField('Kilometri', validators=[DataRequired()])
    diesel = DecimalField('Litri Diesel', validators=[InputRequired()])
    adblue = DecimalField('Litri AdBlue', validators=[InputRequired()])
    submit = SubmitField('Adaugă')


class EditFuelForm(FlaskForm):
    plate_number = StringField('Număr înmatriculare', validators=[DataRequired(), Length(max=10)])
    fuel_date = DateField('Dată alimentare', validators=[DataRequired()])
    km = IntegerField('Kilometri', validators=[DataRequired()])
    diesel = DecimalField('Litri Diesel', validators=[InputRequired()])
    adblue = DecimalField('Litri AdBlue', validators=[InputRequired()])
    submit = SubmitField('Salvează')
