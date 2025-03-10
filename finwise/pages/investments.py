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
from database.models import User, Investment, InvestmentType
from database.operations import (
    get_investments, create_investment, update_investment, delete_investment
)
from utils.finance_utils import (
    calculate_investment_returns, calculate_asset_allocation, calculate_sip_returns
)
from utils.visualization import (
    investment_performance_chart, asset_allocation_chart
)
from utils.auth_utils import require_auth
from config import INVESTMENT_CATEGORIES

def show_investments_page(user):
    """Display the investments page"""
    require_auth()
    
    st.markdown("<h1 class='main-header'>Investment Portfolio Management</h1>", unsafe_allow_html=True)
    
    # Investment Navigation
    tab1, tab2, tab3, tab4 = st.tabs([
        "Portfolio Overview", "Manage Investments", "SIP Calculator", "Asset Allocation"
    ])
    
    # Portfolio Overview Tab
    with tab1:
        show_portfolio_overview(user)
    
    # Manage Investments Tab
    with tab2:
        show_manage_investments(user)
    
    # SIP Calculator Tab
    with tab3:
        show_sip_calculator()
    
    # Asset Allocation Tab
    with tab4:
        show_asset_allocation(user)

def show_portfolio_overview(user):
    """Show portfolio overview section"""
    st.subheader("Portfolio Overview")
    
    # Get user investments
    investments = get_investments(db_session, user.id)
    
    if not investments:
        st.info("You don't have any investments yet. Add some in the 'Manage Investments' tab.")
        return
    
    # Calculate investment returns
    returns_data = calculate_investment_returns(user.id, db_session)
    
    # Display portfolio summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Invested",
            f"₹{returns_data['total']['invested']:,.2f}"
        )
    
    with col2:
        st.metric(
            "Current Value",
            f"₹{returns_data['total']['current_value']:,.2f}",
            f"{returns_data['total']['absolute_return_percent']:.2f}%"
        )
    
    with col3:
        absolute_return = returns_data['total']['absolute_return']
        st.metric(
            "Total Returns",
            f"₹{absolute_return:,.2f}",
            delta_color="normal" if absolute_return >= 0 else "inverse"
        )
    
    # Show investment performance chart
    if returns_data['investments']:
        st.subheader("Investment Performance")
        performance_chart = investment_performance_chart(returns_data)
        st.plotly_chart(performance_chart, use_container_width=True)
    
    # Show investments table
    st.subheader("Investment Details")
    
    # Prepare data for table
    investment_data = []
    for name, data in returns_data['investments'].items():
        investment_data.append({
            "name": name,
            "type": data["type"],
            "initial_investment": data["initial_investment"],
            "current_value": data["current_value"],
            "absolute_return": data["absolute_return"],
            "absolute_return_percent": data["absolute_return_percent"],
            "annualized_return_percent": data["annualized_return_percent"],
            "days_held": data["days_held"] or 0
        })
    
    df = pd.DataFrame(investment_data)
    
    # Sort by current value
    df = df.sort_values("current_value", ascending=False)
    
    # Display the table
    st.dataframe(
        df,
        column_config={
            "name": "Investment Name",
            "type": "Type",
            "initial_investment": st.column_config.NumberColumn(
                "Initial Investment",
                format="₹%.2f"
            ),
            "current_value": st.column_config.NumberColumn(
                "Current Value",
                format="₹%.2f"
            ),
            "absolute_return": st.column_config.NumberColumn(
                "Absolute Return",
                format="₹%.2f"
            ),
            "absolute_return_percent": st.column_config.NumberColumn(
                "Return (%)",
                format="%.2f%%"
            ),
            "annualized_return_percent": st.column_config.NumberColumn(
                "Annualized Return (%)",
                format="%.2f%%"
            ),
            "days_held": "Days Held"
        },
        hide_index=True
    )
    
    # Tax-saving investments section
    st.subheader("Tax-Saving Investments")
    
    tax_saving_investments = [inv for inv in investments if inv.is_tax_saving]
    
    if tax_saving_investments:
        tax_data = []
        total_tax_saving_amount = 0
        
        for inv in tax_saving_investments:
            amount = inv.current_value or inv.amount
            tax_data.append({
                "name": inv.name,
                "type": inv.investment_type,
                "amount": amount,
                "tax_section": inv.tax_section or "Not specified"
            })
            total_tax_saving_amount += amount
        
        tax_df = pd.DataFrame(tax_data)
        
        st.dataframe(
            tax_df,
            column_config={
                "name": "Investment Name",
                "type": "Type",
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    format="₹%.2f"
                ),
                "tax_section": "Tax Section"
            },
            hide_index=True
        )
        
        st.metric("Total Tax-Saving Investments", f"₹{total_tax_saving_amount:,.2f}")
    else:
        st.info("You don't have any tax-saving investments yet.")

def show_manage_investments(user):
    """Show manage investments section"""
    st.subheader("Manage Your Investments")
    
    # Get user investments
    investments = get_investments(db_session, user.id)
    
    # Display existing investments in a table
    if investments:
        investment_data = []
        for inv in investments:
            investment_data.append({
                "id": inv.id,
                "name": inv.name,
                "type": inv.investment_type,
                "amount": inv.amount,
                "current_value": inv.current_value or inv.amount,
                "purchase_date": inv.purchase_date,
                "is_tax_saving": "Yes" if inv.is_tax_saving else "No",
                "is_sip": "Yes" if inv.is_sip else "No"
            })
        
        df = pd.DataFrame(investment_data)
        
        # Edit/Delete functionality
        selected_investment = st.selectbox(
            "Select investment to edit or delete",
            options=df["id"].tolist(),
            format_func=lambda x: next((inv["name"] for inv in investment_data if inv["id"] == x), str(x))
        )
        
        # Get selected investment
        selected_inv = next((inv for inv in investments if inv.id == selected_investment), None)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.dataframe(
                df,
                column_config={
                    "id": None,  # Hide ID column
                    "name": "Name",
                    "type": "Type",
                    "amount": st.column_config.NumberColumn(
                        "Initial Amount",
                        format="₹%.2f"
                    ),
                    "current_value": st.column_config.NumberColumn(
                        "Current Value",
                        format="₹%.2f"
                    ),
                    "purchase_date": st.column_config.DateColumn(
                        "Purchase Date",
                        format="DD-MM-YYYY"
                    ),
                    "is_tax_saving": "Tax Saving",
                    "is_sip": "SIP"
                },
                hide_index=True
            )
        
        with col2:
            if selected_inv:
                # Update current value
                new_value = st.number_input(
                    "Update Current Value",
                    min_value=0.0,
                    value=float(selected_inv.current_value or selected_inv.amount),
                    step=1000.0
                )
                
                if st.button("Update Value"):
                    update_investment(
                        db=db_session,
                        investment_id=selected_inv.id,
                        user_id=user.id,
                        current_value=new_value
                    )
                    st.success("Investment value updated!")
                    st.rerun()
                
                if st.button("Delete Investment", type="secondary"):
                    delete_investment(db_session, selected_inv.id, user.id)
                    st.success("Investment deleted successfully!")
                    st.rerun()
    else:
        st.info("You don't have any investments yet. Add one below.")
    
    # Add new investment
    st.markdown("### Add New Investment")
    
    with st.form("add_investment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Investment Name")
            
            # Get investment type options from enum
            investment_types = []
            for inv_type in InvestmentType:
                investment_types.append((inv_type.value, inv_type.name.replace("_", " ").title()))
            
            investment_type = st.selectbox(
                "Investment Type",
                options=[t[0] for t in investment_types],
                format_func=lambda x: next((t[1] for t in investment_types if t[0] == x), x)
            )
            
            amount = st.number_input("Initial Investment Amount (₹)", min_value=0.0, step=1000.0)
            current_value = st.number_input("Current Value (₹)", min_value=0.0, step=1000.0)
        
        with col2:
            purchase_date = st.date_input("Purchase Date", max_value=date.today())
            maturity_date = st.date_input("Maturity Date (if applicable)", value=None)
            interest_rate = st.number_input("Interest Rate/Expected Return (%)", min_value=0.0, max_value=100.0, step=0.1)
            
            is_tax_saving = st.checkbox("Is this a tax-saving investment?")
            
            tax_section = None
            if is_tax_saving:
                tax_sections = [
                    "80C", "80CCC", "80CCD", "80D", "80E", "80EE", "80G", "Other"
                ]
                tax_section = st.selectbox("Tax Section", tax_sections)
        
        col1, col2 = st.columns(2)
        
        with col1:
            is_sip = st.checkbox("Is this a Systematic Investment Plan (SIP)?")
            
            sip_amount = None
            sip_frequency = None
            if is_sip:
                sip_amount = st.number_input("SIP Amount (₹)", min_value=0.0, step=500.0)
                sip_frequency = st.selectbox(
                    "SIP Frequency",
                    ["monthly", "quarterly", "half-yearly", "yearly"]
                )
        
        with col2:
            description = st.text_area("Notes/Description")
        
        submitted = st.form_submit_button("Add Investment")
        
        if submitted:
            if not name:
                st.error("Please enter an investment name")
            elif amount <= 0:
                st.error("Initial investment amount must be greater than zero")
            else:
                # Create investment
                create_investment(
                    db=db_session,
                    user_id=user.id,
                    name=name,
                    investment_type=investment_type,
                    amount=amount,
                    current_value=current_value if current_value > 0 else amount,
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
                
                st.success("Investment added successfully!")
                st.rerun()

def show_sip_calculator():
    """Show SIP calculator section"""
    st.subheader("SIP Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_investment = st.number_input("Monthly Investment Amount (₹)", min_value=500, step=500, value=5000)
        expected_return = st.number_input("Expected Annual Return (%)", min_value=1.0, max_value=30.0, value=12.0, step=0.5)
    
    with col2:
        tenure_years = st.number_input("Investment Period (Years)", min_value=1, max_value=40, value=10, step=1)
        inflation_rate = st.number_input("Expected Inflation Rate (%)", min_value=0.0, max_value=20.0, value=6.0, step=0.5)
    
    # Calculate SIP returns
    if st.button("Calculate Returns"):
        sip_returns = calculate_sip_returns(monthly_investment, expected_return, tenure_years)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Investment",
                f"₹{sip_returns['total_invested']:,.2f}"
            )
        
        with col2:
            st.metric(
                "Expected Future Value",
                f"₹{sip_returns['future_value']:,.2f}"
            )
        
        with col3:
            st.metric(
                "Wealth Gained",
                f"₹{sip_returns['wealth_gained']:,.2f}",
                f"{sip_returns['absolute_return_percent']:.2f}%"
            )
        
        # Calculate inflation-adjusted value
        inflation_adjusted_value = sip_returns['future_value'] / ((1 + (inflation_rate / 100)) ** tenure_years)
        
        st.info(f"Inflation-adjusted value: **₹{inflation_adjusted_value:,.2f}** in today's money")
        
        # Create SIP growth chart
        fig = go.Figure()
        
        # Generate data for chart
        years = list(range(tenure_years + 1))
        invested_values = [monthly_investment * 12 * year for year in years]
        
        future_values = [0]
        for year in range(1, tenure_years + 1):
            fv = monthly_investment * ((((1 + (expected_return/100/12)) ** (12 * year)) - 1) / (expected_return/100/12)) * (1 + (expected_return/100/12))
            future_values.append(fv)
        
        # Add traces
        fig.add_trace(go.Scatter(
            x=years,
            y=invested_values,
            mode='lines+markers',
            name='Amount Invested',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=years,
            y=future_values,
            mode='lines+markers',
            name='Future Value',
            line=dict(color='green')
        ))
        
        # Update layout
        fig.update_layout(
            title='SIP Growth Over Time',
            xaxis_title='Years',
            yaxis_title='Value (₹)',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # SIP vs Lump Sum comparison
        st.subheader("SIP vs Lump Sum Comparison")
        
        lump_sum_amount = monthly_investment * 12 * tenure_years
        lump_sum_future_value = lump_sum_amount * ((1 + (expected_return / 100)) ** tenure_years)
        
        comparison_data = pd.DataFrame([
            {
                "Investment Type": "SIP (Monthly)",
                "Total Investment": sip_returns['total_invested'],
                "Future Value": sip_returns['future_value'],
                "Absolute Return": sip_returns['absolute_return_percent']
            },
            {
                "Investment Type": "Lump Sum (One-time)",
                "Total Investment": lump_sum_amount,
                "Future Value": lump_sum_future_value,
                "Absolute Return": ((lump_sum_future_value - lump_sum_amount) / lump_sum_amount) * 100
            }
        ])
        
        st.dataframe(
            comparison_data,
            column_config={
                "Investment Type": "Investment Type",
                "Total Investment": st.column_config.NumberColumn(
                    "Total Investment",
                    format="₹%.2f"
                ),
                "Future Value": st.column_config.NumberColumn(
                    "Future Value",
                    format="₹%.2f"
                ),
                "Absolute Return": st.column_config.NumberColumn(
                    "Absolute Return",
                    format="%.2f%%"
                )
            },
            hide_index=True
        )

def show_asset_allocation(user):
    """Show asset allocation section"""
    st.subheader("Asset Allocation Analysis")
    
    # Get user investments
    investments = get_investments(db_session, user.id)
    
    if not investments:
        st.info("You don't have any investments yet. Add some in the 'Manage Investments' tab.")
        return
    
    # Calculate asset allocation
    allocation_data = calculate_asset_allocation(user.id, db_session)
    
    # Display asset allocation pie chart
    st.markdown("### Current Asset Allocation")
    allocation_chart = asset_allocation_chart(allocation_data)
    st.plotly_chart(allocation_chart, use_container_width=True)
    
    # Display asset allocation table
    allocation_table = []
    for asset_type, percentage in allocation_data["allocation"].items():
        allocation_table.append({
            "asset_type": asset_type,
            "percentage": percentage,
            "amount": allocation_data["allocation_amount"][asset_type]
        })
    
    df = pd.DataFrame(allocation_table)
    
    # Sort by percentage (descending)
    df = df.sort_values("percentage", ascending=False)
    
    st.dataframe(
        df,
        column_config={
            "asset_type": "Asset Type",
            "percentage": st.column_config.NumberColumn(
                "Allocation",
                format="%.2f%%"
            ),
            "amount": st.column_config.NumberColumn(
                "Amount",
                format="₹%.2f"
            )
        },
        hide_index=True
    )
    
    # Recommended asset allocation
    st.markdown("### Recommended Asset Allocation")
    
    # Get user age for age-based recommendation
    user_age = None
    if user.date_of_birth:
        today = date.today()
        user_age = today.year - user.date_of_birth.year - ((today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day))
    
    # Risk profile selection
    risk_profiles = ["Conservative", "Moderate", "Balanced", "Growth", "Aggressive"]
    
    default_profile = 2  # Balanced
    if user_age:
        if user_age < 30:
            default_profile = 4  # Aggressive
        elif user_age < 40:
            default_profile = 3  # Growth
        elif user_age < 50:
            default_profile = 2  # Balanced
        elif user_age < 60:
            default_profile = 1  # Moderate
        else:
            default_profile = 0  # Conservative
    
    risk_profile = st.select_slider(
        "Select Your Risk Profile",
        options=risk_profiles,
        value=risk_profiles[default_profile]
    )
    
    # Recommended allocations based on risk profile
    recommended_allocations = {
        "Conservative": {
            "equity": 20,
            "debt": 60,
            "gold": 15,
            "cash": 5
        },
        "Moderate": {
            "equity": 35,
            "debt": 50,
            "gold": 10,
            "cash": 5
        },
        "Balanced": {
            "equity": 50,
            "debt": 35,
            "gold": 10,
            "cash": 5
        },
        "Growth": {
            "equity": 65,
            "debt": 25,
            "gold": 5,
            "cash": 5
        },
        "Aggressive": {
            "equity": 80,
            "debt": 15,
            "gold": 0,
            "cash": 5
        }
    }
    
    selected_allocation = recommended_allocations[risk_profile]
    
    # Create pie chart for recommended allocation
    fig = px.pie(
        values=list(selected_allocation.values()),
        names=list(selected_allocation.keys()),
        title=f"Recommended Asset Allocation for {risk_profile} Risk Profile",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Allocation adjustment recommendations
    st.markdown("### Allocation Adjustment Recommendations")
    
    # Map investment types to allocation categories
    category_mapping = {
        "equity": ["equity", "mutual_fund", "elss"],
        "debt": ["fixed_deposit", "bonds", "ppf", "epf", "nps"],
        "gold": ["gold"],
        "real_estate": ["real_estate"],
        "cash": [],
        "others": ["cryptocurrency", "other"]
    }
    
    # Calculate current allocation based on categories
    current_allocation = {
        "equity": 0,
        "debt": 0,
        "gold": 0,
        "real_estate": 0,
        "cash": 0,
        "others": 0
    }
    
    # Sum up current investments by category
    for asset_type, percentage in allocation_data["allocation"].items():
        allocated = False
        for category, types in category_mapping.items():
            if asset_type in types:
                current_allocation[category] += percentage
                allocated = True
                break
        
        if not allocated:
            current_allocation["others"] += percentage
    
    # Create comparison table
    comparison_data = []
    for category in ["equity", "debt", "gold", "cash"]:
        current = current_allocation.get(category, 0)
        recommended = selected_allocation.get(category, 0)
        difference = current - recommended
        
        comparison_data.append({
            "category": category.capitalize(),
            "current": current,
            "recommended": recommended,
            "difference": difference
        })
    
    # Add real estate and others if present
    if current_allocation.get("real_estate", 0) > 0:
        comparison_data.append({
            "category": "Real Estate",
            "current": current_allocation["real_estate"],
            "recommended": 0,  # Not in standard recommendations
            "difference": current_allocation["real_estate"]
        })
    
    if current_allocation.get("others", 0) > 0:
        comparison_data.append({
            "category": "Others",
            "current": current_allocation["others"],
            "recommended": 0,  # Not in standard recommendations
            "difference": current_allocation["others"]
        })
    
    df = pd.DataFrame(comparison_data)
    
    st.dataframe(
        df,
        column_config={
            "category": "Asset Category",
            "current": st.column_config.NumberColumn(
                "Current Allocation",
                format="%.2f%%"
            ),
            "recommended": st.column_config.NumberColumn(
                "Recommended Allocation",
                format="%.2f%%"
            ),
            "difference": st.column_config.NumberColumn(
                "Difference",
                format="%.2f%%",
                help="Positive value means overallocated, negative means underallocated"
            )
        },
        hide_index=True
    )
    
    # Generate rebalancing suggestions
    st.markdown("### Rebalancing Suggestions")
    
    # Calculate monetary values for rebalancing
    total_portfolio_value = allocation_data["total_value"]
    rebalancing_suggestions = []
    
    for row in comparison_data:
        category = row["category"].lower()
        difference = row["difference"]
        
        if abs(difference) >= 5:  # Only suggest rebalancing for significant differences
            amount_difference = (difference / 100) * total_portfolio_value
            
            if difference > 0:
                rebalancing_suggestions.append({
                    "category": row["category"],
                    "action": "Reduce",
                    "percentage": difference,
                    "amount": amount_difference
                })
            else:
                rebalancing_suggestions.append({
                    "category": row["category"],
                    "action": "Increase",
                    "percentage": abs(difference),
                    "amount": abs(amount_difference)
                })
    
    if rebalancing_suggestions:
        rebalancing_df = pd.DataFrame(rebalancing_suggestions)
        
        st.dataframe(
            rebalancing_df,
            column_config={
                "category": "Asset Category",
                "action": "Action",
                "percentage": st.column_config.NumberColumn(
                    "Percentage Change",
                    format="%.2f%%"
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    format="₹%.2f"
                )
            },
            hide_index=True
        )
        
        # Suggestions text
        for suggestion in rebalancing_suggestions:
            if suggestion["action"] == "Reduce":
                st.markdown(
                    f"- Consider reducing your {suggestion['category']} allocation by **{suggestion['percentage']:.2f}%** "
                    f"(approximately ₹{suggestion['amount']:,.2f}) by selling some investments."
                )
            else:
                st.markdown(
                    f"- Consider increasing your {suggestion['category']} allocation by **{suggestion['percentage']:.2f}%** "
                    f"(approximately ₹{suggestion['amount']:,.2f}) by investing more."
                )
    else:
        st.success("Your portfolio is well-balanced according to your risk profile! No major rebalancing needed.")