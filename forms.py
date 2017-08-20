from wtforms import Form, BooleanField, StringField, IntegerField, validators


class ItemForm(Form):
    name = StringField('Name', [validators.Length(min=5, max=60)])
    quantity = IntegerField('Quantity', [validators.NumberRange(min=0)])
