# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, FloatField, SubmitField, SelectField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length
from flask_wtf.csrf import CSRFProtect
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import io
import csv
import tempfile
import os
from excel_utils import export_applications_to_excel, export_distribution_to_excel, export_productivity_report_to_excel

# Import configuration models and services
from forms.config_form import WorkflowConfigForm, FieldConfigForm, SystemConfigForm
# Note: We'll get SystemConfig through the function below to avoid None issues

app = Flask(__name__)
app.config['SECRET_KEY'] = 'OADSECRET'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///optimus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Application configuration
app.config['ENABLE_PRODUCT_EXPERTISE'] = False  # Set to True to enable product expertise feature
app.config['ENABLE_FIELD_CONFIGURATION'] = True  # Enable field configuration

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ROLE_MAKER = 'maker'
ROLE_CHECKER = 'checker'
ROLE_AUTHOR = 'author'

# Role required decorator
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login', next=request.url))

            if not getattr(current_user, f'is_{role}')():
                flash(f'You need to be a {role} to access this page.', 'danger')
                return redirect(url_for('index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Product type constants - kept for backward compatibility
PRODUCT_PL = 'PL'  # Personal Loan
PRODUCT_TW = 'TW'  # Two Wheeler
PRODUCT_UTW = 'UTW'  # Used Two Wheeler
PRODUCT_UC = 'UC'  # Used Car

# Product model for dynamic product management
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, code, name, active=True):
        self.code = code
        self.name = name
        self.active = active

    def __repr__(self):
        return f'<Product {self.code}: {self.name}>'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_MAKER)
    active = db.Column(db.Boolean, default=True)

    # Product expertise (for checkers and authors)
    product_expertise = db.Column(db.String(10), nullable=True)

    # Availability status
    available = db.Column(db.Boolean, default=True)

    def __init__(self, username, email, password, role=ROLE_MAKER, product_expertise=None, available=True):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
        self.product_expertise = product_expertise
        self.available = available

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_maker(self):
        return self.role == ROLE_MAKER

    def is_checker(self):
        return self.role == ROLE_CHECKER

    def is_author(self):
        return self.role == ROLE_AUTHOR

    def __repr__(self):
        return f'<User {self.username}>'


class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    application_id = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    dealer_code = db.Column(db.String(50), nullable=False)
    scheme_name = db.Column(db.String(100), nullable=False)
    branch_location = db.Column(db.String(100), nullable=False)
    product_type = db.Column(db.String(50), nullable=False)
    loan_amount = db.Column(db.Float, nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    processing_fee = db.Column(db.Float, nullable=False)
    rto = db.Column(db.Float, nullable=False)
    vap_amount = db.Column(db.Float, nullable=False)
    beneficiary_name = db.Column(db.String(100), nullable=False)
    beneficiary_account_number = db.Column(db.String(50), nullable=False)
    beneficiary_ifsc = db.Column(db.String(20), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)

    # Workflow fields
    maker = db.Column(db.String(64), nullable=False)
    maker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    checker = db.Column(db.String(64), nullable=True)
    checker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    author = db.Column(db.String(64), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Status tracking
    STATUS_DRAFT = 'draft'
    STATUS_PENDING_CHECKER = 'pending_checker'
    STATUS_PENDING_AUTHOR = 'pending_author'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    status = db.Column(db.String(20), nullable=False, default=STATUS_DRAFT)

    # Rejection tracking
    rejection_reason = db.Column(db.Text, nullable=True)
    rejected_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    rejected_by = db.Column(db.String(64), nullable=True)

    # Timestamps for tracking
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    status_changed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<LoanApplication {self.application_id}>'

# Form for loan applications
class LoanApplicationForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    application_id = StringField('Application ID', validators=[DataRequired()])
    customer_name = StringField('Customer Name', validators=[DataRequired()])
    dealer_code = StringField('Dealer Code', validators=[DataRequired()])
    scheme_name = StringField('Scheme Name', validators=[DataRequired()])
    branch_location = StringField('Branch Location', validators=[DataRequired()])
    product_type = SelectField('Product Type', validators=[DataRequired()])
    loan_amount = FloatField('Loan Amount', validators=[DataRequired()])
    payment_amount = FloatField('Payment Amount', validators=[DataRequired()])
    processing_fee = FloatField('Processing Fee', validators=[DataRequired()])
    rto = FloatField('RTO', validators=[DataRequired()])
    vap_amount = FloatField('VAP Amount', validators=[DataRequired()])
    beneficiary_name = StringField('Beneficiary Name', validators=[DataRequired()])
    beneficiary_account_number = StringField('Beneficiary Account Number', validators=[DataRequired()])
    beneficiary_ifsc = StringField('Beneficiary IFSC', validators=[DataRequired()])
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    branch_name = StringField('Branch Name', validators=[DataRequired()])
    maker = StringField('Maker', validators=[DataRequired()])
    checker = StringField('Checker', validators=[])
    author = StringField('Author', validators=[])
    # Approval/Rejection fields
    approve = BooleanField('Approve Application')
    reject = BooleanField('Reject Application')
    rejection_reason = TextAreaField('Rejection Reason', validators=[Optional()])
    save_as_draft = SubmitField('Save as Draft')
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(LoanApplicationForm, self).__init__(*args, **kwargs)

        # Dynamically populate product type choices
        self.product_type.choices = [(p.code, f'{p.name} ({p.code})') for p in Product.query.filter_by(active=True).all()]

        # Apply field configurations if enabled
        if app.config['ENABLE_FIELD_CONFIGURATION']:
            self._apply_field_configurations()

        # Adjust field access based on user role
        if current_user.is_authenticated:
            if current_user.is_maker():
                # Maker can only edit maker field
                self.checker.render_kw = {'readonly': True}
                self.author.render_kw = {'readonly': True}

            elif current_user.is_checker():
                # Checker can edit maker and checker fields
                self.author.render_kw = {'readonly': True}
                # Auto-populate checker field with current checker's username
                if not self.checker.data:
                    self.checker.data = current_user.username

            elif current_user.is_author():
                # Auto-populate author field with current author's username
                if not self.author.data:
                    self.author.data = current_user.username

    def _apply_field_configurations(self):
        """Apply field configurations to form fields."""
        if not app.config['ENABLE_FIELD_CONFIGURATION']:
            return

        # Get all field configurations
        field_configs = FieldService.get_all_field_configs()

        # Apply configurations to each field
        for field_config in field_configs:
            field_name = field_config.field_name
            if hasattr(self, field_name):
                field = getattr(self, field_name)

                # Set visibility
                if not field_config.is_visible:
                    if not hasattr(field, 'render_kw') or field.render_kw is None:
                        field.render_kw = {}
                    field.render_kw['style'] = 'display: none;'

                # Set required status
                if not field_config.is_required:
                    field.validators = [v for v in field.validators if not isinstance(v, DataRequired)]

                # Set editability based on user role
                if current_user.is_authenticated:
                    can_edit = False
                    if current_user.is_maker() and field_config.maker_can_edit:
                        can_edit = True
                    elif current_user.is_checker() and field_config.checker_can_edit:
                        can_edit = True
                    elif current_user.is_author() and field_config.author_can_edit:
                        can_edit = True

                    if not can_edit:
                        if not hasattr(field, 'render_kw') or field.render_kw is None:
                            field.render_kw = {}
                        field.render_kw['readonly'] = True

# Form for login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

# Form for registration
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[
        (ROLE_MAKER, 'Maker'),
        (ROLE_CHECKER, 'Checker'),
        (ROLE_AUTHOR, 'Author')
    ])
    product_expertise = SelectField('Product Expertise', choices=[
        ('', 'None'),
        (PRODUCT_PL, 'Personal Loan (PL)'),
        (PRODUCT_TW, 'Two Wheeler (TW)'),
        (PRODUCT_UTW, 'Used Two Wheeler (UTW)'),
        (PRODUCT_UC, 'Used Car (UC)')
    ], validators=[Optional()])
    available = BooleanField('Available for Assignment', default=True)
    submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # Hide product expertise field if the feature is disabled
        if not app.config['ENABLE_PRODUCT_EXPERTISE']:
            self.product_expertise.render_kw = {'style': 'display: none;'}
            # Also hide the label by adding a class
            self.product_expertise.label.text = ''

# Form for editing users
class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[Optional()])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('password')])
    role = SelectField('Role', choices=[
        (ROLE_MAKER, 'Maker'),
        (ROLE_CHECKER, 'Checker'),
        (ROLE_AUTHOR, 'Author')
    ])
    product_expertise = SelectField('Product Expertise', validators=[Optional()])
    available = BooleanField('Available for Assignment', default=True)
    active = BooleanField('Active', default=True)
    submit = SubmitField('Update User')

    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        # Hide product expertise field if the feature is disabled
        if not app.config['ENABLE_PRODUCT_EXPERTISE']:
            self.product_expertise.render_kw = {'style': 'display: none;'}
            # Also hide the label by adding a class
            self.product_expertise.label.text = ''

        # Dynamically populate product expertise choices
        self.product_expertise.choices = [('', 'None')] + [(p.code, f'{p.name} ({p.code})') for p in Product.query.filter_by(active=True).all()]

# Form for adding/editing products
class ProductForm(FlaskForm):
    code = StringField('Product Code', validators=[DataRequired(), Length(min=1, max=10)])
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=100)])
    active = BooleanField('Active', default=True)
    submit = SubmitField('Save Product')

# Routes
@app.route('/')
@app.route('/page/<int:page>')
@login_required
def index(page=1):
    # Get filter parameters
    status_filter = request.args.get('status', '')
    search_term = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'updated_at')
    sort_order = request.args.get('sort_order', 'desc')
    per_page = 10  # Number of items per page

    # Base query
    query = LoanApplication.query

    # Apply role-based filtering
    if current_user.is_maker():
        # Makers see applications they created
        query = query.filter_by(maker_id=current_user.id)
    elif current_user.is_checker():
        # Checkers see applications waiting for checker approval and those they've checked
        query = query.filter(
            (LoanApplication.status == LoanApplication.STATUS_PENDING_CHECKER) |
            (LoanApplication.checker_id == current_user.id)
        )
    # Authors see all applications (no additional filter)

    # Apply status filter if provided
    if status_filter:
        query = query.filter(LoanApplication.status == status_filter)

    # Apply search filter if provided
    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(
            (LoanApplication.customer_name.like(search_pattern)) |
            (LoanApplication.application_id.like(search_pattern)) |
            (LoanApplication.product_type.like(search_pattern))
        )

    # Apply sorting
    sort_column = getattr(LoanApplication, sort_by, LoanApplication.updated_at)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Paginate the results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    loan_applications = pagination.items

    # Get status counts for dashboard
    status_counts = {
        'draft': LoanApplication.query.filter_by(status=LoanApplication.STATUS_DRAFT).count(),
        'pending_checker': LoanApplication.query.filter_by(status=LoanApplication.STATUS_PENDING_CHECKER).count(),
        'pending_author': LoanApplication.query.filter_by(status=LoanApplication.STATUS_PENDING_AUTHOR).count(),
        'approved': LoanApplication.query.filter_by(status=LoanApplication.STATUS_APPROVED).count(),
        'rejected': LoanApplication.query.filter_by(status=LoanApplication.STATUS_REJECTED).count(),
        'total': LoanApplication.query.count()
    }

    return render_template(
        'index.html',
        loan_applications=loan_applications,
        pagination=pagination,
        status_filter=status_filter,
        search_term=search_term,
        sort_by=sort_by,
        sort_order=sort_order,
        status_counts=status_counts
    )

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_loan():
    form = LoanApplicationForm()

    # Set the maker field to current user if a maker
    if current_user.is_maker():
        form.maker.data = current_user.username

    if form.validate_on_submit():
        # Validate field access by role
        if current_user.is_maker():
            if form.checker.data or form.author.data:
                flash('As a Maker, you cannot set Checker or Author fields.', 'danger')
                field_service = FieldService
                field_service.workflow_service = WorkflowService
                return render_template('add_edit.html', form=form, title='Add Loan Application', field_service=field_service)

        elif current_user.is_checker():
            if form.author.data:
                flash('As a Checker, you cannot set the Author field.', 'danger')
                field_service = FieldService
                field_service.workflow_service = WorkflowService
                return render_template('add_edit.html', form=form, title='Add Loan Application', field_service=field_service)

        # Check if save as draft was requested
        if form.save_as_draft.data:
            status = LoanApplication.STATUS_DRAFT
        # Set initial status based on role and workflow mode
        elif current_user.is_maker():
            status = LoanApplication.STATUS_PENDING_CHECKER
        elif current_user.is_checker():
            # In auto mode, checker approval goes straight to approved
            if WorkflowService.is_auto_mode():
                status = LoanApplication.STATUS_APPROVED
            else:
                status = LoanApplication.STATUS_PENDING_AUTHOR
        else:  # Author
            status = LoanApplication.STATUS_APPROVED

        loan_application = LoanApplication(
            date=form.date.data,
            application_id=form.application_id.data,
            customer_name=form.customer_name.data,
            dealer_code=form.dealer_code.data,
            scheme_name=form.scheme_name.data,
            branch_location=form.branch_location.data,
            product_type=form.product_type.data,
            loan_amount=form.loan_amount.data,
            payment_amount=form.payment_amount.data,
            processing_fee=form.processing_fee.data,
            rto=form.rto.data,
            vap_amount=form.vap_amount.data,
            beneficiary_name=form.beneficiary_name.data,
            beneficiary_account_number=form.beneficiary_account_number.data,
            beneficiary_ifsc=form.beneficiary_ifsc.data,
            bank_name=form.bank_name.data,
            branch_name=form.branch_name.data,
            maker=form.maker.data,
            checker=form.checker.data if current_user.is_checker() or current_user.is_author() else "",
            author=form.author.data if current_user.is_author() else "",
            maker_id=current_user.id if current_user.is_maker() else None,
            checker_id=current_user.id if current_user.is_checker() else None,
            author_id=current_user.id if current_user.is_author() else None,
            status=status
        )

        try:
            db.session.add(loan_application)
            db.session.commit()
            if form.save_as_draft.data:
                flash('Loan application saved as draft successfully!', 'info')
            else:
                flash('Loan application added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding loan application: {str(e)}', 'danger')

    # Pass both field service and workflow service to the template
    field_service = FieldService
    field_service.workflow_service = WorkflowService
    return render_template('add_edit.html', form=form, title='Add Loan Application', field_service=field_service)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_loan(id):
    loan_application = LoanApplication.query.get_or_404(id)
    form = LoanApplicationForm(obj=loan_application)

    # For checkers, auto-populate their username in checker field if empty
    if current_user.is_checker() and not loan_application.checker:
        form.checker.data = current_user.username

    # For authors, auto-populate their username in author field if empty
    if current_user.is_author() and not loan_application.author:
        form.author.data = current_user.username

    if form.validate_on_submit():
        # Validate field access by role
        if current_user.is_maker():
            # Check if checker field was modified (only if both values are not empty)
            checker_modified = form.checker.data and loan_application.checker and form.checker.data != loan_application.checker
            # Check if author field was modified (only if both values are not empty)
            author_modified = form.author.data and loan_application.author and form.author.data != loan_application.author

            if checker_modified or author_modified:
                flash('As a Maker, you cannot modify Checker or Author fields.', 'danger')
                field_service = FieldService
                field_service.workflow_service = WorkflowService
                return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application, field_service=field_service)

        elif current_user.is_checker():
            # Only check for author field modification if both values are not empty
            if form.author.data and loan_application.author and form.author.data != loan_application.author:
                flash('As a Checker, you cannot modify the Author field.', 'danger')
                field_service = FieldService
                field_service.workflow_service = WorkflowService
                return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application, field_service=field_service)

        # Update fields
        loan_application.date = form.date.data
        loan_application.application_id = form.application_id.data
        loan_application.customer_name = form.customer_name.data
        loan_application.dealer_code = form.dealer_code.data
        loan_application.scheme_name = form.scheme_name.data
        loan_application.branch_location = form.branch_location.data
        loan_application.product_type = form.product_type.data
        loan_application.loan_amount = form.loan_amount.data
        loan_application.payment_amount = form.payment_amount.data
        loan_application.processing_fee = form.processing_fee.data
        loan_application.rto = form.rto.data
        loan_application.vap_amount = form.vap_amount.data
        loan_application.beneficiary_name = form.beneficiary_name.data
        loan_application.beneficiary_account_number = form.beneficiary_account_number.data
        loan_application.beneficiary_ifsc = form.beneficiary_ifsc.data
        loan_application.bank_name = form.bank_name.data
        loan_application.branch_name = form.branch_name.data

        # Update workflow fields and status based on role permissions
        if current_user.is_author():
            loan_application.maker = form.maker.data
            loan_application.checker = form.checker.data
            loan_application.author = form.author.data or current_user.username
            loan_application.author_id = current_user.id

            # Check if save as draft was requested
            if form.save_as_draft.data:
                loan_application.status = LoanApplication.STATUS_DRAFT
                loan_application.status_changed_at = datetime.utcnow()
                # Other fields will be updated but status remains draft
            # Handle approval or rejection
            elif form.approve.data and form.reject.data:
                flash('Cannot both approve and reject an application.', 'danger')
                field_service = FieldService
                field_service.workflow_service = WorkflowService
                return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application, field_service=field_service)
            elif form.approve.data:
                loan_application.status = LoanApplication.STATUS_APPROVED
                loan_application.status_changed_at = datetime.utcnow()
                flash('Application has been approved!', 'success')
            elif form.reject.data:
                if not form.rejection_reason.data:
                    flash('Rejection reason is required when rejecting an application.', 'danger')
                    field_service = FieldService
                    field_service.workflow_service = WorkflowService
                    return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application, field_service=field_service)
                loan_application.status = LoanApplication.STATUS_REJECTED
                loan_application.rejection_reason = form.rejection_reason.data
                loan_application.rejected_by = current_user.username
                loan_application.rejected_by_id = current_user.id
                loan_application.status_changed_at = datetime.utcnow()
                flash('Application has been rejected!', 'danger')

        elif current_user.is_checker():
            loan_application.maker = form.maker.data
            loan_application.checker = form.checker.data or current_user.username
            if form.checker.data == current_user.username or not loan_application.checker:
                loan_application.checker_id = current_user.id

                # Check if save as draft was requested
                if form.save_as_draft.data:
                    loan_application.status = LoanApplication.STATUS_DRAFT
                    loan_application.status_changed_at = datetime.utcnow()
                    # Other fields will be updated but status remains draft
                # Handle approval or rejection
                elif form.approve.data and form.reject.data:
                    flash('Cannot both approve and reject an application.', 'danger')
                    field_service = FieldService
                    field_service.workflow_service = WorkflowService
                    return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application, field_service=field_service)
                elif form.approve.data:
                    # In auto mode, checker approval goes straight to approved
                    if WorkflowService.is_auto_mode():
                        loan_application.status = LoanApplication.STATUS_APPROVED
                        loan_application.status_changed_at = datetime.utcnow()
                        flash('Application approved! (Auto mode: Author stage bypassed)', 'success')
                    else:
                        loan_application.status = LoanApplication.STATUS_PENDING_AUTHOR
                        loan_application.status_changed_at = datetime.utcnow()
                        flash('Application approved and forwarded to Author!', 'success')
                elif form.reject.data:
                    if not form.rejection_reason.data:
                        flash('Rejection reason is required when rejecting an application.', 'danger')
                        field_service = FieldService
                        field_service.workflow_service = WorkflowService
                        return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application, field_service=field_service)
                    loan_application.status = LoanApplication.STATUS_REJECTED
                    loan_application.rejection_reason = form.rejection_reason.data
                    loan_application.rejected_by = current_user.username
                    loan_application.rejected_by_id = current_user.id
                    loan_application.status_changed_at = datetime.utcnow()
                    flash('Application has been rejected!', 'danger')

        elif current_user.is_maker():
            loan_application.maker = form.maker.data
            if form.maker.data == current_user.username:
                loan_application.maker_id = current_user.id
                # Check if save as draft was requested
                if form.save_as_draft.data:
                    loan_application.status = LoanApplication.STATUS_DRAFT
                else:
                    loan_application.status = LoanApplication.STATUS_PENDING_CHECKER
                loan_application.status_changed_at = datetime.utcnow()

        try:
            db.session.commit()
            if form.save_as_draft.data:
                flash('Loan application saved as draft successfully!', 'info')
            else:
                flash('Loan application updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating loan application: {str(e)}', 'danger')

    # Pass both field service and workflow service to the template
    field_service = FieldService
    field_service.workflow_service = WorkflowService
    return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application, field_service=field_service)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
@role_required('author')  # Only authors can delete loan applications
def delete_loan(id):
    loan_application = LoanApplication.query.get_or_404(id)

    try:
        db.session.delete(loan_application)
        db.session.commit()
        flash('Loan application deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting loan application: {str(e)}', 'danger')

    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome, {user.username}! You are now logged in.', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')

    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
@role_required('author')  # Only authors can register new users
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Only set product expertise if the feature is enabled
        product_expertise = None
        if app.config['ENABLE_PRODUCT_EXPERTISE']:
            # Only set product expertise for checker and author roles
            if form.role.data in [ROLE_CHECKER, ROLE_AUTHOR] and form.product_expertise.data:
                product_expertise = form.product_expertise.data

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data,
            product_expertise=product_expertise,
            available=form.available.data
        )
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('users'))

    return render_template('register.html', title='Register', form=form)

@app.route('/users')
@login_required
@role_required('author')  # Only authors can view the user list
def users():
    users = User.query.all()
    from flask import current_app
    return render_template('users.html', title='Users', users=users, enable_product_expertise=current_app.config['ENABLE_PRODUCT_EXPERTISE'])

@app.route('/edit-user/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('author')  # Only authors can edit users
def edit_user(id):
    user = User.query.get_or_404(id)
    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.available = form.available.data
        user.active = form.active.data

        # Only update password if provided
        if form.password.data:
            user.set_password(form.password.data)

        # Only set product expertise if the feature is enabled
        if app.config['ENABLE_PRODUCT_EXPERTISE']:
            # Only set product expertise for checker and author roles
            if form.role.data in [ROLE_CHECKER, ROLE_AUTHOR] and form.product_expertise.data:
                user.product_expertise = form.product_expertise.data
            else:
                user.product_expertise = None

        try:
            db.session.commit()
            flash(f'User {user.username} has been updated successfully!', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')

    from flask import current_app
    return render_template('edit_user.html', title='Edit User', form=form, user=user, enable_product_expertise=current_app.config['ENABLE_PRODUCT_EXPERTISE'])

@app.route('/delete-user/<int:id>', methods=['POST'])
@login_required
@role_required('author')  # Only authors can delete users
def delete_user(id):
    user = User.query.get_or_404(id)

    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('users'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')

    return redirect(url_for('users'))

# Add a route for the user profile
@app.route('/profile')
@login_required
def profile():
    from flask import current_app
    return render_template('profile.html', title='My Profile', enable_product_expertise=current_app.config['ENABLE_PRODUCT_EXPERTISE'])


# Helper function to auto-distribute applications equally
def auto_distribute_applications(applications_by_product, available_users, user_role):
    if not available_users:
        return False

    # Count total applications
    total_applications = sum(len(apps) for apps in applications_by_product.values())
    if total_applications == 0:
        return False

    # Get current workload for each user
    user_workloads = {}
    for user in available_users:
        if user_role == ROLE_CHECKER:
            workload = LoanApplication.query.filter_by(checker_id=user.id, status=LoanApplication.STATUS_PENDING_CHECKER).count()
        else:  # ROLE_AUTHOR
            workload = LoanApplication.query.filter_by(author_id=user.id, status=LoanApplication.STATUS_PENDING_AUTHOR).count()
        user_workloads[user.id] = workload

    # Sort users by workload (least busy first)
    sorted_users = sorted(available_users, key=lambda u: user_workloads[u.id])

    # Distribute applications equally among users by product type
    for product_type, applications in applications_by_product.items():
        # For each product type, distribute applications evenly
        for i, app in enumerate(applications):
            # Assign to user with least workload
            user_index = i % len(sorted_users)
            user = sorted_users[user_index]

            # Update application
            if user_role == ROLE_CHECKER:
                app.checker = user.username
                app.checker_id = user.id
            else:  # ROLE_AUTHOR
                app.author = user.username
                app.author_id = user.id

            # Update workload count
            user_workloads[user.id] += 1

            # Re-sort users by updated workload
            sorted_users = sorted(available_users, key=lambda u: user_workloads[u.id])

    return True

# Route for distributing applications among checkers
@app.route('/distribute-applications', methods=['GET', 'POST'])
@login_required
@role_required('checker')  # Only checkers can distribute applications
def distribute_applications():
    # Get all available checkers with their product expertise
    available_checkers = User.query.filter_by(role=ROLE_CHECKER, available=True).all()

    # Get all pending checker applications
    pending_applications = LoanApplication.query.filter_by(status=LoanApplication.STATUS_PENDING_CHECKER, checker=None).all()

    # Group applications by product type
    applications_by_product = {}
    for app in pending_applications:
        if app.product_type not in applications_by_product:
            applications_by_product[app.product_type] = []
        applications_by_product[app.product_type].append(app)

    if request.method == 'POST':
        # Check if auto-distribute button was clicked
        if 'auto_distribute' in request.form:
            # Auto-distribute applications
            if auto_distribute_applications(applications_by_product, available_checkers, ROLE_CHECKER):
                db.session.commit()
                flash('Applications have been auto-distributed successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('No applications to distribute or no available checkers.', 'warning')
                return redirect(url_for('distribute_applications'))
        else:
            # Manual distribution
            for app_id in request.form.getlist('application_ids'):
                checker_id = request.form.get(f'checker_{app_id}')
                if checker_id:
                    app = LoanApplication.query.get(app_id)
                    checker = User.query.get(checker_id)
                    if app and checker:
                        app.checker = checker.username
                        app.checker_id = checker.id

            db.session.commit()
            flash('Applications have been distributed successfully!', 'success')
            return redirect(url_for('index'))

    # Get the Flask app instance from current_app
    from flask import current_app
    return render_template('distribute.html',
                           title='Distribute Applications',
                           available_checkers=available_checkers,
                           pending_applications=pending_applications,
                           applications_by_product=applications_by_product,
                           enable_product_expertise=current_app.config['ENABLE_PRODUCT_EXPERTISE'],
                           LoanApplication=LoanApplication)


# Route for distributing applications among authors
@app.route('/distribute-author-applications', methods=['GET', 'POST'])
@login_required
@role_required('author')  # Only authors can distribute applications
def distribute_author_applications():
    # Check if we're in auto mode - if so, redirect to index with a message
    if WorkflowService.is_auto_mode():
        flash('Author distribution is not available in Auto Mode. System is configured to bypass the Author stage.', 'warning')
        return redirect(url_for('index'))

    # Get all available authors with their product expertise
    available_authors = User.query.filter_by(role=ROLE_AUTHOR, available=True).all()

    # Get all pending author applications
    pending_applications = LoanApplication.query.filter_by(status=LoanApplication.STATUS_PENDING_AUTHOR, author=None).all()

    # Group applications by product type
    applications_by_product = {}
    for app in pending_applications:
        if app.product_type not in applications_by_product:
            applications_by_product[app.product_type] = []
        applications_by_product[app.product_type].append(app)

    if request.method == 'POST':
        # Check if auto-distribute button was clicked
        if 'auto_distribute' in request.form:
            # Auto-distribute applications
            if auto_distribute_applications(applications_by_product, available_authors, ROLE_AUTHOR):
                db.session.commit()
                flash('Applications have been auto-distributed successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('No applications to distribute or no available authors.', 'warning')
                return redirect(url_for('distribute_author_applications'))
        else:
            # Manual distribution
            for app_id in request.form.getlist('application_ids'):
                author_id = request.form.get(f'author_{app_id}')
                if author_id:
                    app = LoanApplication.query.get(app_id)
                    author = User.query.get(author_id)
                    if app and author:
                        app.author = author.username
                        app.author_id = author.id

            db.session.commit()
            flash('Applications have been distributed successfully!', 'success')
            return redirect(url_for('index'))

    # Get the Flask app instance from current_app
    from flask import current_app
    return render_template('distribute_author.html',
                           title='Distribute Applications to Authors',
                           available_authors=available_authors,
                           pending_applications=pending_applications,
                           applications_by_product=applications_by_product,
                           enable_product_expertise=current_app.config['ENABLE_PRODUCT_EXPERTISE'],
                           LoanApplication=LoanApplication)


# Route for toggling user availability
@app.route('/toggle-availability/<int:id>', methods=['POST'])
@login_required
def toggle_availability(id):
    user = User.query.get_or_404(id)

    # Only allow users to toggle their own availability or authors to toggle anyone's
    if current_user.id == user.id or current_user.is_author():
        user.available = not user.available
        db.session.commit()
        status = 'available' if user.available else 'unavailable'
        flash(f'User {user.username} is now {status}', 'success')
    else:
        flash('You do not have permission to change this user\'s availability', 'danger')

    return redirect(request.referrer or url_for('users'))


@app.route('/view/<int:id>')
@login_required
def view_loan(id):
    loan_application = LoanApplication.query.get_or_404(id)
    return render_template('view.html', loan=loan_application)

# API endpoint for real-time updates
@app.route('/api/check-updates', methods=['POST'])
@login_required
def check_updates():
    data = request.json
    loan_ids = data.get('loan_ids', [])

    if not loan_ids:
        return jsonify({'updates': []})

    # Get the last time the client checked for updates
    last_check = request.headers.get('Last-Check-Time')
    if last_check:
        try:
            last_check_time = datetime.fromisoformat(last_check)
        except ValueError:
            last_check_time = None
    else:
        last_check_time = None

    # Query for updated loan applications
    query = LoanApplication.query.filter(LoanApplication.id.in_(loan_ids))

    # If we have a last check time, only get applications updated since then
    if last_check_time:
        query = query.filter(LoanApplication.updated_at > last_check_time)

    updated_loans = query.all()

    # Format the response
    updates = [{
        'id': loan.id,
        'status': loan.status,
        'updated_at': loan.updated_at.isoformat() if loan.updated_at else None
    } for loan in updated_loans]

    return jsonify({
        'updates': updates,
        'server_time': datetime.utcnow().isoformat()
    })

# Route for viewing assigned cases for checkers
@app.route('/assigned-cases/checker')
@login_required
@role_required('checker')
def assigned_cases_checker():
    # Get all applications assigned to the current checker
    assigned_applications = LoanApplication.query.filter_by(
        checker_id=current_user.id,
        status=LoanApplication.STATUS_PENDING_CHECKER
    ).order_by(LoanApplication.updated_at.desc()).all()

    # Group applications by product type
    applications_by_product = {}
    for app in assigned_applications:
        if app.product_type not in applications_by_product:
            applications_by_product[app.product_type] = []
        applications_by_product[app.product_type].append(app)

    return render_template('assigned_cases.html',
                          title='My Assigned Cases',
                          applications_by_product=applications_by_product,
                          role='checker',
                          LoanApplication=LoanApplication)

# Route for viewing assigned cases for authors
@app.route('/assigned-cases/author')
@login_required
@role_required('author')
def assigned_cases_author():
    # Check if we're in auto mode - if so, redirect to index with a message
    if WorkflowService.is_auto_mode():
        flash('Author assigned cases view is not available in Auto Mode. System is configured to bypass the Author stage.', 'warning')
        return redirect(url_for('index'))

    # Get all applications assigned to the current author
    assigned_applications = LoanApplication.query.filter_by(
        author_id=current_user.id,
        status=LoanApplication.STATUS_PENDING_AUTHOR
    ).order_by(LoanApplication.updated_at.desc()).all()

    # Group applications by product type
    applications_by_product = {}
    for app in assigned_applications:
        if app.product_type not in applications_by_product:
            applications_by_product[app.product_type] = []
        applications_by_product[app.product_type].append(app)

    return render_template('assigned_cases.html',
                          title='My Assigned Cases',
                          applications_by_product=applications_by_product,
                          role='author',
                          LoanApplication=LoanApplication)

# Route for exporting assigned cases to Excel for checkers
@app.route('/export-cases/checker')
@login_required
@role_required('checker')
def export_cases_checker():
    # Get all applications assigned to the current checker
    assigned_applications = LoanApplication.query.filter_by(
        checker_id=current_user.id,
        status=LoanApplication.STATUS_PENDING_CHECKER
    ).order_by(LoanApplication.updated_at.desc()).all()

    # Export to Excel
    output, filename = export_applications_to_excel(
        applications=assigned_applications,
        filename_prefix='assigned_cases_checker',
        include_checker=False,
        include_author=False,
        include_rejection=False
    )

    # Return the Excel file
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Route for exporting assigned cases to Excel for authors
@app.route('/export-cases/author')
@login_required
@role_required('author')
def export_cases_author():
    # Check if we're in auto mode - if so, redirect to index with a message
    if WorkflowService.is_auto_mode():
        flash('Author cases export is not available in Auto Mode. System is configured to bypass the Author stage.', 'warning')
        return redirect(url_for('index'))

    # Get all applications assigned to the current author
    assigned_applications = LoanApplication.query.filter_by(
        author_id=current_user.id,
        status=LoanApplication.STATUS_PENDING_AUTHOR
    ).order_by(LoanApplication.updated_at.desc()).all()

    # Export to Excel
    output, filename = export_applications_to_excel(
        applications=assigned_applications,
        filename_prefix='assigned_cases_author',
        include_checker=True,
        include_author=False,
        include_rejection=False
    )

    # Return the Excel file
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Route for exporting all distributed applications for checkers
@app.route('/export-distribution/checker')
@login_required
@role_required('checker')
def export_distribution_checker():
    # Get all applications that have been distributed to checkers
    distributed_applications = LoanApplication.query.filter(
        LoanApplication.checker_id.isnot(None),
        LoanApplication.status == LoanApplication.STATUS_PENDING_CHECKER
    ).order_by(LoanApplication.updated_at.desc()).all()

    # Group applications by checker
    applications_by_checker = {}
    for app in distributed_applications:
        checker = User.query.get(app.checker_id)
        if checker:
            if checker.username not in applications_by_checker:
                applications_by_checker[checker.username] = []
            applications_by_checker[checker.username].append(app)

    # Export to Excel
    output, filename = export_distribution_to_excel(
        applications_by_user=applications_by_checker,
        filename_prefix='distribution_checker',
        role_type='checker'
    )

    # Return the Excel file
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Route for exporting all distributed applications for authors
@app.route('/export-distribution/author')
@login_required
@role_required('author')
def export_distribution_author():
    # Check if we're in auto mode - if so, redirect to index with a message
    if WorkflowService.is_auto_mode():
        flash('Author distribution export is not available in Auto Mode. System is configured to bypass the Author stage.', 'warning')
        return redirect(url_for('index'))

    # Get all applications that have been distributed to authors
    distributed_applications = LoanApplication.query.filter(
        LoanApplication.author_id.isnot(None),
        LoanApplication.status == LoanApplication.STATUS_PENDING_AUTHOR
    ).order_by(LoanApplication.updated_at.desc()).all()

    # Group applications by author
    applications_by_author = {}
    for app in distributed_applications:
        author = User.query.get(app.author_id)
        if author:
            if author.username not in applications_by_author:
                applications_by_author[author.username] = []
            applications_by_author[author.username].append(app)

    # Export to Excel
    output, filename = export_distribution_to_excel(
        applications_by_user=applications_by_author,
        filename_prefix='distribution_author',
        role_type='author'
    )

    # Return the Excel file
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Route for exporting all cases with sorting options
@app.route('/export-queue')
@login_required
def export_queue():
    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'updated_at')
    sort_order = request.args.get('sort_order', 'desc')
    status_filter = request.args.get('status', '')
    search_term = request.args.get('search', '')

    # Base query - all applications in the system
    query = LoanApplication.query

    # Apply status filter if provided
    if status_filter:
        query = query.filter(LoanApplication.status == status_filter)

    # Apply search filter if provided
    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(
            (LoanApplication.customer_name.like(search_pattern)) |
            (LoanApplication.application_id.like(search_pattern)) |
            (LoanApplication.product_type.like(search_pattern))
        )

    # Apply sorting
    sort_column = getattr(LoanApplication, sort_by, LoanApplication.updated_at)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Get all applications
    applications = query.all()

    # Include all relevant fields in the export
    # Everyone should see maker, checker, and author information in the queue export
    # Only include rejection information if the application is rejected

    # Export to Excel
    output, filename = export_applications_to_excel(
        applications=applications,
        filename_prefix='queue_export',
        include_checker=True,
        include_author=True,
        include_rejection=True
    )

    # Return the Excel file
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Route for viewing assigned cases for makers
@app.route('/assigned-cases/maker')
@login_required
@role_required('maker')
def assigned_cases_maker():
    # Get all applications created by the current maker
    assigned_applications = LoanApplication.query.filter_by(
        maker_id=current_user.id
    ).order_by(LoanApplication.updated_at.desc()).all()

    # Group applications by product type
    applications_by_product = {}
    for app in assigned_applications:
        if app.product_type not in applications_by_product:
            applications_by_product[app.product_type] = []
        applications_by_product[app.product_type].append(app)

    return render_template('assigned_cases.html',
                          title='My Applications',
                          applications_by_product=applications_by_product,
                          role='maker',
                          LoanApplication=LoanApplication)

# Route for exporting assigned cases to Excel for makers
@app.route('/export-cases/maker')
@login_required
@role_required('maker')
def export_cases_maker():
    # Get all applications created by the current maker
    assigned_applications = LoanApplication.query.filter_by(
        maker_id=current_user.id
    ).order_by(LoanApplication.updated_at.desc()).all()

    # Export to Excel
    output, filename = export_applications_to_excel(
        applications=assigned_applications,
        filename_prefix='my_applications_maker',
        include_checker=True,
        include_author=True,
        include_rejection=True
    )

    # Return the Excel file
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Routes for product management
@app.route('/products')
@login_required
@role_required('author')  # Only authors can manage products
def products():
    products = Product.query.all()
    return render_template('products.html', title='Product Management', products=products)

# Route for application manager
@app.route('/application-manager')
@login_required
def application_manager():
    # Get search parameters
    search_type = request.args.get('search_type', 'user')
    user_id = request.args.get('user_id', '')
    application_id = request.args.get('application_id', '')
    search_performed = bool(user_id or application_id)

    # Initialize applications list
    applications = []

    # Get all users for the dropdown
    all_users = User.query.all()

    # Get users by role for the reassignment dropdowns
    maker_users = User.query.filter_by(role=ROLE_MAKER, active=True).all()
    checker_users = User.query.filter_by(role=ROLE_CHECKER, active=True).all()
    author_users = User.query.filter_by(role=ROLE_AUTHOR, active=True).all()

    # Convert user objects to dictionaries for JavaScript
    maker_users_json = [{'id': user.id, 'username': user.username} for user in maker_users]
    checker_users_json = [{'id': user.id, 'username': user.username} for user in checker_users]
    author_users_json = [{'id': user.id, 'username': user.username} for user in author_users]

    # Perform search if parameters are provided
    if search_type == 'user' and user_id:
        # Search by user ID
        user = User.query.get(user_id)
        if user:
            if user.role == ROLE_MAKER:
                # Get all applications where user is the maker
                applications = LoanApplication.query.filter_by(maker_id=user.id).all()
            elif user.role == ROLE_CHECKER:
                # Get all applications where user is the checker
                applications = LoanApplication.query.filter_by(checker_id=user.id).all()
            elif user.role == ROLE_AUTHOR:
                # Get all applications where user is the author
                applications = LoanApplication.query.filter_by(author_id=user.id).all()

    elif search_type == 'application' and application_id:
        # Search by application ID
        applications = LoanApplication.query.filter(LoanApplication.application_id.like(f'%{application_id}%')).all()

    return render_template('application_manager.html',
                           title='Application Manager',
                           all_users=all_users,
                           applications=applications,
                           search_type=search_type,
                           user_id=user_id,
                           application_id=application_id,
                           search_performed=search_performed,
                           maker_users=maker_users_json,
                           checker_users=checker_users_json,
                           author_users=author_users_json)

# Route for reassigning applications
@app.route('/reassign-application/<int:app_id>', methods=['POST'])
@login_required
def reassign_application(app_id):
    # Get the application
    application = LoanApplication.query.get_or_404(app_id)

    # Get form data
    role_type = request.form.get('role_type')
    new_user_id = request.form.get('new_user_id')

    if not role_type or not new_user_id:
        flash('Role type and new user must be specified.', 'danger')
        return redirect(url_for('application_manager'))

    # Get the new user
    new_user = User.query.get(new_user_id)
    if not new_user:
        flash('Selected user not found.', 'danger')
        return redirect(url_for('application_manager'))

    # Validate that the new user has the correct role
    if role_type == 'maker' and new_user.role != ROLE_MAKER:
        flash('Selected user is not a Maker.', 'danger')
        return redirect(url_for('application_manager'))
    elif role_type == 'checker' and new_user.role != ROLE_CHECKER:
        flash('Selected user is not a Checker.', 'danger')
        return redirect(url_for('application_manager'))
    elif role_type == 'author' and new_user.role != ROLE_AUTHOR:
        flash('Selected user is not an Author.', 'danger')
        return redirect(url_for('application_manager'))

    # Update the application with the new assignment
    if role_type == 'maker':
        application.maker = new_user.username
        application.maker_id = new_user.id
    elif role_type == 'checker':
        application.checker = new_user.username
        application.checker_id = new_user.id
        # If application is in draft status and being assigned to a checker, update status
        if application.status == LoanApplication.STATUS_DRAFT:
            application.status = LoanApplication.STATUS_PENDING_CHECKER
            application.status_changed_at = datetime.utcnow()
    elif role_type == 'author':
        application.author = new_user.username
        application.author_id = new_user.id
        # If application is in pending checker status and being assigned to an author, update status
        # Only change status to PENDING_AUTHOR if we're in manual mode
        if application.status == LoanApplication.STATUS_PENDING_CHECKER and not WorkflowService.is_auto_mode():
            application.status = LoanApplication.STATUS_PENDING_AUTHOR
            application.status_changed_at = datetime.utcnow()

    # Update the timestamp
    application.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        flash(f'Application {application.application_id} has been reassigned to {new_user.username}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error reassigning application: {str(e)}', 'danger')

    # Redirect back to the application manager with the same search parameters
    return redirect(url_for('application_manager',
                           search_type=request.args.get('search_type'),
                           user_id=request.args.get('user_id'),
                           application_id=request.args.get('application_id')))

@app.route('/add-product', methods=['GET', 'POST'])
@login_required
@role_required('author')  # Only authors can add products
def add_product():
    form = ProductForm()

    if form.validate_on_submit():
        # Check if product code already exists
        existing_product = Product.query.filter_by(code=form.code.data).first()
        if existing_product:
            flash(f'Product code {form.code.data} already exists!', 'danger')
            return render_template('add_edit_product.html', title='Add Product', form=form)

        product = Product(
            code=form.code.data,
            name=form.name.data,
            active=form.active.data
        )

        try:
            db.session.add(product)
            db.session.commit()
            flash(f'Product {product.name} ({product.code}) added successfully!', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')

    return render_template('add_edit_product.html', title='Add Product', form=form)

@app.route('/edit-product/<string:code>', methods=['GET', 'POST'])
@login_required
@role_required('author')  # Only authors can edit products
def edit_product(code):
    product = Product.query.filter_by(code=code).first_or_404()
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        # If code is changed, check if the new code already exists
        if form.code.data != product.code:
            existing_product = Product.query.filter_by(code=form.code.data).first()
            if existing_product:
                flash(f'Product code {form.code.data} already exists!', 'danger')
                return render_template('add_edit_product.html', title='Edit Product', form=form, product=product)

        product.code = form.code.data
        product.name = form.name.data
        product.active = form.active.data

        try:
            db.session.commit()
            flash(f'Product {product.name} ({product.code}) updated successfully!', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')

    return render_template('add_edit_product.html', title='Edit Product', form=form, product=product)

@app.route('/delete-product/<string:code>', methods=['POST'])
@login_required
@role_required('author')  # Only authors can delete products
def delete_product(code):
    product = Product.query.filter_by(code=code).first_or_404()

    # Check if product is in use
    in_use = LoanApplication.query.filter_by(product_type=product.code).first()
    if in_use:
        flash(f'Cannot delete product {product.name} ({product.code}) as it is in use by loan applications!', 'danger')
        return redirect(url_for('products'))

    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Product {product.name} ({product.code}) deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')

    return redirect(url_for('products'))

# Configuration Management Routes
@app.route('/config/manage')
@login_required
@role_required('author')  # Only authors can manage configurations
def manage_config():
    # Get current workflow mode using direct database access
    import sqlite3
    import os

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Connect to the database
    db_path = os.path.join(current_dir, 'optimus.db')
    workflow_mode = 'manual'  # Default

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the system_config table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_config'")
        if cursor.fetchone():
            # Get workflow mode
            cursor.execute("SELECT value FROM system_config WHERE key='WORKFLOW_MODE'")
            result = cursor.fetchone()
            if result:
                workflow_mode = result[0]
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

    print(f"Debug: Current workflow mode from direct DB access: {workflow_mode}")

    # Create workflow config form
    workflow_form = WorkflowConfigForm()
    workflow_form.workflow_mode.data = workflow_mode

    # Create field config form
    field_form = FieldConfigForm()

    # Get all field configurations
    field_configs = FieldService.get_all_field_configs()

    return render_template('config/manage.html',
                           title='Configuration Management',
                           workflow_form=workflow_form,
                           field_form=field_form,
                           field_configs=field_configs)

@app.route('/config/workflow', methods=['POST'])
@login_required
@role_required('author')  # Only authors can manage configurations
def save_workflow_config():
    form = WorkflowConfigForm()

    print(f"Debug: save_workflow_config called")
    print(f"Debug: Form data: {request.form}")
    print(f"Debug: CSRF token valid: {form.csrf_token.validate(form)}")

    if form.validate_on_submit():
        print(f"Debug: Form validated successfully")
        print(f"Debug: Selected workflow mode: {form.workflow_mode.data}")

        # Use our direct fix script to update the workflow mode
        from fix_workflow_mode import update_workflow_mode

        if update_workflow_mode(form.workflow_mode.data):
            print(f"Debug: update_workflow_mode returned True")
            flash('Workflow configuration saved successfully!', 'success')
        else:
            print(f"Debug: update_workflow_mode returned False")
            flash('Error saving workflow configuration.', 'danger')
    else:
        print(f"Debug: Form validation failed")
        print(f"Debug: Form errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('manage_config'))

@app.route('/config/fields', methods=['POST'])
@login_required
@role_required('author')  # Only authors can manage configurations
def save_field_config():
    # Get all field IDs from the form
    field_ids = request.form.getlist('field_ids[]')

    # Update each field configuration
    for field_id in field_ids:
        field_id = int(field_id)

        # Get form values for this field
        is_required = 'is_required_' + str(field_id) in request.form
        is_visible = 'is_visible_' + str(field_id) in request.form
        maker_can_edit = 'maker_can_edit_' + str(field_id) in request.form
        checker_can_edit = 'checker_can_edit_' + str(field_id) in request.form
        author_can_edit = 'author_can_edit_' + str(field_id) in request.form

        # Update field configuration
        FieldService.update_field_config(
            field_id,
            is_required,
            is_visible,
            maker_can_edit,
            checker_can_edit,
            author_can_edit
        )

    flash('Field configurations saved successfully!', 'success')
    return redirect(url_for('manage_config'))

# Route for exporting productivity report
@app.route('/export-productivity-report')
@login_required
@role_required('author')  # Only authors (admin role) can access this report
def export_productivity_report():
    # Get all users
    users = User.query.all()

    # Initialize productivity data structure
    productivity_data = {
        'maker': [],
        'checker': [],
        'author': []
    }

    # Calculate productivity for makers
    for user in users:
        if user.role == ROLE_MAKER:
            # Count all applications created by this maker
            count = LoanApplication.query.filter_by(maker_id=user.id).count()
            productivity_data['maker'].append({
                'username': user.username,
                'count': count
            })
        elif user.role == ROLE_CHECKER:
            # Count all applications processed by this checker (not in pending_checker status)
            count = LoanApplication.query.filter(
                LoanApplication.checker_id == user.id,
                LoanApplication.status != LoanApplication.STATUS_PENDING_CHECKER
            ).count()
            productivity_data['checker'].append({
                'username': user.username,
                'count': count
            })
        elif user.role == ROLE_AUTHOR:
            # Count all applications processed by this author (approved or rejected)
            count = LoanApplication.query.filter(
                LoanApplication.author_id == user.id,
                LoanApplication.status.in_([LoanApplication.STATUS_APPROVED, LoanApplication.STATUS_REJECTED])
            ).count()
            productivity_data['author'].append({
                'username': user.username,
                'count': count
            })

    # Export to Excel
    output, filename = export_productivity_report_to_excel(productivity_data)

    # Return the Excel file
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Initialize configuration models
from models.config import init_db, init_default_configs
from services.field_service import FieldService
from services.workflow_service import WorkflowService

# Initialize the database reference in the config module
init_db(db)

# Create all tables including the newly defined configuration models
with app.app_context():
    db.create_all()
    # Initialize default configurations
    init_default_configs()

# Make WorkflowService available in templates
app.config['WORKFLOW_SERVICE'] = WorkflowService

# API route to get the current workflow mode
@app.route('/api/workflow-mode')
def get_workflow_mode_api():
    mode = WorkflowService.get_workflow_mode()
    return jsonify({
        'mode': mode,
        'is_auto': mode == 'auto',
        'timestamp': datetime.now().isoformat()
    })

# Run the app
if __name__ == '__main__':
    app.run(debug=True)