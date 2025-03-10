import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "finwise")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-session-signing")
COOKIE_NAME = "finwise_auth"
SESSION_EXPIRY_DAYS = 30

TAX_YEAR = "2024-25"

OLD_REGIME_SLABS = [
    {"limit": 250000, "rate": 0},
    {"limit": 500000, "rate": 0.05},
    {"limit": 750000, "rate": 0.1},
    {"limit": 1000000, "rate": 0.15},
    {"limit": 1250000, "rate": 0.2},
    {"limit": 1500000, "rate": 0.25},
    {"limit": float('inf'), "rate": 0.3}
]

NEW_REGIME_SLABS = [
    {"limit": 300000, "rate": 0},
    {"limit": 600000, "rate": 0.05},
    {"limit": 900000, "rate": 0.1},
    {"limit": 1200000, "rate": 0.15},
    {"limit": 1500000, "rate": 0.2},
    {"limit": float('inf'), "rate": 0.3}
]

SURCHARGE_SLABS = [
    {"limit": 5000000, "rate": 0},
    {"limit": 10000000, "rate": 0.1},
    {"limit": 20000000, "rate": 0.15},
    {"limit": 50000000, "rate": 0.25},
    {"limit": float('inf'), "rate": 0.37}
]

CESS_RATE = 0.04

STANDARD_DEDUCTION = 50000

EXPENSE_CATEGORIES = [
    "Housing", "Transportation", "Food", "Utilities", "Healthcare", "Entertainment",
    "Shopping", "Personal Care", "Education", "Travel", "Investments", "Savings",
    "Debt Payments", "Insurance", "Gifts & Donations", "Taxes", "Miscellaneous"
]

INVESTMENT_CATEGORIES = [
    "Equity", "Mutual Funds", "Fixed Deposits", "PPF", "EPF", "NPS",
    "ELSS", "Bonds", "Gold", "Real Estate", "Cryptocurrency", "Others"
]

DEBT_CATEGORIES = [
    "Home Loan", "Car Loan", "Personal Loan", "Education Loan", "Credit Card", "Others"
]

INSURANCE_CATEGORIES = [
    "Life Insurance", "Health Insurance", "Car Insurance", "Two-wheeler Insurance",
    "Home Insurance", "Travel Insurance", "Critical Illness", "Term Insurance", "Others"
]

FINANCIAL_GOAL_CATEGORIES = [
    "Retirement", "Emergency Fund", "Home Purchase", "Education", "Vehicle",
    "Wedding", "Vacation", "Starting Business", "Other Major Purchase"
]

DEFAULT_CURRENCY = "₹"