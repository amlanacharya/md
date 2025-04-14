# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, FloatField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'OADSECRET'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loan_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# Model for Loan Application
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
    maker = db.Column(db.String(100), nullable=False)
    checker = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<LoanApplication {self.application_id}>'

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
    checker = StringField('Checker', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Routes
@app.route('/')
def index():
    loan_applications = LoanApplication.query.all()
    return render_template('index.html', loan_applications=loan_applications)

@app.route('/add', methods=['GET', 'POST'])
def add_loan():
    form = LoanApplicationForm()
    if form.validate_on_submit():
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
            checker=form.checker.data,
            author=form.author.data
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
def edit_loan(id):
    loan_application = LoanApplication.query.get_or_404(id)
    form = LoanApplicationForm(obj=loan_application)
    
    if form.validate_on_submit():
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
        loan_application.maker = form.maker.data
        loan_application.checker = form.checker.data
        loan_application.author = form.author.data
        
        try:
            db.session.commit()
            flash('Loan application updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating loan application: {str(e)}', 'danger')
    
    return render_template('add_edit.html', form=form, title='Edit Loan Application')

@app.route('/delete/<int:id>', methods=['POST'])
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

@app.route('/view/<int:id>')
def view_loan(id):
    loan_application = LoanApplication.query.get_or_404(id)
    return render_template('view.html', loan=loan_application)

# Create all tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)