from wtforms import Form, BooleanField, HiddenField, StringField, IntegerField, validators


class ItemForm(Form):
    name = StringField('Name', [validators.Length(min=5, max=60)])
    quantity = IntegerField('Quantity', [validators.NumberRange(min=0)])
    category = StringField('Category', [validators.Length(min=1, max=20)])


class ItemDelete(Form):
    id = HiddenField('ID')
    user_id = HiddenField('User_ID')

