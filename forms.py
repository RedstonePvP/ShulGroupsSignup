from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired, Email, URL, Optional
from wtforms.widgets import TextArea
from wtforms.fields.html5 import DateField


class LoginForm(FlaskForm):
    username = StringField("Username",
                           validators=[DataRequired()])
    password = PasswordField("Password",
                             validators=[DataRequired()])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    cname = StringField("Child Name", validators=[DataRequired()])

    age = StringField("Age", validators=[DataRequired()])

    email = StringField("Email", validators=[DataRequired(), Email()])

    addr = StringField("Address", validators=[DataRequired()])

    pname = StringField("Parent Name", validators=[DataRequired()])

    phone = StringField("Phone Number", validators=[DataRequired()])

    pickup = StringField("Pickup Name", validators=[DataRequired()])

    minyan = StringField("Minyan", validators=[DataRequired()])

    alerg = StringField("Allergies", validators=[DataRequired()])

    submit = SubmitField("Reserve")


class NewWeek(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])

    date = DateField("Date", validators=[DataRequired()])

    grps = SelectMultipleField("Groups")

    visible = BooleanField("Active")

    url = StringField("Form URL", validators=[Optional()])

    submit = SubmitField("Save")


class NewGroup(FlaskForm):
    name = StringField("Group Name", validators=[DataRequired()])

    total = IntegerField("Total", validators=[DataRequired()])

    submit = SubmitField("Add")
