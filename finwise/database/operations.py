from sqlalchemy.orm import Session
import bcrypt
import datetime
from sqlalchemy import func, desc, and_
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import (
    User, IncomeSource, IncomeTransaction, Expense, Budget, Investment, Debt,
    FinancialGoal, Document, Insurance, TaxDeduction, Notification, FinancialCalendarEvent
)

# User operations
def create_user(db: Session, email: str, username: str, password: str, 
                first_name: str = None, last_name: str = None, date_of_birth: datetime.date = None, 
                phone_number: str = None, pan_number: str = None, aadhar_number: str = None):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db_user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        phone_number=phone_number,
        pan_number=pan_number,
        aadhar_number=aadhar_number,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def update_user_login(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_login = datetime.datetime.now()
        db.commit()
        db.refresh(user)
    return user

def update_user_profile(db: Session, user_id: int, **kwargs):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

# Income operations
def create_income_source(db: Session, user_id: int, name: str, source_type: str, 
                         amount: float, frequency: str, is_taxable: bool, start_date: datetime.date, 
                         end_date: datetime.date = None, description: str = None, **kwargs):
    db_income_source = IncomeSource(
        user_id=user_id,
        name=name,
        source_type=source_type,
        amount=amount,
        frequency=frequency,
        is_taxable=is_taxable,
        start_date=start_date,
        end_date=end_date,
        description=description,
        **kwargs
    )
    db.add(db_income_source)
    db.commit()
    db.refresh(db_income_source)
    return db_income_source

def get_income_sources(db: Session, user_id: int):
    return db.query(IncomeSource).filter(IncomeSource.user_id == user_id).all()

def get_income_source(db: Session, income_source_id: int, user_id: int):
    return db.query(IncomeSource).filter(
        IncomeSource.id == income_source_id,
        IncomeSource.user_id == user_id
    ).first()

def update_income_source(db: Session, income_source_id: int, user_id: int, **kwargs):
    income_source = db.query(IncomeSource).filter(
        IncomeSource.id == income_source_id,
        IncomeSource.user_id == user_id
    ).first()
    if income_source:
        for key, value in kwargs.items():
            if hasattr(income_source, key):
                setattr(income_source, key, value)
        db.commit()
        db.refresh(income_source)
    return income_source

def delete_income_source(db: Session, income_source_id: int, user_id: int):
    income_source = db.query(IncomeSource).filter(
        IncomeSource.id == income_source_id,
        IncomeSource.user_id == user_id
    ).first()
    if income_source:
        db.delete(income_source)
        db.commit()
        return True
    return False

def create_income_transaction(db: Session, income_source_id: int, amount: float, 
                              date: datetime.date, description: str = None):
    db_transaction = IncomeTransaction(
        income_source_id=income_source_id,
        amount=amount,
        date=date,
        description=description
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_income_transactions(db: Session, user_id: int, start_date=None, end_date=None):
    query = db.query(IncomeTransaction).join(IncomeSource).filter(IncomeSource.user_id == user_id)
    
    if start_date:
        query = query.filter(IncomeTransaction.date >= start_date)
    
    if end_date:
        query = query.filter(IncomeTransaction.date <= end_date)
        
    return query.order_by(IncomeTransaction.date.desc()).all()

# Expense operations
def create_expense(db: Session, user_id: int, category: str, amount: float, 
                  date: datetime.date, description: str = None, is_recurring: bool = False, 
                  frequency: str = None, payment_method: str = None, receipt_image: str = None):
    db_expense = Expense(
        user_id=user_id,
        category=category,
        amount=amount,
        date=date,
        description=description,
        is_recurring=is_recurring,
        frequency=frequency,
        payment_method=payment_method,
        receipt_image=receipt_image
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def get_expenses(db: Session, user_id: int, start_date=None, end_date=None, category=None):
    query = db.query(Expense).filter(Expense.user_id == user_id)
    
    if start_date:
        query = query.filter(Expense.date >= start_date)
    
    if end_date:
        query = query.filter(Expense.date <= end_date)
    
    if category:
        query = query.filter(Expense.category == category)
        
    return query.order_by(Expense.date.desc()).all()

def get_expense(db: Session, expense_id: int, user_id: int):
    return db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()

def update_expense(db: Session, expense_id: int, user_id: int, **kwargs):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()
    if expense:
        for key, value in kwargs.items():
            if hasattr(expense, key):
                setattr(expense, key, value)
        db.commit()
        db.refresh(expense)
    return expense

def delete_expense(db: Session, expense_id: int, user_id: int):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()
    if expense:
        db.delete(expense)
        db.commit()
        return True
    return False

# Budget operations
def create_budget(db: Session, user_id: int, category: str, amount: float, 
                 period: str, start_date: datetime.date, end_date: datetime.date = None):
    db_budget = Budget(
        user_id=user_id,
        category=category,
        amount=amount,
        period=period,
        start_date=start_date,
        end_date=end_date
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

def get_budgets(db: Session, user_id: int, period=None):
    query = db.query(Budget).filter(Budget.user_id == user_id)
    
    if period:
        query = query.filter(Budget.period == period)
        
    return query.all()

def get_budget(db: Session, budget_id: int, user_id: int):
    return db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()

def update_budget(db: Session, budget_id: int, user_id: int, **kwargs):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()
    if budget:
        for key, value in kwargs.items():
            if hasattr(budget, key):
                setattr(budget, key, value)
        db.commit()
        db.refresh(budget)
    return budget

def delete_budget(db: Session, budget_id: int, user_id: int):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()
    if budget:
        db.delete(budget)
        db.commit()
        return True
    return False

# Investment operations
def create_investment(db: Session, user_id: int, name: str, investment_type: str, 
                     amount: float, purchase_date: datetime.date, maturity_date: datetime.date = None,
                     interest_rate: float = None, is_tax_saving: bool = False, 
                     tax_section: str = None, is_sip: bool = False, sip_amount: float = None,
                     sip_frequency: str = None, description: str = None):
    db_investment = Investment(
        user_id=user_id,
        name=name,
        investment_type=investment_type,
        amount=amount,
        current_value=amount,
        purchase_date=purchase_date,
        maturity_date=maturity_date,
        interest_rate=interest_rate,
        is_tax_saving=is_tax_saving,
        tax_section=tax_section,
        is_sip=is_sip,
        sip_amount=sip_amount,
        sip_frequency=sip_frequency,
        description=description
    )
    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    return db_investment

def get_investments(db: Session, user_id: int, investment_type=None, is_tax_saving=None):
    query = db.query(Investment).filter(Investment.user_id == user_id)
    
    if investment_type:
        query = query.filter(Investment.investment_type == investment_type)
    
    if is_tax_saving is not None:
        query = query.filter(Investment.is_tax_saving == is_tax_saving)
        
    return query.all()

def get_investment(db: Session, investment_id: int, user_id: int):
    return db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == user_id
    ).first()

def update_investment(db: Session, investment_id: int, user_id: int, **kwargs):
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == user_id
    ).first()
    if investment:
        for key, value in kwargs.items():
            if hasattr(investment, key):
                setattr(investment, key, value)
        db.commit()
        db.refresh(investment)
    return investment

def delete_investment(db: Session, investment_id: int, user_id: int):
    investment = db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == user_id
    ).first()
    if investment:
        db.delete(investment)
        db.commit()
        return True
    return False

# Debt operations
def create_debt(db: Session, user_id: int, name: str, debt_type: str, principal_amount: float,
               remaining_amount: float, interest_rate: float, start_date: datetime.date,
               end_date: datetime.date = None, emi_amount: float = None, lender: str = None,
               is_tax_deductible: bool = False, tax_section: str = None, description: str = None):
    db_debt = Debt(
        user_id=user_id,
        name=name,
        debt_type=debt_type,
        principal_amount=principal_amount,
        remaining_amount=remaining_amount,
        interest_rate=interest_rate,
        start_date=start_date,
        end_date=end_date,
        emi_amount=emi_amount,
        lender=lender,
        is_tax_deductible=is_tax_deductible,
        tax_section=tax_section,
        description=description
    )
    db.add(db_debt)
    db.commit()
    db.refresh(db_debt)
    return db_debt

def get_debts(db: Session, user_id: int, debt_type=None, is_tax_deductible=None):
    query = db.query(Debt).filter(Debt.user_id == user_id)
    
    if debt_type:
        query = query.filter(Debt.debt_type == debt_type)
    
    if is_tax_deductible is not None:
        query = query.filter(Debt.is_tax_deductible == is_tax_deductible)
        
    return query.all()

def get_debt(db: Session, debt_id: int, user_id: int):
    return db.query(Debt).filter(
        Debt.id == debt_id,
        Debt.user_id == user_id
    ).first()

def update_debt(db: Session, debt_id: int, user_id: int, **kwargs):
    debt = db.query(Debt).filter(
        Debt.id == debt_id,
        Debt.user_id == user_id
    ).first()
    if debt:
        for key, value in kwargs.items():
            if hasattr(debt, key):
                setattr(debt, key, value)
        db.commit()
        db.refresh(debt)
    return debt

def delete_debt(db: Session, debt_id: int, user_id: int):
    debt = db.query(Debt).filter(
        Debt.id == debt_id,
        Debt.user_id == user_id
    ).first()
    if debt:
        db.delete(debt)
        db.commit()
        return True
    return False

# Financial Goal operations
def create_financial_goal(db: Session, user_id: int, name: str, goal_type: str, 
                         target_amount: float, current_amount: float, start_date: datetime.date,
                         target_date: datetime.date, priority: int = 1, description: str = None):
    db_goal = FinancialGoal(
        user_id=user_id,
        name=name,
        goal_type=goal_type,
        target_amount=target_amount,
        current_amount=current_amount,
        start_date=start_date,
        target_date=target_date,
        priority=priority,
        description=description
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def get_financial_goals(db: Session, user_id: int, goal_type=None, is_completed=None):
    query = db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id)
    
    if goal_type:
        query = query.filter(FinancialGoal.goal_type == goal_type)
    
    if is_completed is not None:
        query = query.filter(FinancialGoal.is_completed == is_completed)
        
    return query.order_by(FinancialGoal.priority).all()

def get_financial_goal(db: Session, goal_id: int, user_id: int):
    return db.query(FinancialGoal).filter(
        FinancialGoal.id == goal_id,
        FinancialGoal.user_id == user_id
    ).first()

def update_financial_goal(db: Session, goal_id: int, user_id: int, **kwargs):
    goal = db.query(FinancialGoal).filter(
        FinancialGoal.id == goal_id,
        FinancialGoal.user_id == user_id
    ).first()
    if goal:
        for key, value in kwargs.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
        db.commit()
        db.refresh(goal)
    return goal

def delete_financial_goal(db: Session, goal_id: int, user_id: int):
    goal = db.query(FinancialGoal).filter(
        FinancialGoal.id == goal_id,
        FinancialGoal.user_id == user_id
    ).first()
    if goal:
        db.delete(goal)
        db.commit()
        return True
    return False

# Document operations
def create_document(db: Session, user_id: int, name: str, document_type: str, 
                   file_path: str, upload_date: datetime.date, expiry_date: datetime.date = None,
                   financial_year: str = None, description: str = None):
    db_document = Document(
        user_id=user_id,
        name=name,
        document_type=document_type,
        file_path=file_path,
        upload_date=upload_date,
        expiry_date=expiry_date,
        financial_year=financial_year,
        description=description
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_documents(db: Session, user_id: int, document_type=None, financial_year=None):
    query = db.query(Document).filter(Document.user_id == user_id)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    
    if financial_year:
        query = query.filter(Document.financial_year == financial_year)
        
    return query.order_by(Document.upload_date.desc()).all()

def get_document(db: Session, document_id: int, user_id: int):
    return db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()

def update_document(db: Session, document_id: int, user_id: int, **kwargs):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()
    if document:
        for key, value in kwargs.items():
            if hasattr(document, key):
                setattr(document, key, value)
        db.commit()
        db.refresh(document)
    return document

def delete_document(db: Session, document_id: int, user_id: int):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()
    if document:
        db.delete(document)
        db.commit()
        return True
    return False

# Insurance operations
def create_insurance(db: Session, user_id: int, name: str, insurance_type: str, 
                    policy_number: str, provider: str, premium_amount: float,
                    sum_assured: float, premium_frequency: str, start_date: datetime.date,
                    end_date: datetime.date, renewal_date: datetime.date,
                    is_tax_deductible: bool = False, tax_section: str = None, 
                    description: str = None):
    db_insurance = Insurance(
        user_id=user_id,
        name=name,
        insurance_type=insurance_type,
        policy_number=policy_number,
        provider=provider,
        premium_amount=premium_amount,
        sum_assured=sum_assured,
        premium_frequency=premium_frequency,
        start_date=start_date,
        end_date=end_date,
        renewal_date=renewal_date,
        is_tax_deductible=is_tax_deductible,
        tax_section=tax_section,
        description=description
    )
    db.add(db_insurance)
    db.commit()
    db.refresh(db_insurance)
    return db_insurance

def get_insurances(db: Session, user_id: int, insurance_type=None, is_tax_deductible=None):
    query = db.query(Insurance).filter(Insurance.user_id == user_id)
    
    if insurance_type:
        query = query.filter(Insurance.insurance_type == insurance_type)
    
    if is_tax_deductible is not None:
        query = query.filter(Insurance.is_tax_deductible == is_tax_deductible)
        
    return query.all()

def get_insurance(db: Session, insurance_id: int, user_id: int):
    return db.query(Insurance).filter(
        Insurance.id == insurance_id,
        Insurance.user_id == user_id
    ).first()

def update_insurance(db: Session, insurance_id: int, user_id: int, **kwargs):
    insurance = db.query(Insurance).filter(
        Insurance.id == insurance_id,
        Insurance.user_id == user_id
    ).first()
    if insurance:
        for key, value in kwargs.items():
            if hasattr(insurance, key):
                setattr(insurance, key, value)
        db.commit()
        db.refresh(insurance)
    return insurance

def delete_insurance(db: Session, insurance_id: int, user_id: int):
    insurance = db.query(Insurance).filter(
        Insurance.id == insurance_id,
        Insurance.user_id == user_id
    ).first()
    if insurance:
        db.delete(insurance)
        db.commit()
        return True
    return False

# Tax Deduction operations
def create_tax_deduction(db: Session, user_id: int, deduction_type: str, 
                        amount: float, financial_year: str, description: str = None,
                        proof_document_id: int = None):
    db_deduction = TaxDeduction(
        user_id=user_id,
        deduction_type=deduction_type,
        amount=amount,
        financial_year=financial_year,
        description=description,
        proof_document_id=proof_document_id
    )
    db.add(db_deduction)
    db.commit()
    db.refresh(db_deduction)
    return db_deduction

def get_tax_deductions(db: Session, user_id: int, deduction_type=None, financial_year=None):
    query = db.query(TaxDeduction).filter(TaxDeduction.user_id == user_id)
    
    if deduction_type:
        query = query.filter(TaxDeduction.deduction_type == deduction_type)
    
    if financial_year:
        query = query.filter(TaxDeduction.financial_year == financial_year)
        
    return query.all()

def get_tax_deduction(db: Session, deduction_id: int, user_id: int):
    return db.query(TaxDeduction).filter(
        TaxDeduction.id == deduction_id,
        TaxDeduction.user_id == user_id
    ).first()

def update_tax_deduction(db: Session, deduction_id: int, user_id: int, **kwargs):
    deduction = db.query(TaxDeduction).filter(
        TaxDeduction.id == deduction_id,
        TaxDeduction.user_id == user_id
    ).first()
    if deduction:
        for key, value in kwargs.items():
            if hasattr(deduction, key):
                setattr(deduction, key, value)
        db.commit()
        db.refresh(deduction)
    return deduction

def delete_tax_deduction(db: Session, deduction_id: int, user_id: int):
    deduction = db.query(TaxDeduction).filter(
        TaxDeduction.id == deduction_id,
        TaxDeduction.user_id == user_id
    ).first()
    if deduction:
        db.delete(deduction)
        db.commit()
        return True
    return False

# Notification operations
def create_notification(db: Session, user_id: int, title: str, message: str, priority: str = "medium"):
    db_notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        priority=priority
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notifications(db: Session, user_id: int, is_read=None, limit=None):
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
        
    query = query.order_by(Notification.created_at.desc())
    
    if limit:
        query = query.limit(limit)
        
    return query.all()

def mark_notification_as_read(db: Session, notification_id: int, user_id: int):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    if notification:
        notification.is_read = True
        notification.read_at = datetime.datetime.now()
        db.commit()
        db.refresh(notification)
    return notification

def delete_notification(db: Session, notification_id: int, user_id: int):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    if notification:
        db.delete(notification)
        db.commit()
        return True
    return False

# Financial Calendar Event operations
def create_financial_calendar_event(db: Session, user_id: int, title: str, event_type: str,
                                  event_date: datetime.date, is_recurring: bool = False,
                                  frequency: str = None, description: str = None):
    db_event = FinancialCalendarEvent(
        user_id=user_id,
        title=title,
        event_type=event_type,
        event_date=event_date,
        is_recurring=is_recurring,
        frequency=frequency,
        description=description
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_financial_calendar_events(db: Session, user_id: int, event_type=None, start_date=None, end_date=None):
    query = db.query(FinancialCalendarEvent).filter(FinancialCalendarEvent.user_id == user_id)
    
    if event_type:
        query = query.filter(FinancialCalendarEvent.event_type == event_type)
    
    if start_date:
        query = query.filter(FinancialCalendarEvent.event_date >= start_date)
        
    if end_date:
        query = query.filter(FinancialCalendarEvent.event_date <= end_date)
        
    return query.order_by(FinancialCalendarEvent.event_date).all()

def get_financial_calendar_event(db: Session, event_id: int, user_id: int):
    return db.query(FinancialCalendarEvent).filter(
        FinancialCalendarEvent.id == event_id,
        FinancialCalendarEvent.user_id == user_id
    ).first()

def update_financial_calendar_event(db: Session, event_id: int, user_id: int, **kwargs):
    event = db.query(FinancialCalendarEvent).filter(
        FinancialCalendarEvent.id == event_id,
        FinancialCalendarEvent.user_id == user_id
    ).first()
    if event:
        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)
        db.commit()
        db.refresh(event)
    return event

def delete_financial_calendar_event(db: Session, event_id: int, user_id: int):
    event = db.query(FinancialCalendarEvent).filter(
        FinancialCalendarEvent.id == event_id,
        FinancialCalendarEvent.user_id == user_id
    ).first()
    if event:
        db.delete(event)
        db.commit()
        return True
    return False