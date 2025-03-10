import streamlit as st
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db_session
from database.models import User, IncomeSource, Expense, Budget, Investment, Debt, FinancialGoal, Notification
from database.operations import get_expenses, get_income_sources, get_notifications, mark_notification_as_read
from utils.finance_utils import (
    calculate_monthly_income, calculate_monthly_expenses, calculate_savings_rate,
    calculate_net_worth, calculate_financial_health_score, calculate_debt_to_income_ratio,
    calculate_emergency_fund_status, detect_spending_anomalies
)
from utils.visualization import (
    income_vs_expenses_chart, expense_breakdown_chart, financial_health_gauge
)
from utils.auth_utils import require_auth

def show_dashboard(user):
    """Display the dashboard page"""
    require_auth()
    
    st.markdown("<h1 class='main-header'>Dashboard</h1>", unsafe_allow_html=True)
    
    # Get current date
    current_date = datetime.now().date()
    current_month = current_date.month
    current_year = current_date.year
    
    # Financial Overview Section
    st.markdown("<h2 class='sub-header'>Financial Overview</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # Net Worth Card
    with col1:
        net_worth = calculate_net_worth(user.id, db_session)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">₹{net_worth['net_worth']:,.2f}</div>
                <div class="metric-label">Net Worth</div>
                <div>Assets: ₹{net_worth['assets']:,.2f}</div>
                <div>Liabilities: ₹{net_worth['liabilities']:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Monthly Cash Flow Card
    with col2:
        monthly_income = calculate_monthly_income(user.id, db_session, current_month, current_year)
        monthly_expenses = calculate_monthly_expenses(user.id, db_session, current_month, current_year)
        monthly_savings = monthly_income - monthly_expenses
        savings_rate = calculate_savings_rate(user.id, db_session, current_month, current_year)
        
        savings_class = "positive" if monthly_savings >= 0 else "negative"
        
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">₹{monthly_savings:,.2f}</div>
                <div class="metric-label">Monthly Cash Flow</div>
                <div>Income: ₹{monthly_income:,.2f}</div>
                <div>Expenses: ₹{monthly_expenses:,.2f}</div>
                <div>Savings Rate: <span class="{savings_class}">{savings_rate:.1f}%</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Financial Health Score Card
    with col3:
        health_score = calculate_financial_health_score(user.id, db_session)
        
        health_class = "positive"
        if health_score["status"] == "Needs Improvement":
            health_class = "negative"
        elif health_score["status"] == "Fair":
            health_class = "warning"
        
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{health_score['overall_score']:.1f}</div>
                <div class="metric-label">Financial Health Score</div>
                <div>Status: <span class="{health_class}">{health_score['status']}</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Income vs Expenses Chart
    st.markdown("<h2 class='sub-header'>Income vs Expenses (Last 6 Months)</h2>", unsafe_allow_html=True)
    
    # Generate dummy data for the demo
    six_months_ago = current_date - timedelta(days=180)
    months = pd.date_range(start=six_months_ago, end=current_date, freq='MS').strftime('%Y-%m').tolist()
    
    income_data = []
    expense_data = []
    
    for i, month in enumerate(months):
        year = int(month.split("-")[0])
        month_num = int(month.split("-")[1])
        
        income = calculate_monthly_income(user.id, db_session, month_num, year)
        expenses = calculate_monthly_expenses(user.id, db_session, month_num, year)
        
        income_data.append({
            "date": month,
            "income": income
        })
        
        expense_data.append({
            "date": month,
            "expenses": expenses
        })
    
    # Plot chart
    if income_data and expense_data:
        income_expense_chart = income_vs_expenses_chart(income_data, expense_data)
        st.plotly_chart(income_expense_chart, use_container_width=True)
    else:
        st.info("Add your income sources and expenses to see this chart")
    
    # Split dashboard into two columns
    col1, col2 = st.columns(2)
    
    # Expense Breakdown (Current Month)
    with col1:
        st.markdown("<h2 class='sub-header'>Expense Breakdown (Current Month)</h2>", unsafe_allow_html=True)
        
        # Get expenses for current month
        start_date = datetime(current_year, current_month, 1).date()
        if current_month == 12:
            end_date = datetime(current_year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(current_year, current_month + 1, 1).date() - timedelta(days=1)
        
        expenses = get_expenses(db_session, user.id, start_date, end_date)
        
        if expenses:
            expense_data = []
            for expense in expenses:
                expense_data.append({
                    "category": expense.category,
                    "amount": expense.amount
                })
            
            expense_chart = expense_breakdown_chart(expense_data)
            st.plotly_chart(expense_chart, use_container_width=True)
        else:
            st.info("Add your expenses to see this breakdown")
    
    # Financial Health Gauge
    with col2:
        st.markdown("<h2 class='sub-header'>Financial Health Score</h2>", unsafe_allow_html=True)
        
        health_gauge = financial_health_gauge(health_score["overall_score"])
        st.plotly_chart(health_gauge, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Savings Rate", 
                f"{health_score['savings_rate']['value']:.1f}%",
                f"{health_score['savings_rate']['score']:.1f}/100"
            )
        
        with col2:
            st.metric(
                "Debt-to-Income", 
                f"{health_score['debt_to_income']['value']:.1f}%",
                f"{health_score['debt_to_income']['score']:.1f}/100"
            )
        
        with col3:
            st.metric(
                "Emergency Fund", 
                f"{health_score['emergency_fund']['months_covered']:.1f} months",
                f"{health_score['emergency_fund']['score']:.1f}/100"
            )
    
    # Alerts and Notifications
    st.markdown("<h2 class='sub-header'>Alerts & Notifications</h2>", unsafe_allow_html=True)
    
    # Get user notifications
    notifications = get_notifications(db_session, user.id, limit=5)
    
    # Get spending anomalies
    anomalies = detect_spending_anomalies(user.id, db_session)
    
    # Check debt-to-income ratio
    dti_ratio = calculate_debt_to_income_ratio(user.id, db_session)
    dti_alert = None
    if dti_ratio > 40:
        dti_alert = {
            "title": "High Debt-to-Income Ratio",
            "message": f"Your debt-to-income ratio is {dti_ratio:.1f}%, which is above the recommended maximum of 36%. Consider reducing your debt or increasing your income."
        }
    
    # Check emergency fund status
    emergency_fund = calculate_emergency_fund_status(user.id, db_session)
    emergency_alert = None
    if emergency_fund["months_covered"] < 3:
        emergency_alert = {
            "title": "Low Emergency Fund",
            "message": f"Your emergency fund covers only {emergency_fund['months_covered']:.1f} months of expenses. It's recommended to have at least 3-6 months of expenses saved."
        }
    
    # Display all alerts
    if notifications or anomalies or dti_alert or emergency_alert:
        tab1, tab2 = st.tabs(["Notifications", "Financial Alerts"])
        
        with tab1:
            if notifications:
                for notification in notifications:
                    with st.expander(f"{notification.title} - {notification.created_at.strftime('%d %b %Y, %H:%M')}"):
                        st.write(notification.message)
                        if not notification.is_read:
                            if st.button("Mark as Read", key=f"read_{notification.id}"):
                                mark_notification_as_read(db_session, notification.id, user.id)
                                st.success("Marked as read!")
                                st.rerun()
            else:
                st.info("No notifications")
        
        with tab2:
            if anomalies:
                for anomaly in anomalies:
                    with st.expander(f"Unusual Spending in {anomaly['category']}"):
                        st.write(f"Your spending in {anomaly['category']} (₹{anomaly['amount']:,.2f}) is {anomaly['percent_increase']:.1f}% higher than your average (₹{anomaly['average']:,.2f}).")
                        st.write("Consider reviewing your spending in this category.")
            
            if dti_alert:
                with st.expander(dti_alert["title"]):
                    st.write(dti_alert["message"])
            
            if emergency_alert:
                with st.expander(emergency_alert["title"]):
                    st.write(emergency_alert["message"])
            
            if not (anomalies or dti_alert or emergency_alert):
                st.success("No financial alerts at this time. Great job!")
    else:
        st.info("No alerts or notifications at this time")