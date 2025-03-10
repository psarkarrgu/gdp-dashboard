import os

def create_structure(base_path, structure):
    for path in structure:
        full_path = os.path.join(base_path, path)
        if path.endswith("/"):  # Create directories
            os.makedirs(full_path, exist_ok=True)
        else:  # Create blank files
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                pass

def main():
    base_path = "finwise"  # Root directory
    structure = [
        "app.py",
        "requirements.txt",
        "config.py",
        "database/__init__.py",
        "database/connection.py",
        "database/models.py",
        "database/operations.py",
        "utils/__init__.py",
        "utils/auth_utils.py",
        "utils/data_utils.py",
        "utils/tax_utils.py",
        "utils/finance_utils.py",
        "utils/visualization.py",
        "pages/__init__.py",
        "pages/auth/__init__.py",
        "pages/auth/login.py",
        "pages/auth/register.py",
        "pages/dashboard.py",
        "pages/income.py",
        "pages/expenses.py",
        "pages/budget.py",
        "pages/investments.py",
        "pages/debt.py",
        "pages/tax_planning.py",
        "pages/reports.py",
        "pages/retirement.py",
        "pages/goals.py",
        "pages/documents.py",
        "pages/insurance.py",
        "pages/networth.py",
        "pages/calendar.py",
        "pages/education.py",
        "pages/settings.py",
        "assets/css/",
        "assets/images/",
        "assets/sample_data/"
    ]
    
    create_structure(base_path, structure)
    print("Project structure created successfully!")

if __name__ == "__main__":
    main()
