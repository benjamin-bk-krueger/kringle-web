from flask_wtf import FlaskForm  # integration with WTForms, data validation and CSRF protection
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, HiddenField, FileField, TextAreaField
from wtforms.validators import InputRequired, NoneOf, EqualTo, Email, Length, Regexp


class LoginForm(FlaskForm):
    creator = StringField('Name', validators=[InputRequired(), Length(min=5, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5, max=20)])
    remember = BooleanField('Remember me', default='checked')


class AccountForm(FlaskForm):
    creator = StringField('Name', validators=[InputRequired(), Length(min=5, max=20),
                                              NoneOf([' '], message='No spaces allowed')])
    email = StringField('E-Mail', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5, max=20),
                                                     EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Password Verification', validators=[InputRequired(), Length(min=5, max=20)])
    invitation = StringField('Invitation Code', validators=[InputRequired(), Length(min=5, max=20)])


class MailCreatorForm(FlaskForm):
    email = StringField('E-Mail', validators=[InputRequired(), Email()])
    description = TextAreaField('Description', validators=[Length(max=1024)])
    # url = StringField('URL', validators=[InputRequired(), URL()])
    url = StringField('Image URL')
    operation = HiddenField(default='mail')


class PassCreatorForm(FlaskForm):
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5, max=20),
                                                     EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Password Verification', validators=[InputRequired(), Length(min=5, max=20)])
    operation = HiddenField(default='pass')


class DelCreatorForm(FlaskForm):
    confirmation = StringField('Confirmation (enter delete)',
                               validators=[InputRequired(), Regexp("delete", message='Enter delete to confirm')])
    operation = HiddenField(default='delete')


class UploadForm(FlaskForm):
    file = FileField(validators=[FileRequired(), FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])
