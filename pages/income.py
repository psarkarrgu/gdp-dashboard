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
from database.models import User, IncomeSource, IncomeSourceType, IncomeTransaction
from database.operations import (
    get_income_sources, create_income_source, update_income_source, delete_income_source,
    get_income_transactions, create_income_transaction
)
from utils.finance_utils import (
    calculate_monthly_income
)
from utils.auth_utils import require_auth

def show_income_page(user):
    """Display the income page"""
    require_auth()
    
    st.markdown("<h1 class='main-header'>Income Tracking</h1>", unsafe_allow_html=True)
    
    # Income tabs
    tab1, tab2 = st.tabs(["Income Sources", "Income Transactions"])
    
    with tab1:
        show_income_sources(user)
    
    with tab2:
        show_income_transactions(user)

def show_income_sources(user):
    """Show income sources management"""
    st.subheader("Manage Income Sources")
    
    # Get user's income sources
    income_sources = get_income_sources(db_session, user.id)
    
    # Display existing income sources
    if income_sources:
        source_data = []
        for source in income_sources:
            source_data.append({
                "id": source.id,
                "name": source.name,
                "type": source.source_type,
                "amount": source.amount,
                "frequency": source.frequency,
                "is_taxable": "Yes" if source.is_taxable else "No",
                "start_date": source.start_date,
                "end_date": source.end_date
            })
        
        df = pd.DataFrame(source_data)
        
        # Edit/Delete functionality
        selected_source = st.selectbox(
            "Select income source to edit or delete",
            options=df["id"].tolist(),
            format_func=lambda x: next((source["name"] for source in source_data if source["id"] == x), str(x))
        )
        
        # Get selected source
        selected_src = next((source for source in income_sources if source.id == selected_source), None)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.dataframe(
                df,
                column_config={
                    "id": None,  # Hide ID column
                    "name": "Name",
                    "type": "Type",
                    "amount": st.column_config.NumberColumn(
                        "Amount",
                        format="₹%.2f"
                    ),
                    "frequency": "Frequency",
                    "is_taxable": "Taxable",
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
            if selected_src:
                # Update amount
                new_amount = st.number_input(
                    "Update Amount",
                    min_value=0.0,
                    value=float(selected_src.amount),
                    step=1000.0
                )
                
                if st.button("Update Amount"):
                    update_income_source(
                        db=db_session,
                        income_source_id=selected_src.id,
                        user_id=user.id,
                        amount=new_amount
                    )
                    st.success("Income source updated!")
                    st.rerun()
                
                if st.button("Delete Source", type="secondary"):
                    delete_income_source(db_session, selected_src.id, user.id)
                    st.success("Income source deleted successfully!")
                    st.rerun()
    else:
        st.info("You don't have any income sources yet. Add one below.")
    
    # Add new income source
    st.markdown("### Add New Income Source")
    
    with st.form("add_income_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Income Source Name")
            
            # Get source type options from enum
            source_types = []
            for src_type in IncomeSourceType:
                source_types.append((src_type.value, src_type.name.replace("_", " ").title()))
            
            source_type = st.selectbox(
                "Income Type",
                options=[t[0] for t in source_types],
                format_func=lambda x: next((t[1] for t in source_types if t[0] == x), x)
            )
            
            amount = st.number_input("Amount (₹)", min_value=0.0, step=1000.0)
            
            frequency = st.selectbox(
                "Frequency",
                ["monthly", "quarterly", "annually", "one-time"]
            )
        
        with col2:
            is_taxable = st.checkbox("Is this income taxable?", value=True)
            start_date = st.date_input("Start Date", max_value=date.today())
            end_date = st.date_input("End Date (leave blank if ongoing)", value=None)
            description = st.text_area("Description")
        
        # Salary specific fields
        if source_type == "salary":
            st.markdown("### Salary Breakdown")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                basic_pay = st.number_input("Basic Pay", min_value=0.0, step=1000.0)
                hra = st.number_input("HRA", min_value=0.0, step=1000.0)
            
            with col2:
                special_allowance = st.number_input("Special Allowance", min_value=0.0, step=1000.0)
                transport_allowance = st.number_input("Transport Allowance", min_value=0.0, step=1000.0)
            
            with col3:
                medical_allowance = st.number_input("Medical Allowance", min_value=0.0, step=1000.0)
                professional_tax = st.number_input("Professional Tax", min_value=0.0, step=100.0)
        else:
            basic_pay = None
            hra = None
            special_allowance = None
            transport_allowance = None
            medical_allowance = None
            professional_tax = None
        
        submitted = st.form_submit_button("Add Income Source")
        
        if submitted:
            if not name:
                st.error("Please enter an income source name")
            elif amount <= 0:
                st.error("Amount must be greater than zero")
            else:
                # Create income source
                create_income_source(
                    db=db_session,
                    user_id=user.id,
                    name=name,
                    source_type=source_type,
                    amount=amount,
                    frequency=frequency,
                    is_taxable=is_taxable,
                    start_date=start_date,
                    end_date=end_date,
                    description=description,
                    basic_pay=basic_pay,
                    hra=hra,
                    special_allowance=special_allowance,
                    transport_allowance=transport_allowance,
                    medical_allowance=medical_allowance,
                    professional_tax=professional_tax
                )
                
                st.success("Income source added successfully!")
                st.rerun()

def show_income_transactions(user):
    """Show income transactions"""
    st.subheader("Income Transactions")
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=date(date.today().year, 1, 1))
    with col2:
        end_date = st.date_input("To", value=date.today())
    
    # Get transactions
    transactions = get_income_transactions(db_session, user.id, start_date, end_date)
    
    # Display transactions
    if transactions:
        transaction_data = []
        for transaction in transactions:
            source = transaction.income_source
            transaction_data.append({
                "id": transaction.id,
                "source": source.name,
                "amount": transaction.amount,
                "date": transaction.date,
                "description": transaction.description or ""
            })
        
        df = pd.DataFrame(transaction_data)
        
        st.dataframe(
            df,
            column_config={
                "id": None,  # Hide ID column
                "source": "Income Source",
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
        
        # Calculate total
        total_income = sum(t.amount for t in transactions)
        st.metric("Total Income", f"₹{total_income:,.2f}")
        
        # Create monthly chart
        income_by_month = {}
        for t in transactions:
            month_key = t.date.strftime("%Y-%m")
            if month_key not in income_by_month:
                income_by_month[month_key] = 0
            income_by_month[month_key] += t.amount
        
        if income_by_month:
            chart_data = pd.DataFrame({
                "Month": list(income_by_month.keys()),
                "Income": list(income_by_month.values())
            })
            
            fig = px.bar(
                chart_data,
                x="Month",
                y="Income",
                title="Monthly Income",
                labels={"Month": "Month", "Income": "Income (₹)"},
                color_discrete_sequence=["green"]
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No income transactions found for the selected period.")
    
    # Add new transaction
    st.markdown("### Add Income Transaction")
    
    # Get available income sources
    income_sources = get_income_sources(db_session, user.id)
    
    if income_sources:
        with st.form("add_transaction_form"):
            source_id = st.selectbox(
                "Income Source",
                options=[source.id for source in income_sources],
                format_func=lambda x: next((source.name for source in income_sources if source.id == x), str(x))
            )
            
            amount = st.number_input("Amount (₹)", min_value=0.0, step=1000.0)
            transaction_date = st.date_input("Date", max_value=date.today())
            description = st.text_area("Description (Optional)")
            
            submitted = st.form_submit_button("Add Transaction")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than zero")
                else:
                    # Create transaction
                    create_income_transaction(
                        db=db_session,
                        income_source_id=source_id,
                        amount=amount,
                        date=transaction_date,
                        description=description
                    )
                    
                    st.success("Income transaction added successfully!")
                    st.rerun()
    else:
        st.warning("Please add an income source first before adding transactions.")