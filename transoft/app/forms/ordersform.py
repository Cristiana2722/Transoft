from flask_wtf import FlaskForm
from wtforms import SubmitField, DecimalField, StringField, DateField
from wtforms.validators import DataRequired, Optional, Length


class OrderForm(FlaskForm):
    order_date = DateField('Dată comandă', validators=[DataRequired()])
    position = StringField('Nr. referință', validators=[DataRequired(), Length(max=30)])
    vehicle = StringField('Camion', validators=[DataRequired(), Length(max=30)])
    trailer = StringField('Trailer', validators=[DataRequired(), Length(max=30)])
    amount = DecimalField('Suma', validators=[DataRequired()])
    departure = StringField('Plecare', validators=[DataRequired(), Length(max=100)])
    arrival = StringField('Sosire', validators=[DataRequired(), Length(max=100)])
    distance = DecimalField('Distanță', validators=[Optional()])
    submit = SubmitField('Adaugă')


class InvoiceForm(FlaskForm):
    position = StringField('Nr. referință', validators=[DataRequired(), Length(max=30)])
    invoice_no = StringField('Nr. factură', validators=[DataRequired(), Length(max=30)])
    invoice_date = DateField('Dată factură', validators=[DataRequired()])
    freight_value = DecimalField('Suma', validators=[DataRequired()])
    submit = SubmitField('Adaugă')


class EditOrderForm(FlaskForm):
    order_date = DateField('Dată comandă', validators=[DataRequired()])
    position = StringField('Nr. referință', validators=[DataRequired(), Length(max=30)])
    vehicle = StringField('Camion', validators=[DataRequired(), Length(max=30)])
    trailer = StringField('Trailer', validators=[DataRequired(), Length(max=30)])
    amount = DecimalField('Suma', validators=[DataRequired()])
    departure = StringField('Plecare', validators=[DataRequired(), Length(max=100)])
    arrival = StringField('Sosire', validators=[DataRequired(), Length(max=100)])
    distance = DecimalField('Distanță', validators=[Optional()])
    invoice_no = StringField('Nr. factură', validators=[Optional(), Length(max=30)])
    invoice_date = DateField('Dată factură', validators=[Optional()])
    freight_value = DecimalField('Suma', validators=[Optional()])
    submit = SubmitField('Salvează')
