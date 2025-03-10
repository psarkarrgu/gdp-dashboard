import streamlit as st
import os
import sys
from datetime import datetime, date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db_session
from database.models import User, Budget, Expense
from database.operations import (
    get_budgets, create_budget, update_budget, delete_budget,
    get_expenses
)
from utils.finance_utils import (
    get_budget_performance
)
from utils.visualization import (
    budget_vs_actual_chart
)
from utils.auth_utils import require_auth
from config import EXPENSE_CATEGORIES

def show_budget_page(user):
    """Display the budget planning page"""
    require_auth()
    
    st.markdown("<h1 class='main-header'>Budget Planning</h1>", unsafe_allow_html=True)
    
    # Budget tabs
    tab1, tab2, tab3 = st.tabs(["Budget Overview", "Manage Budgets", "Budget Performance"])
    
    with tab1:
        show_budget_overview(user)
    
    with tab2:
        show_manage_budgets(user)
    
    with tab3:
        show_budget_performance(user)

def show_budget_overview(user):
    """Show budget overview"""
    st.subheader("Budget Overview")
    
    # Current month and year
    current_date = date.today()
    current_month = current_date.month
    current_year = current_date.year
    
    # Get monthly budgets
    budgets = db_session.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.period == "monthly"
    ).all()
    
    if not budgets:
        st.info("You don't have any monthly budgets yet. Create one in the 'Manage Budgets' tab.")
        return
    
    # Calculate budget performance
    budget_perf = get_budget_performance(user.id, db_session, current_month, current_year)
    
    # Budget vs Actual Chart
    if budget_perf["categories"]:
        budget_chart = budget_vs_actual_chart(budget_perf)
        st.plotly_chart(budget_chart, use_container_width=True)
    else:
        st.info("No budget data available for the current month.")
    
    # Budget Summary
    st.subheader("Budget Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Budget",
            f"₹{budget_perf['total']['budget']:,.2f}"
        )
    
    with col2:
        st.metric(
            "Actual Spending",
            f"₹{budget_perf['total']['actual']:,.2f}"
        )
    
    with col3:
        variance = budget_perf['total']['variance']
        variance_percent = budget_perf['total']['variance_percent']
        
        st.metric(
            "Remaining Budget",
            f"₹{variance:,.2f}",
            f"{variance_percent:.1f}%",
            delta_color="normal" if variance >= 0 else "inverse"
        )
    
    # Category-wise Budget Status
    st.subheader("Category-wise Budget Status")
    
    # Convert to dataframe for display
    categories = []
    for category, data in budget_perf["categories"].items():
        categories.append({
            "category": category,
            "budget": data["budget"],
            "actual": data["actual"],
            "remaining": data["variance"],
            "percent_used": 100 - data["variance_percent"] if data["budget"] > 0 else 100,
            "status": "On Track" if data["variance"] >= 0 else "Over Budget"
        })
    
    # Sort by percent used (descending)
    categories.sort(key=lambda x: x["percent_used"], reverse=True)
    
    df = pd.DataFrame(categories)
    
    # Create a status column with colored indicators
    def status_color(row):
        if row["status"] == "Over Budget":
            return "background-color: #ffcccc"
        elif row["percent_used"] > 90:
            return "background-color: #fff2cc"
        else:
            return "background-color: #d9ead3"
    
    # Apply styling
    styled_df = df.style.apply(lambda row: [status_color(row) if col == "status" else "" for col in df.columns], axis=1)
    
    st.dataframe(
        styled_df,
        column_config={
            "category": "Category",
            "budget": st.column_config.NumberColumn(
                "Budget",
                format="₹%.2f"
            ),
            "actual": st.column_config.NumberColumn(
                "Actual",
                format="₹%.2f"
            ),
            "remaining": st.column_config.NumberColumn(
                "Remaining",
                format="₹%.2f"
            ),
            "percent_used": st.column_config.ProgressColumn(
                "Budget Used",
                format="%.1f%%",
                min_value=0,
                max_value=100
            ),
            "status": "Status"
        },
        hide_index=True
    )
    
    # Budget Alerts
    over_budget_categories = [cat for cat in categories if cat["status"] == "Over Budget"]
    near_limit_categories = [cat for cat in categories if cat["status"] == "On Track" and cat["percent_used"] > 90]
    
    if over_budget_categories or near_limit_categories:
        st.subheader("Budget Alerts")
        
        for category in over_budget_categories:
            st.error(
                f"🔴 **{category['category']}** is over budget by "
                f"₹{-category['remaining']:,.2f} ({category['percent_used']:.1f}% used)"
            )
        
        for category in near_limit_categories:
            st.warning(
                f"🟠 **{category['category']}** is nearing its budget limit "
                f"({category['percent_used']:.1f}% used, ₹{category['remaining']:,.2f} remaining)"
            )

def show_manage_budgets(user):
    """Show manage budgets section"""
    st.subheader("Manage Your Budgets")
    
    # Get user's budgets
    budgets = get_budgets(db_session, user.id)
    
    # Display existing budgets
    if budgets:
        budget_data = []
        for budget in budgets:
            budget_data.append({
                "id": budget.id,
                "category": budget.category,
                "amount": budget.amount,
                "period": budget.period,
                "start_date": budget.start_date,
                "end_date": budget.end_date
            })
        
        df = pd.DataFrame(budget_data)
        
        # Filter options
        period_filter = st.selectbox(
            "Filter by Period",
            ["All", "monthly", "quarterly", "annually"],
            index=0
        )
        
        if period_filter != "All":
            df = df[df["period"] == period_filter]
        
        # Edit/Delete functionality
        selected_budget = st.selectbox(
            "Select budget to edit or delete",
            options=df["id"].tolist(),
            format_func=lambda x: f"{next((b['category'] for b in budget_data if b['id'] == x), '')} - " +
                           f"₹{next((b['amount'] for b in budget_data if b['id'] == x), 0):,.2f} ({next((b['period'] for b in budget_data if b['id'] == x), '')})"
        )
        
        # Get selected budget
        selected_bdg = next((budget for budget in budgets if budget.id == selected_budget), None)
        
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
                    "period": "Period",
                    "start_date": st.column_config.DateColumn(
                        "Start Date",
                        format="DD-MM-YYYY"
                    ),
                    "end_date": st.column_config.DateColumn(
                        "End Date",
                        format="DD-MM-YYYY"
                    )
                },
                hide_index=True
            )
        
        with col2:
            if selected_bdg:
                # Update budget
                new_amount = st.number_input(
                    "Update Amount",
                    min_value=0.0,
                    value=float(selected_bdg.amount),
                    step=1000.0
                )
                
                if st.button("Update Budget"):
                    update_budget(
                        db=db_session,
                        budget_id=selected_bdg.id,
                        user_id=user.id,
                        amount=new_amount
                    )
                    st.success("Budget updated!")
                    st.rerun()
                
                if st.button("Delete Budget", type="secondary"):
                    delete_budget(db_session, selected_bdg.id, user.id)
                    st.success("Budget deleted successfully!")
                    st.rerun()
    else:
        st.info("You don't have any budgets yet. Add one below.")
    
    # Add new budget
    st.markdown("### Add New Budget")
    
    with st.form("add_budget_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox("Category", EXPENSE_CATEGORIES)
            amount = st.number_input("Budget Amount (₹)", min_value=0.0, step=1000.0)
        
        with col2:
            period = st.selectbox(
                "Budget Period",
                ["monthly", "quarterly", "annually"]
            )
            
            start_date = st.date_input("Start Date", value=date.today().replace(day=1))
            end_date = st.date_input("End Date (leave blank for ongoing)", value=None)
        
        submitted = st.form_submit_button("Add Budget")
        
        if submitted:
            if amount <= 0:
                st.error("Budget amount must be greater than zero")
            else:
                # Create budget
                create_budget(
                    db=db_session,
                    user_id=user.id,
                    category=category,
                    amount=amount,
                    period=period,
                    start_date=start_date,
                    end_date=end_date
                )
                
                st.success("Budget added successfully!")
                st.rerun()
    
    # Zero-based budget planner
    st.markdown("### Zero-Based Budget Planner")
    st.info("Zero-based budgeting means assigning a purpose to every rupee of your income.")
    
    # Get current month income
    current_month = date.today().month
    current_year = date.today().year
    monthly_income = db_session.query(User).filter(User.id == user.id).first().income_sources
    
    # Calculate estimated monthly income
    estimated_income = 0
    for source in monthly_income:
        if source.frequency == "monthly":
            estimated_income += source.amount
        elif source.frequency == "quarterly":
            estimated_income += source.amount / 3
        elif source.frequency == "annually":
            estimated_income += source.amount / 12
    
    # Create zero-based budget form
    st.markdown(f"Estimated Monthly Income: **₹{estimated_income:,.2f}**")
    
    # Get current budgets
    current_budgets = db_session.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.period == "monthly"
    ).all()
    
    # Get total budgeted amount
    total_budgeted = sum(budget.amount for budget in current_budgets)
    remaining_to_budget = estimated_income - total_budgeted
    
    st.markdown(f"Total Budgeted: **₹{total_budgeted:,.2f}**")
    st.markdown(f"Remaining to Budget: **₹{remaining_to_budget:,.2f}**")
    
    # Show progress bar for budgeted vs income
    budget_percent = (total_budgeted / estimated_income * 100) if estimated_income > 0 else 0
    st.progress(min(budget_percent / 100, 1.0))
    
    # Budget allocation recommendation
    if estimated_income > 0:
        st.markdown("### Recommended Budget Allocation")
        
        # Common budget allocation percentages
        recommended_allocations = {
            "Housing": 30,
            "Transportation": 15,
            "Food": 15,
            "Utilities": 10,
            "Savings": 10,
            "Debt Payments": 10,
            "Entertainment": 5,
            "Healthcare": 5
        }
        
        allocation_data = []
        for category, percentage in recommended_allocations.items():
            amount = (percentage / 100) * estimated_income
            allocation_data.append({
                "category": category,
                "percentage": percentage,
                "amount": amount
            })
        
        st.dataframe(
            allocation_data,
            column_config={
                "category": "Category",
                "percentage": st.column_config.NumberColumn(
                    "Recommended %",
                    format="%.1f%%"
                ),
                "amount": st.column_config.NumberColumn(
                    "Recommended Amount",
                    format="₹%.2f"
                )
            },
            hide_index=True
        )

def show_budget_performance(user):
    """Show budget performance section"""
    st.subheader("Budget Performance Analysis")
    
    # Date range selection
    col1, col2 = st.columns(2)
    
    with col1:
        month_options = [
            (1, "January"), (2, "February"), (3, "March"), 
            (4, "April"), (5, "May"), (6, "June"),
            (7, "July"), (8, "August"), (9, "September"),
            (10, "October"), (11, "November"), (12, "December")
        ]
        
        selected_month = st.selectbox(
            "Select Month",
            options=[m[0] for m in month_options],
            format_func=lambda x: next((m[1] for m in month_options if m[0] == x), ""),
            index=date.today().month - 1
        )
    
    with col2:
        current_year = date.today().year
        year_options = list(range(current_year - 2, current_year + 1))
        selected_year = st.selectbox("Select Year", year_options, index=2)
    
    # Get budget performance for selected month
    budget_perf = get_budget_performance(user.id, db_session, selected_month, selected_year)
    
    if not budget_perf["categories"]:
        st.info(f"No budget data available for {month_options[selected_month-1][1]} {selected_year}.")
        return
    
    # Budget vs Actual Chart
    budget_chart = budget_vs_actual_chart(budget_perf)
    st.plotly_chart(budget_chart, use_container_width=True)
    
    # Performance Details
    st.subheader("Performance Details")
    
    # Convert to dataframe for display
    performance_data = []
    for category, data in budget_perf["categories"].items():
        variance_percent = data["variance_percent"]
        status = "On Track" if data["variance"] >= 0 else "Over Budget"
        
        performance_data.append({
            "category": category,
            "budget": data["budget"],
            "actual": data["actual"],
            "variance": data["variance"],
            "variance_percent": variance_percent,
            "status": status
        })
    
    # Sort by variance percent
    performance_data.sort(key=lambda x: x["variance_percent"])
    
    df = pd.DataFrame(performance_data)
    
    st.dataframe(
        df,
        column_config={
            "category": "Category",
            "budget": st.column_config.NumberColumn(
                "Budget",
                format="₹%.2f"
            ),
            "actual": st.column_config.NumberColumn(
                "Actual",
                format="₹%.2f"
            ),
            "variance": st.column_config.NumberColumn(
                "Variance",
                format="₹%.2f",
                help="Positive value means under budget, negative means over budget"
            ),
            "variance_percent": st.column_config.NumberColumn(
                "Variance %",
                format="%.1f%%"
            ),
            "status": "Status"
        },
        hide_index=True
    )
    
    # Historical Budget Performance
    st.subheader("Historical Budget Performance")
    
    # Get data for the last 6 months
    months = []
    total_budgets = []
    total_actuals = []
    
    end_date = date(selected_year, selected_month, 1)
    
    for i in range(6):
        # Calculate month and year
        month = end_date.month - i
        year = end_date.year
        
        # Adjust for previous year
        if month <= 0:
            month += 12
            year -= 1
        
        # Get performance data
        perf = get_budget_performance(user.id, db_session, month, year)
        
        month_name = month_options[month-1][1]
        month_key = f"{month_name[:3]} {year}"
        
        months.append(month_key)
        total_budgets.append(perf["total"]["budget"])
        total_actuals.append(perf["total"]["actual"])
    
    # Reverse lists to get chronological order
    months.reverse()
    total_budgets.reverse()
    total_actuals.reverse()
    
    # Create historical chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=months,
        y=total_budgets,
        name="Budget",
        marker_color="blue"
    ))
    
    fig.add_trace(go.Bar(
        x=months,
        y=total_actuals,
        name="Actual",
        marker_color="red"
    ))
    
    fig.update_layout(
        title="Budget vs Actual - Last 6 Months",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        barmode="group",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Budget Adjustment Recommendations
    st.subheader("Budget Adjustment Recommendations")
    
    # Find categories consistently over or under budget
    over_budget_categories = [item for item in performance_data if item["status"] == "Over Budget"]
    under_budget_categories = [item for item in performance_data if item["status"] == "On Track" and item["variance_percent"] > 20]
    
    if over_budget_categories:
        st.markdown("#### Categories to Increase Budget")
        
        for category in over_budget_categories:
            st.markdown(
                f"- **{category['category']}**: Current budget is ₹{category['budget']:,.2f}, but you spent "
                f"₹{category['actual']:,.2f}. Consider increasing budget by at least "
                f"₹{-category['variance']:,.2f} ({-category['variance_percent']:.1f}%)."
            )
    
    if under_budget_categories:
        st.markdown("#### Categories to Decrease Budget")
        
        for category in under_budget_categories:
            st.markdown(
                f"- **{category['category']}**: Current budget is ₹{category['budget']:,.2f}, but you only spent "
                f"₹{category['actual']:,.2f}. Consider decreasing budget by "
                f"₹{category['variance']:,.2f} ({category['variance_percent']:.1f}%)."
            )
    
    if not over_budget_categories and not under_budget_categories:
        st.success("Your budgets are well-balanced! No major adjustments needed.")