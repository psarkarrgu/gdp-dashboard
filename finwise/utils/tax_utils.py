import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.models import User, TaxDeduction, TaxDeductionType, IncomeSource, Debt, Insurance, Investment
from typing import Dict, List, Optional, Tuple
import datetime
from config import (
    OLD_REGIME_SLABS, NEW_REGIME_SLABS, SURCHARGE_SLABS, 
    CESS_RATE, STANDARD_DEDUCTION, TAX_YEAR
)

def calculate_total_income(user_id: int, db: Session, financial_year: str) -> float:
    """Calculate total income for a user in a specific financial year"""
    # Parse financial year to get start and end dates
    fy_start_year = int(financial_year.split("-")[0])
    fy_end_year = int(financial_year.split("-")[1])
    
    start_date = datetime.date(fy_start_year, 4, 1)
    end_date = datetime.date(fy_end_year, 3, 31)
    
    # Get all income sources for the user
    income_sources = db.query(IncomeSource).filter(
        IncomeSource.user_id == user_id,
        IncomeSource.is_taxable == True,
        IncomeSource.start_date <= end_date,
        (IncomeSource.end_date >= start_date) | (IncomeSource.end_date.is_(None))
    ).all()
    
    total_income = 0.0
    
    for source in income_sources:
        # Calculate income based on frequency
        if source.frequency == "monthly":
            months_active = count_months_active(source.start_date, source.end_date, start_date, end_date)
            total_income += source.amount * months_active
        elif source.frequency == "quarterly":
            quarters_active = count_quarters_active(source.start_date, source.end_date, start_date, end_date)
            total_income += source.amount * quarters_active
        elif source.frequency == "annually":
            years_active = count_years_active(source.start_date, source.end_date, start_date, end_date)
            total_income += source.amount * years_active
        else:
            # Handle one-time income within the financial year
            if start_date <= source.start_date <= end_date:
                total_income += source.amount
    
    return total_income

def count_months_active(source_start: datetime.date, source_end: Optional[datetime.date], 
                        fy_start: datetime.date, fy_end: datetime.date) -> int:
    """Calculate number of months a source was active in a financial year"""
    effective_start = max(source_start, fy_start)
    effective_end = min(source_end or fy_end, fy_end)
    
    if effective_start > effective_end:
        return 0
    
    months = (effective_end.year - effective_start.year) * 12
    months += effective_end.month - effective_start.month
    
    # If source was active for any part of a month, count it as a full month
    if effective_end.day >= effective_start.day:
        months += 1
    
    return months

def count_quarters_active(source_start: datetime.date, source_end: Optional[datetime.date], 
                         fy_start: datetime.date, fy_end: datetime.date) -> int:
    """Calculate number of quarters a source was active in a financial year"""
    months = count_months_active(source_start, source_end, fy_start, fy_end)
    return (months + 2) // 3  # Round up to nearest quarter

def count_years_active(source_start: datetime.date, source_end: Optional[datetime.date], 
                      fy_start: datetime.date, fy_end: datetime.date) -> float:
    """Calculate number of years (possibly fractional) a source was active in a financial year"""
    months = count_months_active(source_start, source_end, fy_start, fy_end)
    return months / 12

def get_tax_deductions(user_id: int, db: Session, financial_year: str) -> Dict[str, float]:
    """Get all tax deductions for a user in a specific financial year"""
    deductions = db.query(TaxDeduction).filter(
        TaxDeduction.user_id == user_id,
        TaxDeduction.financial_year == financial_year
    ).all()
    
    # Initialize deduction categories
    deduction_dict = {
        "80C": 0.0,
        "80D": 0.0,
        "80E": 0.0,
        "80EE": 0.0,
        "80G": 0.0,
        "80CCD": 0.0,
        "HRA": 0.0,
        "LTA": 0.0,
        "HOME_LOAN_INTEREST": 0.0,
        "OTHER": 0.0,
        "STANDARD_DEDUCTION": STANDARD_DEDUCTION
    }
    
    # Populate with actual deductions
    for deduction in deductions:
        if deduction.deduction_type == TaxDeductionType.SEC_80C:
            deduction_dict["80C"] += deduction.amount
        elif deduction.deduction_type == TaxDeductionType.SEC_80D:
            deduction_dict["80D"] += deduction.amount
        elif deduction.deduction_type == TaxDeductionType.SEC_80E:
            deduction_dict["80E"] += deduction.amount
        elif deduction.deduction_type == TaxDeductionType.SEC_80EE:
            deduction_dict["80EE"] += deduction.amount
        elif deduction.deduction_type == TaxDeductionType.SEC_80G:
            deduction_dict["80G"] += deduction.amount
        elif deduction.deduction_type == TaxDeductionType.SEC_80CCD:
            deduction_dict["80CCD"] += deduction.amount
        elif deduction.deduction_type == TaxDeductionType.HRA:
            deduction_dict["HRA"] += deduction.amount
        elif deduction.deduction_type == TaxDeductionType.LTA:
            deduction_dict["LTA"] += deduction.amount
        elif deduction.deduction_type == TaxDeductionType.HOME_LOAN_INTEREST:
            deduction_dict["HOME_LOAN_INTEREST"] += deduction.amount
        elif deduction.deduction_type == TaxDeductionType.OTHER:
            deduction_dict["OTHER"] += deduction.amount
    
    # Cap 80C deductions at 1.5 lakhs
    deduction_dict["80C"] = min(deduction_dict["80C"], 150000)
    
    # Add home loan interest from debts
    parse_year = financial_year.split("-")
    start_date = datetime.date(int(parse_year[0]), 4, 1)
    end_date = datetime.date(int(parse_year[1]), 3, 31)
    
    home_loans = db.query(Debt).filter(
        Debt.user_id == user_id,
        Debt.debt_type == "home_loan",
        Debt.is_tax_deductible == True,
        Debt.start_date <= end_date,
        (Debt.end_date >= start_date) | (Debt.end_date.is_(None))
    ).all()
    
    for loan in home_loans:
        # Calculate interest paid in the financial year
        # Simplified calculation - in real app would be more detailed
        months = count_months_active(loan.start_date, loan.end_date, start_date, end_date)
        if loan.emi_amount and loan.interest_rate:
            yearly_interest = (loan.interest_rate / 100) * loan.remaining_amount
            monthly_interest = yearly_interest / 12
            interest_paid = monthly_interest * months
            deduction_dict["HOME_LOAN_INTEREST"] += interest_paid
    
    # Add insurance premium deductions
    health_insurances = db.query(Insurance).filter(
        Insurance.user_id == user_id,
        Insurance.insurance_type == "health",
        Insurance.is_tax_deductible == True,
        Insurance.start_date <= end_date,
        Insurance.end_date >= start_date
    ).all()
    
    for insurance in health_insurances:
        if insurance.premium_frequency == "annually":
            deduction_dict["80D"] += insurance.premium_amount
        elif insurance.premium_frequency == "monthly":
            deduction_dict["80D"] += insurance.premium_amount * 12
        elif insurance.premium_frequency == "quarterly":
            deduction_dict["80D"] += insurance.premium_amount * 4
    
    return deduction_dict

def calculate_taxable_income_old_regime(gross_income: float, deductions: Dict[str, float]) -> float:
    """Calculate taxable income under the old tax regime with deductions"""
    total_deductions = sum(deductions.values())
    
    # In old regime, we apply all eligible deductions
    taxable_income = max(0, gross_income - total_deductions)
    
    return taxable_income

def calculate_taxable_income_new_regime(gross_income: float) -> float:
    """Calculate taxable income under the new tax regime"""
    # New regime only allows standard deduction and specific deductions
    taxable_income = max(0, gross_income - STANDARD_DEDUCTION)
    
    return taxable_income

def calculate_tax_old_regime(taxable_income: float) -> float:
    """Calculate tax under old regime based on slabs"""
    tax = 0.0
    remaining_income = taxable_income
    
    for slab in OLD_REGIME_SLABS:
        if remaining_income <= 0:
            break
            
        income_in_slab = min(slab["limit"], remaining_income) - (0 if slab == OLD_REGIME_SLABS[0] else OLD_REGIME_SLABS[OLD_REGIME_SLABS.index(slab) - 1]["limit"])
        tax += income_in_slab * slab["rate"]
        remaining_income -= income_in_slab
    
    return tax

def calculate_tax_new_regime(taxable_income: float) -> float:
    """Calculate tax under new regime based on slabs"""
    tax = 0.0
    remaining_income = taxable_income
    
    for slab in NEW_REGIME_SLABS:
        if remaining_income <= 0:
            break
            
        income_in_slab = min(slab["limit"], remaining_income) - (0 if slab == NEW_REGIME_SLABS[0] else NEW_REGIME_SLABS[NEW_REGIME_SLABS.index(slab) - 1]["limit"])
        tax += income_in_slab * slab["rate"]
        remaining_income -= income_in_slab
    
    return tax

def calculate_surcharge(tax_amount: float, taxable_income: float) -> float:
    """Calculate surcharge based on taxable income"""
    surcharge = 0.0
    
    for slab in SURCHARGE_SLABS:
        if taxable_income <= slab["limit"]:
            surcharge = tax_amount * slab["rate"]
            break
    
    return surcharge

def calculate_cess(tax_amount: float, surcharge: float) -> float:
    """Calculate education cess"""
    return (tax_amount + surcharge) * CESS_RATE

def calculate_tax_liability(user_id: int, db: Session, financial_year: str = TAX_YEAR) -> Dict:
    """Calculate tax liability for both old and new regimes"""
    gross_income = calculate_total_income(user_id, db, financial_year)
    deductions = get_tax_deductions(user_id, db, financial_year)
    
    # Old regime calculations
    taxable_income_old = calculate_taxable_income_old_regime(gross_income, deductions)
    tax_old = calculate_tax_old_regime(taxable_income_old)
    surcharge_old = calculate_surcharge(tax_old, taxable_income_old)
    cess_old = calculate_cess(tax_old, surcharge_old)
    total_tax_old = tax_old + surcharge_old + cess_old
    
    # New regime calculations
    taxable_income_new = calculate_taxable_income_new_regime(gross_income)
    tax_new = calculate_tax_new_regime(taxable_income_new)
    surcharge_new = calculate_surcharge(tax_new, taxable_income_new)
    cess_new = calculate_cess(tax_new, surcharge_new)
    total_tax_new = tax_new + surcharge_new + cess_new
    
    # Determine which regime is better
    better_regime = "old" if total_tax_old <= total_tax_new else "new"
    savings = abs(total_tax_old - total_tax_new)
    
    return {
        "financial_year": financial_year,
        "gross_income": gross_income,
        "old_regime": {
            "taxable_income": taxable_income_old,
            "tax": tax_old,
            "surcharge": surcharge_old,
            "cess": cess_old,
            "total_tax": total_tax_old,
            "deductions": deductions
        },
        "new_regime": {
            "taxable_income": taxable_income_new,
            "tax": tax_new,
            "surcharge": surcharge_new,
            "cess": cess_new,
            "total_tax": total_tax_new,
            "deductions": {"STANDARD_DEDUCTION": STANDARD_DEDUCTION}
        },
        "better_regime": better_regime,
        "tax_savings": savings
    }

def calculate_hra_exemption(basic_salary: float, hra_received: float, rent_paid: float, is_metro: bool) -> float:
    """
    Calculate HRA exemption based on:
    1. Actual HRA received
    2. Rent paid in excess of 10% of basic salary
    3. 50% of basic salary (for metro cities) or 40% of basic salary (for non-metro)
    """
    exemption_1 = hra_received
    exemption_2 = rent_paid - (0.1 * basic_salary)
    exemption_2 = max(0, exemption_2)  # Ensure not negative
    exemption_3 = basic_salary * (0.5 if is_metro else 0.4)
    
    return min(exemption_1, exemption_2, exemption_3)

def suggest_tax_saving_investments(user_id: int, db: Session, financial_year: str = TAX_YEAR) -> Dict:
    """Suggest tax-saving investments based on current deductions"""
    deductions = get_tax_deductions(user_id, db, financial_year)
    
    suggestions = {}
    
    # Section 80C - Max 1.5 lakhs
    sec_80c_used = deductions.get("80C", 0)
    sec_80c_remaining = max(0, 150000 - sec_80c_used)
    
    if sec_80c_remaining > 0:
        suggestions["80C"] = {
            "current": sec_80c_used,
            "limit": 150000,
            "remaining": sec_80c_remaining,
            "options": [
                {"name": "PPF", "description": "Public Provident Fund - Long term savings with tax benefits"},
                {"name": "ELSS", "description": "Equity Linked Savings Scheme - Mutual funds with 3 year lock-in"},
                {"name": "Tax-saving FD", "description": "Fixed Deposits with 5 year lock-in period"},
                {"name": "NSC", "description": "National Savings Certificate"},
                {"name": "Life Insurance Premium", "description": "Premium paid for life insurance policies"}
            ]
        }
    
    # Section 80D - Health Insurance
    sec_80d_used = deductions.get("80D", 0)
    sec_80d_limit = 25000  # Basic limit for self and family
    sec_80d_remaining = max(0, sec_80d_limit - sec_80d_used)
    
    if sec_80d_remaining > 0:
        suggestions["80D"] = {
            "current": sec_80d_used,
            "limit": sec_80d_limit,
            "remaining": sec_80d_remaining,
            "options": [
                {"name": "Health Insurance Premium", "description": "Premium for self, spouse, and children"},
                {"name": "Preventive Health Check-up", "description": "Up to ₹5,000 within the overall limit"}
            ]
        }
    
    # Section 80CCD(1B) - Additional NPS contribution
    nps_additional_used = deductions.get("80CCD", 0)
    nps_additional_limit = 50000
    nps_additional_remaining = max(0, nps_additional_limit - nps_additional_used)
    
    if nps_additional_remaining > 0:
        suggestions["80CCD(1B)"] = {
            "current": nps_additional_used,
            "limit": nps_additional_limit,
            "remaining": nps_additional_remaining,
            "options": [
                {"name": "National Pension System (NPS)", "description": "Additional contribution beyond 80C limit"}
            ]
        }
    
    # Home Loan Interest - Section 24
    home_loan_interest_used = deductions.get("HOME_LOAN_INTEREST", 0)
    home_loan_interest_limit = 200000
    home_loan_interest_remaining = max(0, home_loan_interest_limit - home_loan_interest_used)
    
    if home_loan_interest_remaining > 0:
        suggestions["HOME_LOAN_INTEREST"] = {
            "current": home_loan_interest_used,
            "limit": home_loan_interest_limit,
            "remaining": home_loan_interest_remaining,
            "options": [
                {"name": "Home Loan Interest", "description": "Interest paid on home loan for self-occupied property"}
            ]
        }
    
    return suggestions

def generate_tax_timeline(financial_year: str = TAX_YEAR) -> List[Dict]:
    """Generate important tax dates for the financial year"""
    fy_start_year = int(financial_year.split("-")[0])
    fy_end_year = int(financial_year.split("-")[1])
    
    timeline = [
        {
            "date": datetime.date(fy_start_year, 6, 15),
            "title": "Advance Tax - First Installment",
            "description": "Pay 15% of total advance tax"
        },
        {
            "date": datetime.date(fy_start_year, 9, 15),
            "title": "Advance Tax - Second Installment",
            "description": "Pay 45% of total advance tax (cumulative)"
        },
        {
            "date": datetime.date(fy_start_year, 12, 15),
            "title": "Advance Tax - Third Installment",
            "description": "Pay 75% of total advance tax (cumulative)"
        },
        {
            "date": datetime.date(fy_end_year, 3, 15),
            "title": "Advance Tax - Fourth Installment",
            "description": "Pay 100% of total advance tax (cumulative)"
        },
        {
            "date": datetime.date(fy_end_year, 3, 31),
            "title": "Tax-Saving Investments Deadline",
            "description": "Last date to make tax-saving investments for the financial year"
        },
        {
            "date": datetime.date(fy_end_year, 7, 31),
            "title": "Income Tax Return Filing - Non-Audit Cases",
            "description": "Last date for filing ITR for individuals not requiring tax audit"
        }
    ]
    
    return timeline