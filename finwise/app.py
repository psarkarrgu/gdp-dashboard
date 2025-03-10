import streamlit as st
import os
import sys
from datetime import datetime
import pandas as pd
from streamlit_option_menu import option_menu

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from database.connection import init_db, Base, engine, db_session
from utils.auth_utils import init_auth_session_state, get_current_user
from pages.auth.login import show_login_page
from pages.auth.register import show_register_page
from pages.dashboard import show_dashboard
from pages.income import show_income_page
from pages.expenses import show_expenses_page
from pages.budget import show_budget_page
from pages.investments import show_investments_page
from pages.debt import show_debt_page
from pages.tax_planning import show_tax_planning_page
from pages.reports import show_reports_page
from pages.retirement import show_retirement_page
from pages.goals import show_goals_page
from pages.documents import show_documents_page
from pages.insurance import show_insurance_page
from pages.networth import show_networth_page
from pages.calendar import show_calendar_page
from pages.education import show_education_page
from pages.settings import show_settings_page

# App configuration
st.set_page_config(
    page_title="FinWise - Indian Personal Finance Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Initialize authentication session state
init_auth_session_state()

def main():
    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            font-size: 2rem;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #333;
            margin-bottom: 1rem;
        }
        .card {
            background-color: #f9f9f9;
            border-radius: 5px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .metric-card {
            background-color: #ffffff;
            border-left: 5px solid #1E88E5;
            padding: 1rem;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: #1E88E5;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #666;
        }
        .positive {
            color: #4CAF50;
        }
        .negative {
            color: #F44336;
        }
        .warning {
            color: #FF9800;
        }
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
        }
        .stButton button {
            width: 100%;
        }
        .footer {
            text-align: center;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.8rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Check authentication status
    if not st.session_state.is_authenticated:
        # Show authentication pages
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h1 class='main-header'>FinWise</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Your complete personal finance manager for Indian tax and investment planning</p>", unsafe_allow_html=True)
            
            tabs = st.tabs(["Login", "Register"])
            
            with tabs[0]:
                show_login_page()
            
            with tabs[1]:
                show_register_page()
        
        with col2:
            st.image("assets/images/finance_illustration.png", use_column_width=True)
        
        # App features section
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>Key Features</h2>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("<div class='card'><h3>Budget Planning</h3><p>Create custom budgets, track expenses, and analyze your spending patterns.</p></div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='card'><h3>Tax Optimization</h3><p>Compare old and new tax regimes, maximize tax savings, and get personalized recommendations.</p></div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("<div class='card'><h3>Investment Tracking</h3><p>Monitor your investments, analyze returns, and plan for future financial goals.</p></div>", unsafe_allow_html=True)
    
    else:
        # Get current user
        user = get_current_user(db_session)
        
        # Create sidebar menu
        with st.sidebar:
            st.markdown(f"<h2>Welcome, {user.first_name or user.username}!</h2>", unsafe_allow_html=True)
            
            selected = option_menu(
                "Main Menu",
                [
                    "Dashboard", "Income", "Expenses", "Budget", "Investments",
                    "Debt", "Tax Planning", "Reports", "Retirement", "Goals",
                    "Documents", "Insurance", "Net Worth", "Calendar", "Education", "Settings"
                ],
                icons=[
                    "speedometer2", "cash-coin", "cart-dash", "calculator", "graph-up-arrow",
                    "credit-card", "receipt", "file-earmark-text", "piggy-bank", "bullseye",
                    "folder", "shield-check", "bank", "calendar-date", "book", "gear"
                ],
                menu_icon="menu-button-wide",
                default_index=0
            )
            
            st.markdown("---")
            if st.button("Logout"):
                st.session_state.is_authenticated = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.rerun()
        
        # Render selected page
        if selected == "Dashboard":
            show_dashboard(user)
        elif selected == "Income":
            show_income_page(user)
        elif selected == "Expenses":
            show_expenses_page(user)
        elif selected == "Budget":
            show_budget_page(user)
        elif selected == "Investments":
            show_investments_page(user)
        elif selected == "Debt":
            show_debt_page(user)
        elif selected == "Tax Planning":
            show_tax_planning_page(user)
        elif selected == "Reports":
            show_reports_page(user)
        elif selected == "Retirement":
            show_retirement_page(user)
        elif selected == "Goals":
            show_goals_page(user)
        elif selected == "Documents":
            show_documents_page(user)
        elif selected == "Insurance":
            show_insurance_page(user)
        elif selected == "Net Worth":
            show_networth_page(user)
        elif selected == "Calendar":
            show_calendar_page(user)
        elif selected == "Education":
            show_education_page(user)
        elif selected == "Settings":
            show_settings_page(user)
    
    # Footer
    st.markdown("<div class='footer'>© 2025 FinWise - Your Personal Finance Manager for India</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()