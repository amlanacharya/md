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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'OADSECRET'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loan_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Application configuration
app.config['ENABLE_PRODUCT_EXPERTISE'] = False  # Set to True to enable product expertise feature

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

# Product type constants
PRODUCT_PL = 'PL'  # Personal Loan
PRODUCT_TW = 'TW'  # Two Wheeler
PRODUCT_UTW = 'UTW'  # Used Two Wheeler
PRODUCT_UC = 'UC'  # Used Car

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
    product_type = SelectField('Product Type', validators=[DataRequired()], choices=[
        (PRODUCT_PL, 'Personal Loan (PL)'),
        (PRODUCT_TW, 'Two Wheeler (TW)'),
        (PRODUCT_UTW, 'Used Two Wheeler (UTW)'),
        (PRODUCT_UC, 'Used Car (UC)')
    ])
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
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(LoanApplicationForm, self).__init__(*args, **kwargs)

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

# Routes
@app.route('/')
@app.route('/page/<int:page>')
@login_required
def index(page=1):
    # Get filter parameters
    status_filter = request.args.get('status', '')
    search_term = request.args.get('search', '')
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

    # Order by most recent first
    query = query.order_by(LoanApplication.updated_at.desc())

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
                return render_template('add_edit.html', form=form, title='Add Loan Application')

        elif current_user.is_checker():
            if form.author.data:
                flash('As a Checker, you cannot set the Author field.', 'danger')
                return render_template('add_edit.html', form=form, title='Add Loan Application')

        # Set initial status based on role
        if current_user.is_maker():
            status = LoanApplication.STATUS_PENDING_CHECKER
        elif current_user.is_checker():
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
            flash('Loan application added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding loan application: {str(e)}', 'danger')

    return render_template('add_edit.html', form=form, title='Add Loan Application')

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
                return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application)

        elif current_user.is_checker():
            # Only check for author field modification if both values are not empty
            if form.author.data and loan_application.author and form.author.data != loan_application.author:
                flash('As a Checker, you cannot modify the Author field.', 'danger')
                return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application)

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

            # Handle approval or rejection
            if form.approve.data and form.reject.data:
                flash('Cannot both approve and reject an application.', 'danger')
                return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application)
            elif form.approve.data:
                loan_application.status = LoanApplication.STATUS_APPROVED
                loan_application.status_changed_at = datetime.utcnow()
                flash('Application has been approved!', 'success')
            elif form.reject.data:
                if not form.rejection_reason.data:
                    flash('Rejection reason is required when rejecting an application.', 'danger')
                    return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application)
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

                # Handle approval or rejection
                if form.approve.data and form.reject.data:
                    flash('Cannot both approve and reject an application.', 'danger')
                    return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application)
                elif form.approve.data:
                    loan_application.status = LoanApplication.STATUS_PENDING_AUTHOR
                    loan_application.status_changed_at = datetime.utcnow()
                    flash('Application approved and forwarded to Author!', 'success')
                elif form.reject.data:
                    if not form.rejection_reason.data:
                        flash('Rejection reason is required when rejecting an application.', 'danger')
                        return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application)
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
                loan_application.status = LoanApplication.STATUS_PENDING_CHECKER
                loan_application.status_changed_at = datetime.utcnow()

        try:
            db.session.commit()
            flash('Loan application updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating loan application: {str(e)}', 'danger')

    return render_template('add_edit.html', form=form, title='Edit Loan Application', loan_application=loan_application)

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
@app.route('/export-all-cases')
@login_required
def export_all_cases():
    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'updated_at')
    sort_order = request.args.get('sort_order', 'desc')
    status_filter = request.args.get('status', '')
    search_term = request.args.get('search', '')

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

    # Get all applications
    applications = query.all()

    # Determine which fields to include based on user role
    include_checker = current_user.is_checker() or current_user.is_author()
    include_author = current_user.is_author()
    include_rejection = current_user.is_author()

    # Export to Excel
    output, filename = export_applications_to_excel(
        applications=applications,
        filename_prefix='all_cases',
        include_checker=include_checker,
        include_author=include_author,
        include_rejection=include_rejection
    )

    # Return the Excel file
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

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

# Create all tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)