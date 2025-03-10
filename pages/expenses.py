import streamlit as st
import os
import sys
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db_session
from database.models import User, Expense
from database.operations import (
    get_expenses, create_expense, update_expense, delete_expense
)
from utils.visualization import (
    expense_breakdown_chart
)
from utils.auth_utils import require_auth
from config import EXPENSE_CATEGORIES

def show_expenses_page(user):
    """Display the expenses page"""
    require_auth()
    
    st.markdown("<h1 class='main-header'>Expense Management</h1>", unsafe_allow_html=True)
    
    # Expenses tabs
    tab1, tab2, tab3 = st.tabs(["Expense Tracker", "Expense Analysis", "Recurring Expenses"])
    
    with tab1:
        show_expense_tracker(user)
    
    with tab2:
        show_expense_analysis(user)
    
    with tab3:
        show_recurring_expenses(user)

def show_expense_tracker(user):
    """Show expense tracker"""
    st.subheader("Expense Tracker")
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=date(date.today().year, date.today().month, 1))
    with col2:
        end_date = st.date_input("To", value=date.today())
    
    # Get expenses
    expenses = get_expenses(db_session, user.id, start_date, end_date)
    
    # Display expenses
    if expenses:
        expense_data = []
        for expense in expenses:
            expense_data.append({
                "id": expense.id,
                "category": expense.category,
                "amount": expense.amount,
                "date": expense.date,
                "description": expense.description or "",
                "payment_method": expense.payment_method or "",
                "is_recurring": "Yes" if expense.is_recurring else "No"
            })
        
        df = pd.DataFrame(expense_data)
        
        # Edit/Delete functionality
        selected_expense = st.selectbox(
            "Select expense to edit or delete",
            options=df["id"].tolist(),
            format_func=lambda x: f"{next((e['category'] for e in expense_data if e['id'] == x), '')} - " +
                           f"₹{next((e['amount'] for e in expense_data if e['id'] == x), 0):,.2f} - " +
                           f"{next((e['date'] for e in expense_data if e['id'] == x), '')}"
        )
        
        # Get selected expense
        selected_exp = next((expense for expense in expenses if expense.id == selected_expense), None)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.dataframe(
                df,
                column_config={
                    "id": None,  # Hide ID column
                    "category": "Category",
                    "amount": st.column_config.NumberColumn(
                        "Amount",
                        format="₹%.2f"
                    ),
                    "date": st.column_config.DateColumn(
                        "Date",
                        format="DD-MM-YYYY"
                    ),
                    "description": "Description",
                    "payment_method": "Payment Method",
                    "is_recurring": "Recurring"
                },
                hide_index=True
            )
        
        with col2:
            if selected_exp:
                # Update expense
                new_amount = st.number_input(
                    "Update Amount",
                    min_value=0.0,
                    value=float(selected_exp.amount),
                    step=100.0
                )
                
                new_category = st.selectbox(
                    "Update Category",
                    options=EXPENSE_CATEGORIES,
                    index=EXPENSE_CATEGORIES.index(selected_exp.category) if selected_exp.category in EXPENSE_CATEGORIES else 0
                )
                
                if st.button("Update Expense"):
                    update_expense(
                        db=db_session,
                        expense_id=selected_exp.id,
                        user_id=user.id,
                        amount=new_amount,
                        category=new_category
                    )
                    st.success("Expense updated!")
                    st.rerun()
                
                if st.button("Delete Expense", type="secondary"):
                    delete_expense(db_session, selected_exp.id, user.id)
                    st.success("Expense deleted successfully!")
                    st.rerun()
        
        # Calculate total
        total_expenses = sum(expense.amount for expense in expenses)
        st.metric("Total Expenses", f"₹{total_expenses:,.2f}")
        
        # Expense breakdown chart
        st.subheader("Expense Breakdown")
        
        if expense_data:
            expense_chart = expense_breakdown_chart(expense_data)
            st.plotly_chart(expense_chart, use_container_width=True)
    else:
        st.info("No expenses found for the selected period.")
    
    # Add new expense
    st.markdown("### Add New Expense")
    
    with st.form("add_expense_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox("Category", EXPENSE_CATEGORIES)
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            expense_date = st.date_input("Date", max_value=date.today())
        
        with col2:
            payment_methods = ["Cash", "Credit Card", "Debit Card", "UPI", "Net Banking", "Other"]
            payment_method = st.selectbox("Payment Method", payment_methods)
            description = st.text_area("Description (Optional)")
            is_recurring = st.checkbox("Is this a recurring expense?")
        
        # Recurring expense details
        if is_recurring:
            col1, col2 = st.columns(2)
            with col1:
                frequency = st.selectbox(
                    "Frequency",
                    ["daily", "weekly", "monthly", "quarterly", "yearly"]
                )
        else:
            frequency = None
        
        submitted = st.form_submit_button("Add Expense")
        
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than zero")
            else:
                # Create expense
                create_expense(
                    db=db_session,
                    user_id=user.id,
                    category=category,
                    amount=amount,
                    date=expense_date,
                    description=description,
                    is_recurring=is_recurring,
                    frequency=frequency,
                    payment_method=payment_method
                )
                
                st.success("Expense added successfully!")
                st.rerun()

def show_expense_analysis(user):
    """Show expense analysis"""
    st.subheader("Expense Analysis")
    
    # Time period selection
    period = st.radio(
        "Select Time Period",
        ["Current Month", "Last Month", "Last 3 Months", "Last 6 Months", "Current Year", "Custom"],
        horizontal=True
    )
    
    # Set date range based on selection
    today = date.today()
    if period == "Current Month":
        start_date = date(today.year, today.month, 1)
        end_date = today
    elif period == "Last Month":
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1
        start_date = date(last_month_year, last_month, 1)
        end_date = date(today.year, today.month, 1) - timedelta(days=1)
    elif period == "Last 3 Months":
        start_date = today - timedelta(days=90)
        end_date = today
    elif period == "Last 6 Months":
        start_date = today - timedelta(days=180)
        end_date = today
    elif period == "Current Year":
        start_date = date(today.year, 1, 1)
        end_date = today
    else:  # Custom
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date(today.year, 1, 1))
        with col2:
            end_date = st.date_input("End Date", value=today)
    
    # Get expenses for the selected period
    expenses = get_expenses(db_session, user.id, start_date, end_date)
    
    if not expenses:
        st.info("No expenses found for the selected period.")
        return
    
    # Category breakdown analysis
    st.markdown("### Expense by Category")
    
    # Group expenses by category
    category_expenses = {}
    for expense in expenses:
        category = expense.category
        if category not in category_expenses:
            category_expenses[category] = 0
        category_expenses[category] += expense.amount
    
    # Create category breakdown chart
    category_data = []
    for category, amount in category_expenses.items():
        category_data.append({
            "category": category,
            "amount": amount
        })
    
    # Sort by amount
    category_data.sort(key=lambda x: x["amount"], reverse=True)
    
    # Display pie chart
    fig_pie = px.pie(
        category_data,
        values="amount",
        names="category",
        title="Expense Distribution by Category",
        hole=0.4
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Monthly trend analysis
    st.markdown("### Monthly Expense Trend")
    
    # Group expenses by month
    monthly_expenses = {}
    for expense in expenses:
        month_key = expense.date.strftime("%Y-%m")
        if month_key not in monthly_expenses:
            monthly_expenses[month_key] = 0
        monthly_expenses[month_key] += expense.amount
    
    # Create monthly trend chart
    if monthly_expenses:
        months = list(monthly_expenses.keys())
        amounts = list(monthly_expenses.values())
        
        fig_line = go.Figure()
        
        fig_line.add_trace(go.Scatter(
            x=months,
            y=amounts,
            mode='lines+markers',
            name='Monthly Expenses',
            line=dict(color='red', width=3)
        ))
        
        fig_line.update_layout(
            title='Monthly Expense Trend',
            xaxis_title='Month',
            yaxis_title='Amount (₹)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
    
    # Day of week analysis
    st.markdown("### Expense by Day of Week")
    
    # Group expenses by day of week
    day_expenses = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for expense in expenses:
        day_of_week = expense.date.weekday()  # 0 is Monday
        day_name = days[day_of_week]
        if day_name not in day_expenses:
            day_expenses[day_name] = 0
        day_expenses[day_name] += expense.amount
    
    # Create day of week chart
    if day_expenses:
        day_data = []
        for day in days:
            day_data.append({
                "day": day,
                "amount": day_expenses.get(day, 0)
            })
        
        fig_bar = px.bar(
            day_data,
            x="day",
            y="amount",
            title="Expense by Day of Week",
            labels={"day": "Day", "amount": "Amount (₹)"},
            color_discrete_sequence=["#FF6666"]
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Payment method analysis
    st.markdown("### Expense by Payment Method")
    
    # Group expenses by payment method
    payment_expenses = {}
    for expense in expenses:
        payment_method = expense.payment_method or "Other"
        if payment_method not in payment_expenses:
            payment_expenses[payment_method] = 0
        payment_expenses[payment_method] += expense.amount
    
    # Create payment method chart
    if payment_expenses:
        payment_data = []
        for method, amount in payment_expenses.items():
            payment_data.append({
                "method": method,
                "amount": amount
            })
        
        # Sort by amount
        payment_data.sort(key=lambda x: x["amount"], reverse=True)
        
        fig_payment = px.bar(
            payment_data,
            x="method",
            y="amount",
            title="Expense by Payment Method",
            labels={"method": "Payment Method", "amount": "Amount (₹)"},
            color="method"
        )
        
        st.plotly_chart(fig_payment, use_container_width=True)
    
    # Top expenses
    st.markdown("### Top 10 Expenses")
    
    # Sort expenses by amount
    top_expenses = sorted(expenses, key=lambda x: x.amount, reverse=True)[:10]
    
    if top_expenses:
        top_data = []
        for expense in top_expenses:
            top_data.append({
                "category": expense.category,
                "amount": expense.amount,
                "date": expense.date,
                "description": expense.description or ""
            })
        
        st.dataframe(
            top_data,
            column_config={
                "category": "Category",
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    format="₹%.2f"
                ),
                "date": st.column_config.DateColumn(
                    "Date",
                    format="DD-MM-YYYY"
                ),
                "description": "Description"
            },
            hide_index=True
        )

def show_recurring_expenses(user):
    """Show recurring expenses"""
    st.subheader("Recurring Expenses")
    
    # Get recurring expenses
    recurring_expenses = db_session.query(Expense).filter(
        Expense.user_id == user.id,
        Expense.is_recurring == True
    ).all()
    
    if recurring_expenses:
        recurring_data = []
        for expense in recurring_expenses:
            recurring_data.append({
                "id": expense.id,
                "category": expense.category,
                "amount": expense.amount,
                "frequency": expense.frequency or "Not specified",
                "payment_method": expense.payment_method or "",
                "description": expense.description or ""
            })
        
        df = pd.DataFrame(recurring_data)
        
        st.dataframe(
            df,
            column_config={
                "id": None,  # Hide ID column
                "category": "Category",
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    format="₹%.2f"
                ),
                "frequency": "Frequency",
                "payment_method": "Payment Method",
                "description": "Description"
            },
            hide_index=True
        )
        
        # Calculate monthly recurring expenses
        monthly_total = 0
        for expense in recurring_expenses:
            freq = expense.frequency or "monthly"
            if freq == "daily":
                monthly_total += expense.amount * 30
            elif freq == "weekly":
                monthly_total += expense.amount * 4
            elif freq == "monthly":
                monthly_total += expense.amount
            elif freq == "quarterly":
                monthly_total += expense.amount / 3
            elif freq == "yearly":
                monthly_total += expense.amount / 12
        
        st.metric("Total Monthly Recurring Expenses", f"₹{monthly_total:,.2f}")
        
        # Recurring expenses breakdown
        st.markdown("### Recurring Expenses Breakdown")
        
        # Group by category
        recurring_by_category = {}
        for expense in recurring_expenses:
            category = expense.category
            if category not in recurring_by_category:
                recurring_by_category[category] = 0
            
            # Convert all to monthly
            freq = expense.frequency or "monthly"
            if freq == "daily":
                recurring_by_category[category] += expense.amount * 30
            elif freq == "weekly":
                recurring_by_category[category] += expense.amount * 4
            elif freq == "monthly":
                recurring_by_category[category] += expense.amount
            elif freq == "quarterly":
                recurring_by_category[category] += expense.amount / 3
            elif freq == "yearly":
                recurring_by_category[category] += expense.amount / 12
        
        # Create chart
        category_data = []
        for category, amount in recurring_by_category.items():
            category_data.append({
                "category": category,
                "amount": amount
            })
        
        # Sort by amount
        category_data.sort(key=lambda x: x["amount"], reverse=True)
        
        fig = px.pie(
            category_data,
            values="amount",
            names="category",
            title="Monthly Recurring Expenses by Category",
            hole=0.4
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("You don't have any recurring expenses yet. Create one by checking the 'Recurring' option when adding an expense.")