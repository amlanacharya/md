# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, FloatField, SubmitField, SelectField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length
from flask_wtf.csrf import CSRFProtect
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'OADSECRET'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loan_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_MAKER)
    active = db.Column(db.Boolean, default=True)
    
    def __init__(self, username, email, password, role=ROLE_MAKER):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
    
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

# Model for Loan Application
class LoanApplicationForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    application_id = StringField('Application ID', validators=[DataRequired()])
    customer_name = StringField('Customer Name', validators=[DataRequired()])
    dealer_code = StringField('Dealer Code', validators=[DataRequired()])
    scheme_name = StringField('Scheme Name', validators=[DataRequired()])
    branch_location = StringField('Branch Location', validators=[DataRequired()])
    product_type = StringField('Product Type', validators=[DataRequired()])
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
    # Add approval field
    approve = BooleanField('Approve Application')
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
    
    # Status tracking
    STATUS_DRAFT = 'draft'
    STATUS_PENDING_CHECKER = 'pending_checker'
    STATUS_PENDING_AUTHOR = 'pending_author'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    status = db.Column(db.String(20), nullable=False, default=STATUS_DRAFT)
    
    def __repr__(self):
        return f'<LoanApplication {self.application_id}>'

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
    submit = SubmitField('Register')

# Form for adding/editing loan applications
class LoanApplicationForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    application_id = StringField('Application ID', validators=[DataRequired()])
    customer_name = StringField('Customer Name', validators=[DataRequired()])
    dealer_code = StringField('Dealer Code', validators=[DataRequired()])
    scheme_name = StringField('Scheme Name', validators=[DataRequired()])
    branch_location = StringField('Branch Location', validators=[DataRequired()])
    product_type = StringField('Product Type', validators=[DataRequired()])
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
    # Add approval field
    approve = BooleanField('Approve Application')
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

# Routes
@app.route('/')
@login_required
def index():
    # Filter applications based on role
    if current_user.is_maker():
        # Makers see applications they created
        loan_applications = LoanApplication.query.filter_by(maker_id=current_user.id).all()
    elif current_user.is_checker():
        # Checkers see applications waiting for checker approval and those they've checked
        loan_applications = LoanApplication.query.filter(
            (LoanApplication.status == LoanApplication.STATUS_PENDING_CHECKER) | 
            (LoanApplication.checker_id == current_user.id)
        ).all()
    else:  # Author
        # Authors see all applications
        loan_applications = LoanApplication.query.all()
        
    return render_template('index.html', loan_applications=loan_applications)

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
            if form.checker.data != loan_application.checker or form.author.data != loan_application.author:
                flash('As a Maker, you cannot modify Checker or Author fields.', 'danger')
                return render_template('add_edit.html', form=form, title='Edit Loan Application')
                
        elif current_user.is_checker():
            if form.author.data != loan_application.author:
                flash('As a Checker, you cannot modify the Author field.', 'danger')
                return render_template('add_edit.html', form=form, title='Edit Loan Application')
        
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
            
            # If author approves, change status to approved
            if form.approve.data:
                loan_application.status = LoanApplication.STATUS_APPROVED
                flash('Application has been approved!', 'success')
            
        elif current_user.is_checker():
            loan_application.maker = form.maker.data
            loan_application.checker = form.checker.data or current_user.username
            if form.checker.data == current_user.username or not loan_application.checker:
                loan_application.checker_id = current_user.id
                # If checker approves, move to next stage
                if form.approve.data:
                    loan_application.status = LoanApplication.STATUS_PENDING_AUTHOR
                    flash('Application approved and forwarded to Author!', 'success')
                
        elif current_user.is_maker():
            loan_application.maker = form.maker.data
            if form.maker.data == current_user.username:
                loan_application.maker_id = current_user.id
                loan_application.status = LoanApplication.STATUS_PENDING_CHECKER
        
        try:
            db.session.commit()
            flash('Loan application updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating loan application: {str(e)}', 'danger')
    
    return render_template('add_edit.html', form=form, title='Edit Loan Application')

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
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data
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
    return render_template('users.html', title='Users', users=users)

# Add a route for the user profile
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', title='My Profile')


@app.route('/view/<int:id>')
@login_required
def view_loan(id):
    loan_application = LoanApplication.query.get_or_404(id)
    return render_template('view.html', loan=loan_application)

# Create all tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)