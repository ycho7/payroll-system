from sqlalchemy.orm import Session
from typing import Optional, List
from services.calculator import calculate_age_from_ic
import models, schemas
from fastapi import HTTPException

# Register a new employee
def create_employee(db: Session, employee: schemas.EmployeeCreate):
    # Calculate age from IC
    employee_age = calculate_age_from_ic(employee.ic_number)
    
    # Convert Pydantic model to dict
    employee_data = employee.model_dump()
    
    # Overwrite age in the dictionary
    employee_data['age'] = employee_age
    
    # Automatically flag as over 60
    employee_data['is_over_60'] = employee_age >= 60

    # Create the DB model instance (no duplicates now)
    db_employee = models.Employee(**employee_data)
    
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

# Get all employees (optionally filtered by company)
def get_employees(db: Session, skip: int = 0, limit: int = 100, company_name: Optional[str] = None):
    query = db.query(models.Employee)
    if company_name:
        query = query.filter(models.Employee.company_name == company_name)
    return query.offset(skip).limit(limit).all()

# Get employees by company name
def get_employees_by_company(db: Session, company_name: str, skip: int = 0, limit: int = 100):
    return db.query(models.Employee).filter(
        models.Employee.company_name == company_name
    ).offset(skip).limit(limit).all()

# Find one employee by ID
def get_employee(db: Session, employee_id: int):
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()

# Delete an employee by ID
def delete_employee(db: Session, employee_id: int):
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if employee:
        db.delete(employee)
        db.commit()
        return True
    return False

# Create a payroll record
def create_payroll_record(db: Session, employee_id: int, month_year: str, payroll_data: dict):
    db_record = models.PayrollRecord(
        employee_id=employee_id,
        month_year=month_year,
        basic_salary=payroll_data.get("basic_salary", 0),
        fixed_allowance=payroll_data.get("fixed_allowance", 0),
        additional_allowance=payroll_data.get("additional_allowance", 0),
        salary_advanced=payroll_data.get("salary_advanced", 0),
        bonus=payroll_data.get("bonus", 0),
        profit_sharing=payroll_data.get("profit_sharing", 0),
        gross=payroll_data.get("gross", 0),
        epf_employee=payroll_data.get("epf_ee", 0),
        epf_employer=payroll_data.get("epf_er", 0),
        socso_employee=payroll_data.get("socso_ee", 0),
        socso_employer=payroll_data.get("socso_er", 0),
        eis_employee=payroll_data.get("eis_ee", 0),
        eis_employer=payroll_data.get("eis_er", 0),
        net_pay=payroll_data.get("net_pay", 0)
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

# Get payroll records for an employee
def get_payroll_records(db: Session, employee_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.PayrollRecord).filter(
        models.PayrollRecord.employee_id == employee_id
    ).order_by(models.PayrollRecord.month_year.desc()).offset(skip).limit(limit).all()

# Get payroll record by employee and month
def get_payroll_record_by_month(db: Session, employee_id: int, month_year: str):
    return db.query(models.PayrollRecord).filter(
        models.PayrollRecord.employee_id == employee_id,
        models.PayrollRecord.month_year == month_year
    ).first()

# Get payroll record by ID
def get_payroll_record(db: Session, record_id: int):
    return db.query(models.PayrollRecord).filter(models.PayrollRecord.id == record_id).first()

# Delete a payroll record by ID
def delete_payroll_record(db: Session, record_id: int):
    record = db.query(models.PayrollRecord).filter(models.PayrollRecord.id == record_id).first()
    if record:
        db.delete(record)
        db.commit()
        return True
    return False

# # Get all companies (optionally filtered by name)
# def get_companies(db: Session, skip: int = 0, limit: int = 100, name: Optional[str] = None) -> List[models.Company]:
#     query = db.query(models.Company)
#     if name:
#         query = query.filter(models.Company.name == name)
#     return query.offset(skip).limit(limit).all()

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Company).offset(skip).limit(limit).all()

def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = models.Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def update_company(db: Session, company_id: int, company: schemas.CompanyUpdate):
    db_company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in company.model_dump(exclude_unset=True).items():
        setattr(db_company, key, value)
    db.commit()
    db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: int):
    db_company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(db_company)
    db.commit()
    return {"message": "Company deleted"}