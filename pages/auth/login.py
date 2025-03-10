import streamlit as st
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.connection import db_session
from utils.auth_utils import login

def show_login_page():
    """Display the login page"""
    st.markdown("<h3>Login to your account</h3>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                if login(db_session, email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    auth_status = st.session_state.authentication_status
                    if auth_status == "invalid_user":
                        st.error("Email not found. Please check your email or register.")
                    elif auth_status == "invalid_password":
                        st.error("Incorrect password. Please try again.")
                    elif auth_status == "inactive_user":
                        st.error("Your account is inactive. Please contact support.")
                    else:
                        st.error("Login failed. Please try again.")