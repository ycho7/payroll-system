from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import date

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    age = Column(Integer)
    # --- CHANGED: Link to Company ID instead of just a name ---
    company_id = Column(Integer, ForeignKey("companies.id"))
    # New Information Fields
    job_title = Column(String)
    ic_number = Column(String(12))  # or Column(String(12)) for standard Malaysian IC
    tin_number = Column(String) # Tax Identification Number
    is_malaysian = Column(Boolean, default=True)
    is_over_60 = Column(Boolean, default=False)


    join_date = Column(Date, default=date.today)   # ✅ NEW
    kwsp_number = Column(String)                    # ✅ NEW
    socso_number = Column(String)                   # ✅ NEW


    basic_salary = Column(Float)
    fixed_allowance = Column(Float, default=0.0)
    profit_sharing = Column(Float, default=0.0)

    payrolls = relationship("PayrollRecord", back_populates="employee", cascade="all, delete-orphan")

    company = relationship("Company", back_populates="employees")

class PayrollRecord(Base):
    __tablename__ = "payroll_records"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    month_year = Column(String)  # e.g., "2026-02"
    is_malaysian = Column(Boolean, default=True)
    is_over_60 = Column(Boolean, default=False)
    # Salary components
    basic_salary = Column(Float)
    salary_advanced = Column(Float, default=0.0)
    fixed_allowance = Column(Float, default=0.0)
    additional_allowance = Column(Float, default=0.0)
    bonus = Column(Float, default=0.0)
    profit_sharing = Column(Float, default=0.0)
    gross = Column(Float)
    
    # We store these so we can generate reports for EPF/SOCSO later
    epf_employee = Column(Float)
    epf_employer = Column(Float)
    socso_employee = Column(Float)
    socso_employer = Column(Float)
    eis_employee = Column(Float)
    eis_employer = Column(Float)
    net_pay = Column(Float)

    employee = relationship("Employee", back_populates="payrolls")

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # --- Official EA Form Fields ---
    name = Column(String, nullable=False)        # Official Registered Name
    e_number = Column(String)                   # Employer's No. (e.g., E 123456789)
    address = Column(Text)                      # Registered/Business Address
    phone_no = Column(String)                   # Employer's Tel No.
    
    # --- Authorized Signatory (The person signing the EA) ---
    authorized_officer = Column(String)         # Name of Officer
    officer_designation = Column(String)        # Job Title (e.g., Director/HR Manager)
    # This allows you to do: company.employees
    employees = relationship("Employee", back_populates="company")