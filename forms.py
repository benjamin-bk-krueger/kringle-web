from flask_wtf import FlaskForm  # integration with WTForms, data validation and CSRF protection
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, HiddenField, FileField, TextAreaField, SelectField
from wtforms.validators import InputRequired, NoneOf, EqualTo, Email, Length


# Every form used both in the Flask/Jinja templates as well the main Python app is defined here.
# Not all fields have full validators as they are used in modal windows.
class LoginForm(FlaskForm):
    creator = StringField('Name', validators=[InputRequired(), Length(min=5, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5, max=20)])
    remember = BooleanField('Remember me', default='checked')


class PasswordForm(FlaskForm):
    email = StringField('E-Mail', validators=[InputRequired(), Email()])


class PasswordResetForm(FlaskForm):
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5, max=20),
                                                     EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Password Verification', validators=[InputRequired(), Length(min=5, max=20)])


class AccountForm(FlaskForm):
    creator = StringField('Name', validators=[InputRequired(), Length(min=5, max=20),
                                              NoneOf([' '], message='No spaces allowed')])
    email = StringField('E-Mail', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5, max=20),
                                                     EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Password Verification', validators=[InputRequired(), Length(min=5, max=20)])
    invitation = StringField('Invitation Code', validators=[InputRequired(), Length(min=5, max=20)], default='guest')


class MailCreatorForm(FlaskForm):
    email = StringField('E-Mail', validators=[InputRequired(), Email()])
    description = TextAreaField('Description', validators=[Length(max=1024)])
    image = SelectField('Image', choices=["none"], validate_choice=False)
    notification = BooleanField('Send notifications', default='checked')


class PassCreatorForm(FlaskForm):
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5, max=20),
                                                     EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Password Verification', validators=[InputRequired(), Length(min=5, max=20)])
    operation = HiddenField(default='pass')


class DelCreatorForm(FlaskForm):
    operation = HiddenField(default='delete')


class UploadForm(FlaskForm):
    file = FileField(validators=[FileRequired(), FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])


class WorldForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    url = StringField('URL')
    description = TextAreaField('Description')
    image = SelectField('Image', choices=["none"], validate_choice=False)


class RoomForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    description = TextAreaField('Description')
    image = SelectField('Image', choices=["none"], validate_choice=False)


class ItemForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    description = TextAreaField('Description')
    image = SelectField('Image', choices=["none"], validate_choice=False)
    room = SelectField('Select Room', choices=["none"], validate_choice=False)


class PersonForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    description = TextAreaField('Description')
    image = SelectField('Image', choices=["none"], validate_choice=False)
    room = SelectField('Select Room', choices=["none"], validate_choice=False)


class ObjectiveForm(FlaskForm):
    name = StringField('Character Name', validators=[InputRequired()])
    title = StringField('Objective Title', validators=[InputRequired()])
    difficulty = SelectField('Difficulty', choices=[0, 1, 2, 3, 4, 5])
    url = StringField('URL')
    supported = SelectField('Supported by', choices=["none"], validate_choice=False)
    requires = SelectField('Requires', choices=["none"], validate_choice=False)
    description = TextAreaField('Description')
    image = SelectField('Image', choices=["none"], validate_choice=False)
    room = SelectField('Select Room', choices=["none"], validate_choice=False)


class JunctionForm(FlaskForm):
    description = TextAreaField('Description')
    room = SelectField('Select Room', choices=["none"], validate_choice=False)
    room_dest = SelectField('Select Destination Room', choices=["none"], validate_choice=False)


class ContactForm(FlaskForm):
    contact_name = StringField('Name', validators=[InputRequired(), Length(min=5, max=20)])
    email = StringField('E-Mail', validators=[InputRequired(), Email()])
    message = TextAreaField('Message', validators=[Length(max=1024)])
    check_captcha = HiddenField(default='0')
    captcha = StringField('Captcha', validators=[InputRequired(), EqualTo('check_captcha', message='Captcha does not '
                                                                                                   'match')])


class QuestSolForm(FlaskForm):
    operation = HiddenField(default='quest')
    ctf_flag = StringField('Flag', validators=[Length(max=100)])


class FileForm(FlaskForm):
    filename_new = StringField('File Name', validators=[InputRequired()])
    filename_old = HiddenField(default='filename')
