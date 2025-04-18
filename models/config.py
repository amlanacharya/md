"""
Configuration models for OPTiMuS.
This module contains models for storing configuration settings for the application.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# This will be initialized in app.py
db = None

# Model definitions - these will be defined after db is initialized
SystemConfig = None
FieldConfig = None

def init_db(_db):
    """
    Initialize the database reference and define models.
    """
    global db, SystemConfig, FieldConfig
    db = _db

    # Check if models are already defined
    if SystemConfig is not None and FieldConfig is not None:
        print("Models already defined, skipping redefinition.")
        return

    print("Defining configuration models...")

    # Now define the models using the initialized db
    class SystemConfig(db.Model):
        """
        System-wide configuration settings.
        """
        __tablename__ = 'system_config'

        id = db.Column(db.Integer, primary_key=True)
        key = db.Column(db.String(100), unique=True, nullable=False)
        value = db.Column(db.String(255), nullable=True)
        description = db.Column(db.String(255), nullable=True)
        created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

        def __repr__(self):
            return f'<SystemConfig {self.key}={self.value}>'

    class FieldConfig(db.Model):
        """
        Configuration for loan application fields.
        """
        __tablename__ = 'field_config'

        id = db.Column(db.Integer, primary_key=True)
        field_name = db.Column(db.String(100), nullable=False)
        display_name = db.Column(db.String(100), nullable=False)
        is_required = db.Column(db.Boolean, default=True)
        is_visible = db.Column(db.Boolean, default=True)
        order = db.Column(db.Integer, default=0)

        # Role-based access control
        maker_can_edit = db.Column(db.Boolean, default=True)
        checker_can_edit = db.Column(db.Boolean, default=False)
        author_can_edit = db.Column(db.Boolean, default=False)

        created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

        def __repr__(self):
            return f'<FieldConfig {self.field_name}>'

    # Make the models available at module level
    globals()['SystemConfig'] = SystemConfig
    globals()['FieldConfig'] = FieldConfig

    print("Configuration models defined successfully.")


# This function is now defined above


def get_default_field_configs():
    """
    Get default field configurations for loan application.
    """
    return [
        # Basic Information
        FieldConfig(
            field_name='date',
            display_name='Date',
            is_required=True,
            is_visible=True,
            order=1,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='application_id',
            display_name='Application ID',
            is_required=True,
            is_visible=True,
            order=2,
            maker_can_edit=True,
            checker_can_edit=False,
            author_can_edit=False
        ),
        FieldConfig(
            field_name='customer_name',
            display_name='Customer Name',
            is_required=True,
            is_visible=True,
            order=3,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='dealer_code',
            display_name='Dealer Code',
            is_required=True,
            is_visible=True,
            order=4,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='scheme_name',
            display_name='Scheme Name',
            is_required=True,
            is_visible=True,
            order=5,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='branch_location',
            display_name='Branch Location',
            is_required=True,
            is_visible=True,
            order=6,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),

        # Product and Financial Information
        FieldConfig(
            field_name='product_type',
            display_name='Product Type',
            is_required=True,
            is_visible=True,
            order=7,
            maker_can_edit=True,
            checker_can_edit=False,
            author_can_edit=False
        ),
        FieldConfig(
            field_name='loan_amount',
            display_name='Loan Amount',
            is_required=True,
            is_visible=True,
            order=8,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='payment_amount',
            display_name='Payment Amount',
            is_required=True,
            is_visible=True,
            order=9,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='processing_fee',
            display_name='Processing Fee',
            is_required=True,
            is_visible=True,
            order=10,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='rto',
            display_name='RTO',
            is_required=True,
            is_visible=True,
            order=11,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='vap_amount',
            display_name='VAP Amount',
            is_required=True,
            is_visible=True,
            order=12,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),

        # Beneficiary Information
        FieldConfig(
            field_name='beneficiary_name',
            display_name='Beneficiary Name',
            is_required=True,
            is_visible=True,
            order=13,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='beneficiary_account_number',
            display_name='Beneficiary Account Number',
            is_required=True,
            is_visible=True,
            order=14,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='beneficiary_ifsc',
            display_name='Beneficiary IFSC',
            is_required=True,
            is_visible=True,
            order=15,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='bank_name',
            display_name='Bank Name',
            is_required=True,
            is_visible=True,
            order=16,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='branch_name',
            display_name='Branch Name',
            is_required=True,
            is_visible=True,
            order=17,
            maker_can_edit=True,
            checker_can_edit=True,
            author_can_edit=True
        ),

        # Workflow Fields
        FieldConfig(
            field_name='maker',
            display_name='Maker',
            is_required=True,
            is_visible=True,
            order=18,
            maker_can_edit=True,
            checker_can_edit=False,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='checker',
            display_name='Checker',
            is_required=False,
            is_visible=True,
            order=19,
            maker_can_edit=False,
            checker_can_edit=True,
            author_can_edit=True
        ),
        FieldConfig(
            field_name='author',
            display_name='Author',
            is_required=False,
            is_visible=True,
            order=20,
            maker_can_edit=False,
            checker_can_edit=False,
            author_can_edit=True
        ),
    ]


def get_default_system_configs():
    """
    Get default system configurations.
    """
    return [
        SystemConfig(
            key='WORKFLOW_MODE',
            value='manual',  # 'auto' or 'manual'
            description='Workflow mode: auto (bypass author) or manual (include author)'
        ),
        SystemConfig(
            key='ENABLE_FIELD_CONFIGURATION',
            value='true',
            description='Enable field configuration'
        ),
    ]


def init_default_configs():
    """
    Initialize default configurations if they don't exist.
    """
    try:
        # Add default system configs
        for config in get_default_system_configs():
            try:
                existing = SystemConfig.query.filter_by(key=config.key).first()
                if not existing:
                    db.session.add(config)
            except Exception as e:
                print(f"Error checking/adding system config {config.key}: {str(e)}")

        # Add default field configs
        for field_config in get_default_field_configs():
            try:
                existing = FieldConfig.query.filter_by(field_name=field_config.field_name).first()
                if not existing:
                    db.session.add(field_config)
            except Exception as e:
                print(f"Error checking/adding field config {field_config.field_name}: {str(e)}")

        db.session.commit()
        print("Default configurations initialized successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing default configurations: {str(e)}")
