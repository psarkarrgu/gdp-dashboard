from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    date_of_birth = Column(Date)
    phone_number = Column(String(20))
    pan_number = Column(String(10))
    aadhar_number = Column(String(12))
    profile_picture = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    tax_regime = Column(String(10), default="old")  # 'old' or 'new'
    preferences = Column(JSON)

    income_sources = relationship("IncomeSource", back_populates="user", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    investments = relationship("Investment", back_populates="user", cascade="all, delete-orphan")
    debts = relationship("Debt", back_populates="user", cascade="all, delete-orphan")
    financial_goals = relationship("FinancialGoal", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    insurance_policies = relationship("Insurance", back_populates="user", cascade="all, delete-orphan")
    tax_deductions = relationship("TaxDeduction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    financial_calendar_events = relationship("FinancialCalendarEvent", back_populates="user", cascade="all, delete-orphan")

class IncomeSourceType(enum.Enum):
    SALARY = "salary"
    FREELANCE = "freelance"
    BUSINESS = "business"
    RENTAL = "rental"
    INVESTMENT = "investment"
    OTHER = "other"

class IncomeSource(Base):
    __tablename__ = "income_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    source_type = Column(Enum(IncomeSourceType), nullable=False)
    amount = Column(Float, nullable=False)
    frequency = Column(String(20), nullable=False)  # monthly, quarterly, annually
    is_taxable = Column(Boolean, default=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # For salary income
    basic_pay = Column(Float)
    hra = Column(Float)
    special_allowance = Column(Float)
    transport_allowance = Column(Float)
    medical_allowance = Column(Float)
    professional_tax = Column(Float)
    other_allowances = Column(JSON)
    
    user = relationship("User", back_populates="income_sources")
    income_transactions = relationship("IncomeTransaction", back_populates="income_source", cascade="all, delete-orphan")

class IncomeTransaction(Base):
    __tablename__ = "income_transactions"

    id = Column(Integer, primary_key=True, index=True)
    income_source_id = Column(Integer, ForeignKey("income_sources.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    income_source = relationship("IncomeSource", back_populates="income_transactions")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text)
    is_recurring = Column(Boolean, default=False)
    frequency = Column(String(20))  # daily, weekly, monthly, yearly
    payment_method = Column(String(50))
    receipt_image = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="expenses")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    period = Column(String(20), nullable=False)  # monthly, quarterly, annually
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="budgets")

class InvestmentType(enum.Enum):
    EQUITY = "equity"
    MUTUAL_FUND = "mutual_fund"
    FIXED_DEPOSIT = "fixed_deposit"
    PPF = "ppf"
    EPF = "epf"
    NPS = "nps"
    ELSS = "elss"
    BONDS = "bonds"
    GOLD = "gold"
    REAL_ESTATE = "real_estate"
    CRYPTOCURRENCY = "cryptocurrency"
    OTHER = "other"

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    investment_type = Column(Enum(InvestmentType), nullable=False)
    amount = Column(Float, nullable=False)
    current_value = Column(Float)
    purchase_date = Column(Date, nullable=False)
    maturity_date = Column(Date)
    interest_rate = Column(Float)
    is_tax_saving = Column(Boolean, default=False)
    tax_section = Column(String(20))  # 80C, 80D, etc.
    is_sip = Column(Boolean, default=False)
    sip_amount = Column(Float)
    sip_frequency = Column(String(20))  # monthly, quarterly, etc.
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="investments")

class DebtType(enum.Enum):
    HOME_LOAN = "home_loan"
    CAR_LOAN = "car_loan"
    PERSONAL_LOAN = "personal_loan"
    EDUCATION_LOAN = "education_loan"
    CREDIT_CARD = "credit_card"
    OTHER = "other"

class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    debt_type = Column(Enum(DebtType), nullable=False)
    principal_amount = Column(Float, nullable=False)
    remaining_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    emi_amount = Column(Float)
    lender = Column(String(100))
    is_tax_deductible = Column(Boolean, default=False)
    tax_section = Column(String(20))  # 24, 80E, etc.
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="debts")

class FinancialGoalType(enum.Enum):
    RETIREMENT = "retirement"
    EMERGENCY_FUND = "emergency_fund"
    HOME_PURCHASE = "home_purchase"
    EDUCATION = "education"
    VEHICLE = "vehicle"
    WEDDING = "wedding"
    VACATION = "vacation"
    BUSINESS = "business"
    OTHER = "other"

class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    goal_type = Column(Enum(FinancialGoalType), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0)
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)
    priority = Column(Integer, default=1)  # 1: High, 2: Medium, 3: Low
    is_completed = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="financial_goals")

class DocumentType(enum.Enum):
    FORM_16 = "form_16"
    ITR = "itr"
    INVESTMENT_PROOF = "investment_proof"
    INSURANCE_POLICY = "insurance_policy"
    PROPERTY_DOCUMENT = "property_document"
    IDENTITY_DOCUMENT = "identity_document"
    OTHER = "other"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    file_path = Column(String(255), nullable=False)
    upload_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    financial_year = Column(String(10))
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="documents")

class InsuranceType(enum.Enum):
    LIFE = "life"
    HEALTH = "health"
    CAR = "car"
    TWO_WHEELER = "two_wheeler"
    HOME = "home"
    TRAVEL = "travel"
    CRITICAL_ILLNESS = "critical_illness"
    TERM = "term"
    OTHER = "other"

class Insurance(Base):
    __tablename__ = "insurance_policies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    insurance_type = Column(Enum(InsuranceType), nullable=False)
    policy_number = Column(String(50), nullable=False)
    provider = Column(String(100), nullable=False)
    premium_amount = Column(Float, nullable=False)
    sum_assured = Column(Float, nullable=False)
    premium_frequency = Column(String(20), nullable=False)  # monthly, quarterly, annually
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    renewal_date = Column(Date, nullable=False)
    is_tax_deductible = Column(Boolean, default=False)
    tax_section = Column(String(20))  # 80C, 80D, etc.
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="insurance_policies")

class TaxDeductionType(enum.Enum):
    SEC_80C = "80c"
    SEC_80D = "80d"
    SEC_80E = "80e"
    SEC_80EE = "80ee"
    SEC_80G = "80g"
    SEC_80CCD = "80ccd"
    HRA = "hra"
    LTA = "lta"
    HOME_LOAN_INTEREST = "home_loan_interest"
    OTHER = "other"

class TaxDeduction(Base):
    __tablename__ = "tax_deductions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deduction_type = Column(Enum(TaxDeductionType), nullable=False)
    amount = Column(Float, nullable=False)
    financial_year = Column(String(10), nullable=False)
    description = Column(Text)
    proof_document_id = Column(Integer, ForeignKey("documents.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="tax_deductions")
    proof_document = relationship("Document")

class NotificationPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    read_at = Column(DateTime)
    
    user = relationship("User", back_populates="notifications")

class EventType(enum.Enum):
    TAX_DUE = "tax_due"
    INSURANCE_PREMIUM = "insurance_premium"
    SIP_INVESTMENT = "sip_investment"
    LOAN_EMI = "loan_emi"
    FINANCIAL_REVIEW = "financial_review"
    BILL_PAYMENT = "bill_payment"
    OTHER = "other"

class FinancialCalendarEvent(Base):
    __tablename__ = "financial_calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    event_date = Column(Date, nullable=False)
    is_recurring = Column(Boolean, default=False)
    frequency = Column(String(20))  # daily, weekly, monthly, yearly
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="financial_calendar_events")