import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.models import (
    User, IncomeSource, Expense, Budget, Investment, Debt,
    FinancialGoal, Insurance
)
import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, extract, and_

def calculate_net_worth(user_id: int, db: Session) -> Dict:
    """Calculate the net worth for a user"""
    # Calculate total assets
    investments = db.query(Investment).filter(
        Investment.user_id == user_id
    ).all()
    
    total_assets = sum(investment.current_value or investment.amount for investment in investments)
    
    # Calculate total liabilities
    debts = db.query(Debt).filter(
        Debt.user_id == user_id
    ).all()
    
    total_liabilities = sum(debt.remaining_amount for debt in debts)
    
    # Calculate net worth
    net_worth = total_assets - total_liabilities
    
    return {
        "assets": total_assets,
        "liabilities": total_liabilities,
        "net_worth": net_worth
    }

def calculate_monthly_income(user_id: int, db: Session, month: int, year: int) -> float:
    """Calculate total income for a specific month"""
    start_date = datetime.date(year, month, 1)
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    
    # Get monthly income sources
    monthly_sources = db.query(IncomeSource).filter(
        IncomeSource.user_id == user_id,
        IncomeSource.frequency == "monthly",
        IncomeSource.start_date <= end_date,
        (IncomeSource.end_date >= start_date) | (IncomeSource.end_date.is_(None))
    ).all()
    
    monthly_income = sum(source.amount for source in monthly_sources)
    
    # Get quarterly income sources (1/3 per month)
    quarterly_sources = db.query(IncomeSource).filter(
        IncomeSource.user_id == user_id,
        IncomeSource.frequency == "quarterly",
        IncomeSource.start_date <= end_date,
        (IncomeSource.end_date >= start_date) | (IncomeSource.end_date.is_(None))
    ).all()
    
    quarterly_income = sum(source.amount for source in quarterly_sources) / 3
    
    # Get annual income sources (1/12 per month)
    annual_sources = db.query(IncomeSource).filter(
        IncomeSource.user_id == user_id,
        IncomeSource.frequency == "annually",
        IncomeSource.start_date <= end_date,
        (IncomeSource.end_date >= start_date) | (IncomeSource.end_date.is_(None))
    ).all()
    
    annual_income = sum(source.amount for source in annual_sources) / 12
    
    # Get one-time income in this month
    one_time_sources = db.query(IncomeSource).filter(
        IncomeSource.user_id == user_id,
        IncomeSource.frequency == "one-time",
        extract('month', IncomeSource.start_date) == month,
        extract('year', IncomeSource.start_date) == year
    ).all()
    
    one_time_income = sum(source.amount for source in one_time_sources)
    
    return monthly_income + quarterly_income + annual_income + one_time_income

def calculate_monthly_expenses(user_id: int, db: Session, month: int, year: int) -> float:
    """Calculate total expenses for a specific month"""
    start_date = datetime.date(year, month, 1)
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    
    # Get all expenses in the month
    expenses = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()
    
    # Sum all expenses
    return sum(expense.amount for expense in expenses)

def calculate_savings_rate(user_id: int, db: Session, month: int, year: int) -> float:
    """Calculate savings rate (savings / income) for a specific month"""
    income = calculate_monthly_income(user_id, db, month, year)
    expenses = calculate_monthly_expenses(user_id, db, month, year)
    
    if income == 0:
        return 0
    
    savings = income - expenses
    savings_rate = (savings / income) * 100
    
    return max(0, savings_rate)

def calculate_debt_to_income_ratio(user_id: int, db: Session) -> float:
    """Calculate debt-to-income ratio"""
    # Get monthly income
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    monthly_income = calculate_monthly_income(user_id, db, current_month, current_year)
    
    if monthly_income == 0:
        return float('inf')
    
    # Get monthly debt payments
    debts = db.query(Debt).filter(
        Debt.user_id == user_id
    ).all()
    
    monthly_debt_payments = sum(debt.emi_amount or 0 for debt in debts)
    
    # Calculate ratio
    debt_to_income_ratio = (monthly_debt_payments / monthly_income) * 100
    
    return debt_to_income_ratio

def calculate_emergency_fund_status(user_id: int, db: Session) -> Dict:
    """Calculate emergency fund status"""
    # Get monthly expenses (average of last 3 months)
    current_date = datetime.datetime.now().date()
    three_months_ago = current_date - datetime.timedelta(days=90)
    
    expenses = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.date >= three_months_ago,
        Expense.date <= current_date
    ).all()
    
    if not expenses:
        return {"status": "unknown", "months_covered": 0, "target_months": 6}
    
    total_expenses = sum(expense.amount for expense in expenses)
    avg_monthly_expenses = total_expenses / 3
    
    # Get emergency fund goal
    emergency_fund_goal = db.query(FinancialGoal).filter(
        FinancialGoal.user_id == user_id,
        FinancialGoal.goal_type == "emergency_fund"
    ).first()
    
    if not emergency_fund_goal:
        return {"status": "not_set", "months_covered": 0, "target_months": 6}
    
    # Calculate months covered
    if avg_monthly_expenses > 0:
        months_covered = emergency_fund_goal.current_amount / avg_monthly_expenses
    else:
        months_covered = 0
    
    # Determine status
    if months_covered >= 6:
        status = "excellent"
    elif months_covered >= 3:
        status = "good"
    elif months_covered >= 1:
        status = "adequate"
    else:
        status = "inadequate"
    
    return {
        "status": status,
        "months_covered": months_covered,
        "target_months": 6,
        "current_amount": emergency_fund_goal.current_amount,
        "target_amount": emergency_fund_goal.target_amount
    }

def calculate_financial_health_score(user_id: int, db: Session) -> Dict:
    """Calculate overall financial health score based on various metrics"""
    # Get current month and year
    current_date = datetime.datetime.now().date()
    current_month = current_date.month
    current_year = current_date.year
    
    # Calculate savings rate (30% of score)
    savings_rate = calculate_savings_rate(user_id, db, current_month, current_year)
    savings_score = min(100, (savings_rate / 20) * 100)  # 20% savings rate = 100 score
    
    # Calculate debt-to-income ratio (30% of score)
    dti_ratio = calculate_debt_to_income_ratio(user_id, db)
    dti_score = max(0, 100 - (dti_ratio / 36) * 100)  # 36% DTI ratio = 0 score
    
    # Calculate emergency fund status (40% of score)
    emergency_fund = calculate_emergency_fund_status(user_id, db)
    emergency_fund_score = min(100, (emergency_fund["months_covered"] / 6) * 100)  # 6 months = 100 score
    
    # Calculate overall score
    overall_score = (0.3 * savings_score) + (0.3 * dti_score) + (0.4 * emergency_fund_score)
    
    # Determine health status
    if overall_score >= 80:
        status = "Excellent"
    elif overall_score >= 60:
        status = "Good"
    elif overall_score >= 40:
        status = "Fair"
    else:
        status = "Needs Improvement"
    
    return {
        "overall_score": overall_score,
        "status": status,
        "savings_rate": {
            "value": savings_rate,
            "score": savings_score
        },
        "debt_to_income": {
            "value": dti_ratio,
            "score": dti_score
        },
        "emergency_fund": {
            "months_covered": emergency_fund["months_covered"],
            "score": emergency_fund_score
        }
    }

def get_budget_performance(user_id: int, db: Session, month: int, year: int) -> Dict:
    """Calculate budget performance for a specific month"""
    start_date = datetime.date(year, month, 1)
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    
    # Get all budgets for the month
    budgets = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.period == "monthly",
        Budget.start_date <= end_date,
        (Budget.end_date >= start_date) | (Budget.end_date.is_(None))
    ).all()
    
    # Get all expenses for the month
    expenses = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()
    
    # Create a dictionary to track budget vs actual by category
    budget_performance = {}
    
    # Initialize with budget amounts
    for budget in budgets:
        budget_performance[budget.category] = {
            "budget": budget.amount,
            "actual": 0,
            "variance": 0,
            "variance_percent": 0
        }
    
    # Add categories with expenses but no budget
    for expense in expenses:
        if expense.category not in budget_performance:
            budget_performance[expense.category] = {
                "budget": 0,
                "actual": 0,
                "variance": 0,
                "variance_percent": 0
            }
    
    # Add expense amounts
    for expense in expenses:
        budget_performance[expense.category]["actual"] += expense.amount
    
    # Calculate variances
    for category, data in budget_performance.items():
        data["variance"] = data["budget"] - data["actual"]
        if data["budget"] > 0:
            data["variance_percent"] = (data["variance"] / data["budget"]) * 100
        else:
            data["variance_percent"] = -100  # Over budget by 100% when there was no budget
    
    # Calculate totals
    total_budget = sum(data["budget"] for data in budget_performance.values())
    total_actual = sum(data["actual"] for data in budget_performance.values())
    total_variance = total_budget - total_actual
    
    if total_budget > 0:
        total_variance_percent = (total_variance / total_budget) * 100
    else:
        total_variance_percent = -100
    
    return {
        "categories": budget_performance,
        "total": {
            "budget": total_budget,
            "actual": total_actual,
            "variance": total_variance,
            "variance_percent": total_variance_percent
        }
    }

def calculate_investment_returns(user_id: int, db: Session) -> Dict:
    """Calculate returns on investments"""
    investments = db.query(Investment).filter(
        Investment.user_id == user_id
    ).all()
    
    investment_returns = {}
    total_invested = 0
    total_current_value = 0
    
    for investment in investments:
        # Skip investments without current value
        if not investment.current_value:
            continue
        
        initial_investment = investment.amount
        current_value = investment.current_value
        
        # Calculate absolute return
        absolute_return = current_value - initial_investment
        
        # Calculate purchase date
        if investment.purchase_date:
            days_held = (datetime.datetime.now().date() - investment.purchase_date).days
            years_held = days_held / 365.25
        else:
            years_held = 1  # Default to 1 year if no purchase date
        
        # Calculate annualized return (CAGR)
        if years_held > 0 and initial_investment > 0:
            cagr = ((current_value / initial_investment) ** (1 / years_held)) - 1
            cagr_percent = cagr * 100
        else:
            cagr_percent = 0
        
        investment_returns[investment.name] = {
            "type": investment.investment_type,
            "initial_investment": initial_investment,
            "current_value": current_value,
            "absolute_return": absolute_return,
            "absolute_return_percent": (absolute_return / initial_investment) * 100 if initial_investment > 0 else 0,
            "annualized_return_percent": cagr_percent,
            "days_held": days_held if investment.purchase_date else None
        }
        
        total_invested += initial_investment
        total_current_value += current_value
    
    # Calculate overall return
    overall_absolute_return = total_current_value - total_invested
    overall_absolute_return_percent = (overall_absolute_return / total_invested) * 100 if total_invested > 0 else 0
    
    return {
        "investments": investment_returns,
        "total": {
            "invested": total_invested,
            "current_value": total_current_value,
            "absolute_return": overall_absolute_return,
            "absolute_return_percent": overall_absolute_return_percent
        }
    }

def calculate_asset_allocation(user_id: int, db: Session) -> Dict:
    """Calculate asset allocation across different investment types"""
    investments = db.query(Investment).filter(
        Investment.user_id == user_id
    ).all()
    
    # Initialize allocation dictionary
    allocation = {}
    
    # Calculate total investment value
    total_value = sum(inv.current_value or inv.amount for inv in investments)
    
    if total_value == 0:
        return {"allocation": {}, "total_value": 0}
    
    # Calculate allocation by investment type
    for investment in investments:
        inv_type = investment.investment_type
        value = investment.current_value or investment.amount
        
        if inv_type not in allocation:
            allocation[inv_type] = 0
        
        allocation[inv_type] += value
    
    # Convert to percentages
    allocation_percent = {
        inv_type: (value / total_value) * 100
        for inv_type, value in allocation.items()
    }
    
    return {
        "allocation": allocation_percent,
        "allocation_amount": allocation,
        "total_value": total_value
    }

def calculate_goal_progress(user_id: int, db: Session) -> Dict:
    """Calculate progress towards financial goals"""
    goals = db.query(FinancialGoal).filter(
        FinancialGoal.user_id == user_id,
        FinancialGoal.is_completed == False
    ).all()
    
    goal_progress = {}
    
    for goal in goals:
        # Calculate progress percentage
        progress_percent = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0
        
        # Calculate time progress
        if goal.target_date and goal.start_date:
            total_days = (goal.target_date - goal.start_date).days
            days_passed = (datetime.datetime.now().date() - goal.start_date).days
            time_percent = (days_passed / total_days) * 100 if total_days > 0 else 0
            
            # Check if on track
            if progress_percent >= time_percent:
                status = "on_track"
            else:
                status = "behind"
        else:
            time_percent = 0
            status = "unknown"
        
        # Calculate remaining amount
        remaining_amount = goal.target_amount - goal.current_amount
        
        # Calculate monthly contribution needed
        if goal.target_date and remaining_amount > 0:
            months_remaining = ((goal.target_date - datetime.datetime.now().date()).days / 30)
            if months_remaining > 0:
                monthly_contribution_needed = remaining_amount / months_remaining
            else:
                monthly_contribution_needed = remaining_amount
        else:
            monthly_contribution_needed = 0
        
        goal_progress[goal.name] = {
            "type": goal.goal_type,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "progress_percent": progress_percent,
            "time_percent": time_percent,
            "status": status,
            "remaining_amount": remaining_amount,
            "monthly_contribution_needed": monthly_contribution_needed,
            "target_date": goal.target_date
        }
    
    return goal_progress

def calculate_retirement_projection(user_id: int, db: Session, 
                                   current_age: int, retirement_age: int, 
                                   life_expectancy: int, inflation_rate: float,
                                   expected_return_rate: float) -> Dict:
    """Project retirement corpus and income"""
    # Get current retirement savings
    retirement_investments = db.query(Investment).filter(
        Investment.user_id == user_id,
        Investment.investment_type.in_(["epf", "nps", "ppf"])
    ).all()
    
    current_retirement_corpus = sum(inv.current_value or inv.amount for inv in retirement_investments)
    
    # Get monthly SIP contributions to retirement
    monthly_retirement_contribution = sum(
        inv.sip_amount for inv in retirement_investments 
        if inv.is_sip and inv.sip_frequency == "monthly"
    )
    
    # Calculate years to retirement
    years_to_retirement = retirement_age - current_age
    
    # Project retirement corpus
    projected_corpus = current_retirement_corpus
    
    for year in range(years_to_retirement):
        # Add annual contribution
        annual_contribution = monthly_retirement_contribution * 12
        # Add investment returns
        annual_return = (projected_corpus + annual_contribution / 2) * expected_return_rate
        # Update corpus
        projected_corpus += annual_contribution + annual_return
    
    # Calculate monthly income in today's value
    retirement_years = life_expectancy - retirement_age
    
    if retirement_years > 0:
        # Calculate sustainable withdrawal rate (SWR)
        # Simple implementation - 4% rule
        annual_withdrawal = projected_corpus * 0.04
        monthly_income_at_retirement = annual_withdrawal / 12
        
        # Adjust for inflation to get today's value
        monthly_income_today_value = monthly_income_at_retirement / ((1 + inflation_rate) ** years_to_retirement)
    else:
        monthly_income_at_retirement = 0
        monthly_income_today_value = 0
    
    return {
        "current_retirement_corpus": current_retirement_corpus,
        "monthly_contribution": monthly_retirement_contribution,
        "years_to_retirement": years_to_retirement,
        "projected_retirement_corpus": projected_corpus,
        "monthly_income_at_retirement": monthly_income_at_retirement,
        "monthly_income_today_value": monthly_income_today_value
    }

def calculate_loan_amortization(principal: float, rate: float, tenure_months: int) -> Dict:
    """Calculate loan amortization schedule"""
    monthly_rate = rate / (12 * 100)  # Convert annual rate to monthly rate
    
    if monthly_rate == 0:
        emi = principal / tenure_months
    else:
        emi = (principal * monthly_rate * (1 + monthly_rate) ** tenure_months) / ((1 + monthly_rate) ** tenure_months - 1)
    
    amortization_schedule = []
    remaining_principal = principal
    
    for month in range(1, tenure_months + 1):
        interest_payment = remaining_principal * monthly_rate
        principal_payment = emi - interest_payment
        remaining_principal -= principal_payment
        
        amortization_schedule.append({
            "month": month,
            "emi": emi,
            "principal_payment": principal_payment,
            "interest_payment": interest_payment,
            "remaining_principal": max(0, remaining_principal)  # Ensure no negative value due to rounding
        })
    
    return {
        "loan_amount": principal,
        "interest_rate_annual": rate,
        "tenure_months": tenure_months,
        "emi": emi,
        "total_payment": emi * tenure_months,
        "total_interest": (emi * tenure_months) - principal,
        "amortization_schedule": amortization_schedule
    }

def calculate_sip_returns(monthly_investment: float, expected_return_rate: float, 
                         tenure_years: int) -> Dict:
    """Calculate SIP returns"""
    monthly_rate = expected_return_rate / (12 * 100)  # Convert annual rate to monthly rate
    tenure_months = tenure_years * 12
    
    # SIP future value formula
    future_value = monthly_investment * ((((1 + monthly_rate) ** tenure_months) - 1) / monthly_rate) * (1 + monthly_rate)
    
    total_invested = monthly_investment * tenure_months
    wealth_gained = future_value - total_invested
    absolute_return = (wealth_gained / total_invested) * 100
    
    return {
        "monthly_investment": monthly_investment,
        "expected_return_rate": expected_return_rate,
        "tenure_years": tenure_years,
        "tenure_months": tenure_months,
        "future_value": future_value,
        "total_invested": total_invested,
        "wealth_gained": wealth_gained,
        "absolute_return_percent": absolute_return
    }

def detect_spending_anomalies(user_id: int, db: Session) -> List[Dict]:
    """Detect unusual spending patterns"""
    # Get current date
    current_date = datetime.datetime.now().date()
    
    # Get expenses for the last 6 months
    six_months_ago = current_date - datetime.timedelta(days=180)
    
    expenses = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.date >= six_months_ago,
        Expense.date <= current_date
    ).all()
    
    # Group expenses by category and month
    category_month_expenses = {}
    
    for expense in expenses:
        category = expense.category
        month_year = expense.date.strftime("%Y-%m")
        
        if category not in category_month_expenses:
            category_month_expenses[category] = {}
        
        if month_year not in category_month_expenses[category]:
            category_month_expenses[category][month_year] = 0
        
        category_month_expenses[category][month_year] += expense.amount
    
    # Calculate average and standard deviation for each category
    category_stats = {}
    anomalies = []
    
    for category, month_data in category_month_expenses.items():
        if len(month_data) < 3:  # Need at least 3 months of data
            continue
        
        values = list(month_data.values())
        avg = sum(values) / len(values)
        std_dev = (sum((x - avg) ** 2 for x in values) / len(values)) ** 0.5
        
        category_stats[category] = {
            "average": avg,
            "std_dev": std_dev
        }
        
        # Check the most recent month for anomalies
        current_month_year = current_date.strftime("%Y-%m")
        if current_month_year in month_data:
            current_month_expense = month_data[current_month_year]
            z_score = (current_month_expense - avg) / std_dev if std_dev > 0 else 0
            
            # Consider as anomaly if more than 2 standard deviations
            if z_score > 2:
                anomalies.append({
                    "category": category,
                    "month": current_month_year,
                    "amount": current_month_expense,
                    "average": avg,
                    "percent_increase": ((current_month_expense - avg) / avg) * 100,
                    "severity": "high" if z_score > 3 else "medium"
                })
    
    return anomalies