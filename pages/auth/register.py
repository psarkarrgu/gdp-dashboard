import streamlit as st
import os
import sys
import re
from datetime import date

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.connection import db_session
from database.operations import create_user
from utils.auth_utils import check_email_exists, check_username_exists, login

def is_valid_email(email):
    """Check if email is valid"""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """Check if password meets requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, ""

def is_valid_pan(pan):
    """Check if PAN is valid"""
    if not pan:
        return True, ""  # PAN is optional
    
    pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
    if not re.match(pattern, pan):
        return False, "PAN should be in the format AAAAA0000A"
    
    return True, ""

def is_valid_aadhar(aadhar):
    """Check if Aadhar is valid"""
    if not aadhar:
        return True, ""  # Aadhar is optional
    
    if not aadhar.isdigit() or len(aadhar) != 12:
        return False, "Aadhar should be a 12-digit number"
    
    return True, ""

def show_register_page():
    """Display the registration page"""
    st.markdown("<h3>Create a new account</h3>", unsafe_allow_html=True)
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input("Email*", key="reg_email")
            username = st.text_input("Username*", key="reg_username")
            password = st.text_input("Password*", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password*", type="password", key="reg_confirm_password")
        
        with col2:
            first_name = st.text_input("First Name", key="reg_first_name")
            last_name = st.text_input("Last Name", key="reg_last_name")
            dob = st.date_input("Date of Birth", value=None, key="reg_dob")
            phone = st.text_input("Phone Number", key="reg_phone")
        
        st.markdown("### Optional Tax Information")
        col1, col2 = st.columns(2)
        
        with col1:
            pan = st.text_input("PAN Number", key="reg_pan")
        
        with col2:
            aadhar = st.text_input("Aadhar Number", key="reg_aadhar")
            
        default_regime = st.radio("Preferred Tax Regime", ["old", "new"], horizontal=True)
        
        st.markdown("*Required fields")
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            # Validate required fields
            if not email or not username or not password or not confirm_password:
                st.error("Please fill in all required fields")
                return
            
            # Validate email format
            if not is_valid_email(email):
                st.error("Please enter a valid email address")
                return
            
            # Check if email already exists
            if check_email_exists(db_session, email):
                st.error("Email already registered. Please use a different email or login")
                return
            
            # Check if username already exists
            if check_username_exists(db_session, username):
                st.error("Username already taken. Please choose a different username")
                return
            
            # Validate password
            valid_password, password_error = is_valid_password(password)
            if not valid_password:
                st.error(password_error)
                return
            
            # Check if passwords match
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            # Validate PAN if provided
            valid_pan, pan_error = is_valid_pan(pan)
            if not valid_pan:
                st.error(pan_error)
                return
            
            # Validate Aadhar if provided
            valid_aadhar, aadhar_error = is_valid_aadhar(aadhar)
            if not valid_aadhar:
                st.error(aadhar_error)
                return
            
            try:
                # Create user
                user = create_user(
                    db=db_session,
                    email=email,
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=dob,
                    phone_number=phone,
                    pan_number=pan,
                    aadhar_number=aadhar
                )
                
                # Update tax regime preference
                user.tax_regime = default_regime
                db_session.commit()
                
                # Automatically login
                if login(db_session, email, password):
                    st.success("Registration successful! You are now logged in.")
                    st.rerun()
                else:
                    st.error("Registration successful but automatic login failed. Please login manually.")
            
            except Exception as e:
                st.error(f"Registration failed: {str(e)}")
                db_session.rollback()