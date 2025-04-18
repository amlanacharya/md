"""
Forms for configuration management.
"""
from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, SubmitField, StringField
from wtforms.validators import DataRequired

class WorkflowConfigForm(FlaskForm):
    """
    Form for configuring workflow settings.
    """
    workflow_mode = SelectField(
        'Workflow Mode',
        choices=[
            ('manual', 'Manual Mode (Maker → Checker → Author)'),
            ('auto', 'Auto Mode (Maker → Checker, bypass Author)')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Save Workflow Configuration')


class FieldConfigForm(FlaskForm):
    """
    Form for configuring field settings.
    """
    # This form will be dynamically generated based on the fields in the database
    submit = SubmitField('Save Field Configuration')


class SystemConfigForm(FlaskForm):
    """
    Form for configuring system settings.
    """
    enable_field_configuration = BooleanField('Enable Field Configuration', default=True)
    submit = SubmitField('Save System Configuration')
