from flask_wtf import FlaskForm
from wtforms import SubmitField, DecimalField, StringField, TextAreaField, DateField, ValidationError
from wtforms.validators import DataRequired, Optional, Length


class PaymentForm(FlaskForm):
    payment_type = StringField('Tip plată', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Descriere (opțională)', validators=[Optional()])
    amount = DecimalField('Suma', validators=[DataRequired()])
    issue_date = DateField('Data emiterii',
                           validators=[DataRequired(message="Formatul datei de emitere este greșit.")]
                           )
    due_date = DateField('Data scadentă',
                         validators=[DataRequired(message="Formatul datei scadente este greșit.")]
                         )

    def validate_due_date(self, field):
        if self.issue_date.data and field.data:
            if field.data < self.issue_date.data:
                raise ValidationError('Data scadentă nu poate fi mai mică decât data emiterii.')

    submit = SubmitField('Adaugă')


class EditPaymentForm(FlaskForm):
    payment_type = StringField('Tip plată', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Descriere (opțională)', validators=[Optional()])
    amount = DecimalField('Suma', validators=[DataRequired()])
    issue_date = DateField('Data emiterii',
                           validators=[DataRequired(message="Formatul datei de emitere este greșit.")]
                           )
    due_date = DateField('Data scadentă',
                         validators=[DataRequired(message="Formatul datei scadente este greșit.")]
                         )

    def validate_due_date(self, field):
        if self.issue_date.data and field.data:
            if field.data < self.issue_date.data:
                raise ValidationError('Data scadentă nu poate fi mai mică decât data emiterii.')

    submit = SubmitField('Salvează')
