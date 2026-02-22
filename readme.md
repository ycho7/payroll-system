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
- Period-First Navigation: The table prioritized the Period (Year-Month) as the first column, followed by the Employee Name.
- Live Metrics Engine: The summary cards (Basic, Allowances, Profit, Statutory, and Total CTC) update in real-time as you search or filter.
- Modern Pagination: A sleek, custom-styled selector (10, 20, 50 rows) for easy navigation.
- CSV Export: Integrated Button that allows you to export exactly what you see on the screen into a professional CSV file.
- Clean Navigation: A modern header featuring a Home icon and a Settings button for quick transitions.
- Multi-Column Sorting: Data is pre-sorted by the newest period first, then alphabetically by name.

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