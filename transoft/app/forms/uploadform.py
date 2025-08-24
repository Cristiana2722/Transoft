from flask_wtf import FlaskForm
from wtforms import SubmitField, DecimalField, StringField, DateField
from wtforms.validators import DataRequired, Optional, Length


class UploadedOrderForm(FlaskForm):
    order_date = DateField('Dată comandă', validators=[DataRequired()])
    position = StringField('Nr. referință', validators=[DataRequired(), Length(max=30)])
    vehicle = StringField('Camion', validators=[DataRequired(), Length(max=30)])
    trailer = StringField('Trailer', validators=[DataRequired(), Length(max=30)])
    amount = DecimalField('Suma', validators=[DataRequired()])
    departure = StringField('Plecare', validators=[DataRequired(), Length(max=100)])
    arrival = StringField('Sosire', validators=[DataRequired(), Length(max=100)])
    distance = DecimalField('Distanță (opțională)', validators=[Optional()])
    submit = SubmitField('Adaugă')


class UploadedInvoiceForm(FlaskForm):
    position = StringField('Nr. referință', validators=[DataRequired(), Length(max=30)])
    invoice_no = StringField('Nr. factură', validators=[DataRequired(), Length(max=30)])
    invoice_date = DateField('Dată factură', validators=[DataRequired()])
    freight_value = DecimalField('Suma', validators=[DataRequired()])
    submit = SubmitField('Adaugă')
