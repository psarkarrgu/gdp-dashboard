import streamlit as st
import datetime
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.operations import get_user_by_email, get_user_by_username, get_user_by_id, verify_password, update_user_login
from config import COOKIE_NAME, SESSION_EXPIRY_DAYS

def init_auth_session_state():
    """Initialize authentication-related session state variables"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None

def login(db: Session, email: str, password: str):
    """Authenticate a user and set session state"""
    user = get_user_by_email(db, email)
    if not user:
        st.session_state.authentication_status = "invalid_user"
        return False
    
    if not user.is_active:
        st.session_state.authentication_status = "inactive_user"
        return False
    
    if not verify_password(password, user.hashed_password):
        st.session_state.authentication_status = "invalid_password"
        return False
    
    # Update user login timestamp
    update_user_login(db, user.id)
    
    # Set session state
    st.session_state.user_id = user.id
    st.session_state.username = user.username
    st.session_state.is_authenticated = True
    st.session_state.authentication_status = "authenticated"
    
    return True

def logout():
    """Log out the user and clear session state"""
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.is_authenticated = False
    st.session_state.authentication_status = None

def require_auth():
    """Check if the user is authenticated, otherwise redirect to login page"""
    if not st.session_state.is_authenticated:
        st.warning("You need to log in to access this page.")
        st.stop()

def get_current_user(db: Session):
    """Get the current authenticated user from the database"""
    if st.session_state.user_id:
        return get_user_by_id(db, st.session_state.user_id)
    return None

def check_email_exists(db: Session, email: str):
    """Check if an email already exists in the database"""
    user = get_user_by_email(db, email)
    return user is not None

def check_username_exists(db: Session, username: str):
    """Check if a username already exists in the database"""
    user = get_user_by_username(db, username)
    return user is not None