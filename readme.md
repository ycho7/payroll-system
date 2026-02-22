# 📊 Cost Intelligence & Payroll Dashboard

A professional payroll analytics dashboard built with **FastAPI** and **DataTables.js**. This system provides real-time employer cost tracking, dynamic filtering, and premium CSV exports.

---
## 🚀 Quick Setup

### 1. Create a Virtual Environment
It is recommended to use a virtual environment to keep your project dependencies isolated.

```bash
# Create the virtual environment
python -m venv venv

# Activate the environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
Run the following command to install all necessary libraries:

```bash
pip install fastapi uvicorn sqlalchemy jinja2 python-multipart
```

### 3. Start the Application
Launch the Uvicorn server:

```bash
uvicorn main:app --reload
```

## ✨ Dashboard Features

- **Multi-Company Support**  
  Create and manage **multiple company profiles**, each with its own employees, payroll records, and reporting context.

- **Employee Management**  
  Add, edit, and manage employees under each company, including personal details required for payroll and statutory reporting.

- **Payroll Entry & Automation**  
  Key in employee payslips manually while the system **automatically calculates statutory contributions**, including:
  - **KWSP (EPF)**  
  - **SOCSO (PERKESO)**  
  Based on the **latest contribution rules (updated for 2026)**.

- **Centralized Payroll Cost Dashboard**  
  A comprehensive dashboard to view **all payslip-related costs**, allowing employers to quickly understand total payroll expenses across employees and periods.

- **Period-First Navigation**  
  The payroll table prioritizes the Period (Year–Month) as the first column, followed by the Employee Name, making monthly analysis intuitive.

- **Live Cost Intelligence Engine**  
  Summary cards (Basic Salary, Allowances, Statutory Contributions, Employer Cost, and Total CTC) update in real time as you search, filter, or paginate.

- **EA Form Auto-Generation**  
  Automatically generate **filled EA Forms** using:
  - Employee personal information  
  - Employee payslip history  
  - Company profile details  
  This significantly reduces manual paperwork and reporting errors.

- **Modern Pagination & Filtering**  
  Clean, custom-styled pagination (10 / 20 / 50 rows) with instant search and multi-column sorting.

- **CSV Export**  
  Export exactly what is shown on screen into a CSV file for reporting, auditing, or accounting purposes.

- **Clean & Intuitive Navigation**  
  Modern header with quick access actions for seamless movement between dashboards, companies, and payroll views.

- **Smart Sorting**  
  Payroll data is automatically sorted by the **latest period first**, then alphabetically by employee name for clarity.

## 📁 Project Structure
- main.py: FastAPI Routes & App Logic
- models.py: Database Schema (Company, Employee, Payroll)
- templates/company_cost_dashboard.html: The UI Template
- static/: CSS and JS Assets

## 🛠 Tech Stack
- Backend: Python / FastAPI
- Database: SQLite via SQLAlchemy
- Frontend: Jinja2 / Bootstrap 5 / DataTables.js
- Icons: Bootstrap Icons