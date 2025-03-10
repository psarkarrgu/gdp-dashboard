import streamlit as st
import os
import sys
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db_session
from database.models import User, TaxDeduction, TaxDeductionType, Investment, Insurance, Debt
from database.operations import (
    get_tax_deductions, create_tax_deduction, update_tax_deduction, delete_tax_deduction,
    get_investments, get_debts, get_insurances
)
from utils.tax_utils import (
    calculate_tax_liability, suggest_tax_saving_investments, generate_tax_timeline,
    calculate_hra_exemption
)
from utils.visualization import (
    tax_comparison_chart, deduction_breakdown_chart
)
from utils.auth_utils import require_auth
from config import TAX_YEAR

def show_tax_planning_page(user):
    """Display the tax planning page"""
    require_auth()
    
    st.markdown("<h1 class='main-header'>Tax Planning & Optimization</h1>", unsafe_allow_html=True)
    
    # Tax Year Selection
    tax_years = [TAX_YEAR, "2023-24", "2022-23"]  # Add more years as needed
    selected_year = st.selectbox("Select Financial Year", tax_years)
    
    # Tax Regime Preference
    st.markdown("### Tax Regime Preference")
    current_regime = user.tax_regime
    new_regime = st.radio(
        "Your currently selected tax regime",
        ["old", "new"],
        index=0 if current_regime == "old" else 1,
        horizontal=True,
        help="This is your preference for tax calculation. We'll still show you comparison between both regimes."
    )
    
    if new_regime != current_regime:
        if st.button("Update Tax Regime Preference"):
            user.tax_regime = new_regime
            db_session.commit()
            st.success(f"Tax regime preference updated to {new_regime} regime")
            st.rerun()
    
    # Calculate Tax Liability
    tax_data = calculate_tax_liability(user.id, db_session, selected_year)
    
    # Tax Comparison Section
    st.markdown("### Tax Liability Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        old_regime_tax = tax_data["old_regime"]["total_tax"]
        new_regime_tax = tax_data["new_regime"]["total_tax"]
        
        better_regime = tax_data["better_regime"]
        savings = tax_data["tax_savings"]
        
        st.metric(
            "Old Tax Regime",
            f"₹{old_regime_tax:,.2f}",
            f"{-savings:,.2f}" if better_regime == "new" else None
        )
    
    with col2:
        st.metric(
            "New Tax Regime",
            f"₹{new_regime_tax:,.2f}",
            f"{-savings:,.2f}" if better_regime == "old" else None
        )
    
    # Recommendation
    st.info(
        f"Based on your current financial situation, the **{better_regime.upper()} TAX REGIME** "
        f"would be better for you, saving you **₹{savings:,.2f}**."
    )
    
    # Tax Comparison Chart
    tax_chart = tax_comparison_chart(tax_data)
    st.plotly_chart(tax_chart, use_container_width=True)
    
    # Income Breakdown
    st.markdown("### Income & Deduction Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Gross Income")
        st.markdown(f"Total Gross Income: **₹{tax_data['gross_income']:,.2f}**")
        st.markdown("---")
        st.markdown("#### Income Breakdown (TODO)")
        st.info("Add your income sources to see detailed breakdown")
    
    with col2:
        st.subheader("Deductions (Old Regime)")
        
        # Deduction chart
        if tax_data["old_regime"]["deductions"]:
            deduction_chart = deduction_breakdown_chart(tax_data["old_regime"]["deductions"])
            st.plotly_chart(deduction_chart, use_container_width=True)
        else:
            st.info("No deductions found")
    
    # Tabs for different tax planning features
    tab1, tab2, tab3, tab4 = st.tabs([
        "Tax Deductions", "Tax Saving Recommendations", "HRA Exemption Calculator", "Tax Timeline"
    ])
    
    # Tax Deductions Tab
    with tab1:
        show_tax_deductions_tab(user, selected_year)
    
    # Tax Saving Recommendations Tab
    with tab2:
        show_tax_saving_recommendations_tab(user, selected_year)
    
    # HRA Exemption Calculator Tab
    with tab3:
        show_hra_exemption_calculator_tab(user)
    
    # Tax Timeline Tab
    with tab4:
        show_tax_timeline_tab(selected_year)

def show_tax_deductions_tab(user, selected_year):
    """Show tax deductions management tab"""
    st.subheader("Manage Tax Deductions")
    
    # Get current deductions
    deductions = get_tax_deductions(db_session, user.id, financial_year=selected_year)
    
    # Display existing deductions in a table
    if deductions:
        deduction_data = []
        for deduction in deductions:
            deduction_data.append({
                "id": deduction.id,
                "type": deduction.deduction_type.value,
                "amount": deduction.amount,
                "description": deduction.description or ""
            })
        
        df = pd.DataFrame(deduction_data)
        st.dataframe(
            df,
            column_config={
                "id": None,  # Hide ID column
                "type": "Deduction Type",
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    format="₹%.2f"
                ),
                "description": "Description"
            },
            hide_index=True
        )
        
        # Calculate total deductions
        total_deductions = sum(deduction.amount for deduction in deductions)
        st.markdown(f"Total Deductions: **₹{total_deductions:,.2f}**")
    else:
        st.info("No tax deductions recorded for this financial year")
    
    # Add new deduction
    st.markdown("### Add New Deduction")
    
    with st.form("add_deduction_form"):
        # Get deduction type options
        deduction_types = [
            ("80C", "Section 80C (PPF, ELSS, Life Insurance, etc.)"),
            ("80D", "Section 80D (Health Insurance Premium)"),
            ("80E", "Section 80E (Education Loan Interest)"),
            ("80EE", "Section 80EE/EEA (Home Loan Interest for First-Time Buyers)"),
            ("80G", "Section 80G (Donations)"),
            ("80CCD", "Section 80CCD (NPS Contribution)"),
            ("HRA", "House Rent Allowance Exemption"),
            ("LTA", "Leave Travel Allowance"),
            ("HOME_LOAN_INTEREST", "Home Loan Interest (Section 24)"),
            ("OTHER", "Other Deductions")
        ]
        
        deduction_type = st.selectbox(
            "Deduction Type",
            options=[d[0] for d in deduction_types],
            format_func=lambda x: next((d[1] for d in deduction_types if d[0] == x), x)
        )
        
        amount = st.number_input("Amount (₹)", min_value=0.0, step=1000.0)
        description = st.text_area("Description (Optional)")
        
        submitted = st.form_submit_button("Add Deduction")
        
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than zero")
            else:
                # Create deduction
                create_tax_deduction(
                    db=db_session,
                    user_id=user.id,
                    deduction_type=deduction_type,
                    amount=amount,
                    financial_year=selected_year,
                    description=description
                )
                
                st.success("Tax deduction added successfully!")
                st.rerun()

def show_tax_saving_recommendations_tab(user, selected_year):
    """Show tax saving recommendations tab"""
    st.subheader("Tax Saving Recommendations")
    
    # Get tax saving suggestions
    suggestions = suggest_tax_saving_investments(user.id, db_session, selected_year)
    
    if suggestions:
        for section, data in suggestions.items():
            with st.expander(f"{section} - ₹{data['remaining']:,.2f} remaining out of ₹{data['limit']:,.2f}"):
                st.progress(data['current'] / data['limit'])
                st.markdown(f"Current Utilization: **₹{data['current']:,.2f}** / **₹{data['limit']:,.2f}**")
                
                st.markdown("#### Recommended Tax-Saving Options")
                for option in data['options']:
                    st.markdown(f"**{option['name']}**: {option['description']}")
    else:
        st.info("You have maximized all your tax-saving options. Great job!")
    
    # Investment Eligibility Check
    st.markdown("### Check Your Investment Eligibility")
    
    investment_checks = [
        {
            "name": "Public Provident Fund (PPF)",
            "section": "80C",
            "condition": True,  # Everyone is eligible
            "max_amount": 150000,
            "description": "Long-term savings with tax benefits, 15-year lock-in period"
        },
        {
            "name": "Sukanya Samriddhi Yojana",
            "section": "80C",
            "condition": False,  # Need to check if user has a girl child
            "max_amount": 150000,
            "description": "Savings scheme for girl child, higher interest rates"
        },
        {
            "name": "National Pension System (NPS)",
            "section": "80CCD(1B)",
            "condition": user.date_of_birth and (datetime.now().year - user.date_of_birth.year) < 60,
            "max_amount": 50000,
            "description": "Additional tax benefit beyond 80C limit for NPS contributions"
        },
        {
            "name": "Senior Citizen Savings Scheme",
            "section": "80C",
            "condition": user.date_of_birth and (datetime.now().year - user.date_of_birth.year) >= 60,
            "max_amount": 150000,
            "description": "High interest savings scheme for senior citizens"
        }
    ]
    
    eligible_investments = [inv for inv in investment_checks if inv["condition"]]
    
    if eligible_investments:
        st.markdown("Based on your profile, you are eligible for these tax-saving investments:")
        
        for investment in eligible_investments:
            st.markdown(
                f"**{investment['name']}** (Section {investment['section']}) - "
                f"Max: ₹{investment['max_amount']:,}\n\n"
                f"{investment['description']}"
            )
            st.markdown("---")
    else:
        st.info("Please complete your profile to check eligible tax-saving investments")

def show_hra_exemption_calculator_tab(user):
    """Show HRA exemption calculator tab"""
    st.subheader("HRA Exemption Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        basic_salary = st.number_input("Basic Salary per month (₹)", min_value=0.0, step=1000.0)
        hra_received = st.number_input("HRA Received per month (₹)", min_value=0.0, step=1000.0)
    
    with col2:
        rent_paid = st.number_input("Rent Paid per month (₹)", min_value=0.0, step=1000.0)
        is_metro = st.checkbox("Living in Metro City (Delhi, Mumbai, Chennai, Kolkata)")
    
    if st.button("Calculate HRA Exemption"):
        if basic_salary > 0 and rent_paid > 0:
            # Calculate monthly exemption
            monthly_exemption = calculate_hra_exemption(basic_salary, hra_received, rent_paid, is_metro)
            
            # Annualize for the year
            annual_exemption = monthly_exemption * 12
            
            st.markdown("### HRA Exemption Calculation")
            
            # Create a dataframe for the calculation
            calculation_data = pd.DataFrame([
                {"Description": "Actual HRA received", "Monthly": hra_received, "Annually": hra_received * 12},
                {"Description": "Rent paid in excess of 10% of basic salary", "Monthly": max(0, rent_paid - (0.1 * basic_salary)), "Annually": max(0, rent_paid - (0.1 * basic_salary)) * 12},
                {"Description": "50% of basic salary (metro) or 40% of basic salary (non-metro)", "Monthly": basic_salary * (0.5 if is_metro else 0.4), "Annually": basic_salary * (0.5 if is_metro else 0.4) * 12},
                {"Description": "HRA Exemption (Minimum of above three)", "Monthly": monthly_exemption, "Annually": annual_exemption}
            ])
            
            st.dataframe(
                calculation_data,
                column_config={
                    "Description": "Description",
                    "Monthly": st.column_config.NumberColumn(
                        "Monthly (₹)",
                        format="₹%.2f"
                    ),
                    "Annually": st.column_config.NumberColumn(
                        "Annually (₹)",
                        format="₹%.2f"
                    )
                },
                hide_index=True
            )
            
            st.success(f"Your HRA exemption amount is **₹{annual_exemption:,.2f}** per year")
            
            # Show add to deductions button
            if st.button("Add to Tax Deductions"):
                # Check if HRA deduction already exists for this financial year
                existing_hra = db_session.query(TaxDeduction).filter(
                    TaxDeduction.user_id == user.id,
                    TaxDeduction.deduction_type == TaxDeductionType.HRA,
                    TaxDeduction.financial_year == TAX_YEAR
                ).first()
                
                if existing_hra:
                    # Update existing deduction
                    update_tax_deduction(
                        db=db_session,
                        deduction_id=existing_hra.id,
                        user_id=user.id,
                        amount=annual_exemption,
                        description=f"HRA Exemption for Basic: ₹{basic_salary}, Rent: ₹{rent_paid}, Metro: {is_metro}"
                    )
                    st.success("Updated HRA exemption in your tax deductions!")
                else:
                    # Create new deduction
                    create_tax_deduction(
                        db=db_session,
                        user_id=user.id,
                        deduction_type="HRA",
                        amount=annual_exemption,
                        financial_year=TAX_YEAR,
                        description=f"HRA Exemption for Basic: ₹{basic_salary}, Rent: ₹{rent_paid}, Metro: {is_metro}"
                    )
                    st.success("Added HRA exemption to your tax deductions!")
        else:
            st.error("Please enter valid values for Basic Salary and Rent Paid")

def show_tax_timeline_tab(selected_year):
    """Show tax timeline tab"""
    st.subheader("Tax Calendar & Important Dates")
    
    # Get tax timeline
    timeline = generate_tax_timeline(selected_year)
    
    # Create a dataframe for display
    timeline_data = pd.DataFrame([
        {
            "Date": item["date"].strftime("%d %b %Y"),
            "Event": item["title"],
            "Description": item["description"]
        }
        for item in timeline
    ])
    
    # Display the timeline
    st.dataframe(
        timeline_data,
        column_config={
            "Date": "Date",
            "Event": "Event",
            "Description": "Description"
        },
        hide_index=True
    )
    
    # Show calendar view
    st.markdown("### Calendar View")
    
    # Create a dictionary to map month names to numbers
    months = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    
    # Get year from selected tax year
    year_start, year_end = selected_year.split("-")
    calendar_year = int(year_start)
    
    # Allow user to select month
    selected_month = st.selectbox("Select Month", list(months.keys()))
    month_number = months[selected_month]
    
    # Adjust year for Jan-Mar (which would be in the next calendar year)
    if month_number < 4:
        calendar_year = int(year_end)
    
    # Filter events for selected month
    month_events = [
        event for event in timeline 
        if event["date"].month == month_number and event["date"].year == calendar_year
    ]
    
    # Display events for selected month
    if month_events:
        for event in month_events:
            event_date = event["date"]
            st.markdown(
                f"""
                <div style="border-left: 3px solid #1E88E5; padding-left: 10px; margin-bottom: 10px;">
                    <div style="font-weight: bold;">{event_date.strftime('%d %b %Y')} - {event["title"]}</div>
                    <div>{event["description"]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info(f"No tax events in {selected_month} {calendar_year}")