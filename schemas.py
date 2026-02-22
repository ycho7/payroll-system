from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from enum import Enum

# Define an Enum for Marital Status
class MaritalStatus(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"

# Common fields shared between creating and reading
class EmployeeBase(BaseModel):
    full_name: str
    company_id: int = Field(..., description="The ID from the companies table")
    is_malaysian: bool = True
    age: Optional[int]
    is_over_60: Optional[bool] = False
    basic_salary: float = Field(..., ge=1700, description="Minimum wage in 2026 is RM1700")
    fixed_allowance: Optional[float] = 0.0
    profit_sharing: Optional[float] = Field(default=0.0, ge=0, description="Profit sharing amount")
    job_title: Optional[str] = None
    ic_number: Optional[str] = None
    tin_number: Optional[str] = None
    kwsp_number: Optional[str] = None          # ✅ NEW
    socso_number: Optional[str] = None         # ✅ NEW

    # ✅ MARITAL & DEPENDENTS
    marital_status: MaritalStatus = Field(default=MaritalStatus.SINGLE)
    number_of_kids: int = Field(default=0, ge=0)

    join_date: Optional[date] = Field(
        default=None,
        description="Employee join date"
    )
    end_date: Optional[date] = Field(
        default=None, 
        description="Resignation or contract end date. Leave empty if still active."
    )

# Fields required only when creating a new employee
class EmployeeCreate(EmployeeBase):
    pass

# Fields returned when reading from the database (includes ID)
class Employee(EmployeeBase):
    id: int

    class Config:
        from_attributes = True # This allows Pydantic to read SQLAlchemy objects

# Payroll calculation request
class PayrollCalculate(BaseModel):
    month_year: str = Field(..., description="Month and year in format YYYY-MM, e.g., 2026-02")
    bonus: Optional[float] = Field(default=0.0, ge=0, description="Bonus amount for this month")
    profit_sharing: Optional[float] = Field(default=0.0, ge=0, description="Profit sharing amount for this month")

# Payroll record response
class PayrollRecord(BaseModel):
    id: int
    employee_id: int
    month_year: str
    basic_salary: float
    fixed_allowance: float
    additional_allowance: float
    salary_advanced: float
    bonus: float
    profit_sharing: float
    gross: float
    epf_employee: float
    epf_employer: float
    socso_employee: float
    socso_employer: float
    eis_employee: float
    eis_employer: float
    net_pay: float

    class Config:
        from_attributes = True

class CompanyCreate(BaseModel):
    name: str
    e_number: Optional[str] = None
    address: Optional[str] = None
    phone_no: Optional[str] = None
    authorized_officer: Optional[str] = None
    officer_designation: Optional[str] = None

class CompanyResponse(CompanyCreate):
    id: int

    class Config:
        from_attributes = True

# This is your ListResponse
class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    e_number: Optional[str] = None
    address: Optional[str] = None
    phone_no: Optional[str] = None
    authorized_officer: Optional[str] = None
    officer_designation: Optional[str] = None