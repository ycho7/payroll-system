from fastapi import FastAPI, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import crud, models, schemas
from database import SessionLocal, engine
from services.calculator import calculate_malaysian_payroll
from services.pdf_generator import generate_payroll_slip_pdf, generate_ea_pdf
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.calculator import calculate_age_from_ic
import os, zipfile, tempfile
import io

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Family Business Payroll 2026")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mount static files (for Bootstrap)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    employees = crud.get_employees(db)
    companies = crud.get_companies(db)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "employees": employees, # List of Employee objects
        "companies": companies   # List of Company objects
    })

@app.post("/employees/", response_model=schemas.Employee)
def create_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    return crud.create_employee(db=db, employee=employee)

@app.get("/employees/", response_model=list[schemas.Employee])
def read_employees(
    skip: int = 0, 
    limit: int = 100, 
    company_name: Optional[str] = Query(None, description="Filter by company name: CH Hotel or Leong Car Service"),
    db: Session = Depends(get_db)
):
    return crud.get_employees(db, skip=skip, limit=limit, company_name=company_name)

@app.get("/employees/{emp_id}/calculate")
def get_payroll(
    emp_id: int, 
    bonus: float = 0.0, 
    additional_allowance: float = 0.0, # New Parameter
    db: Session = Depends(get_db)
):
    employee = crud.get_employee(db, employee_id=emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Run the calculation logic
    # We pass additional_allowance here
    result = calculate_malaysian_payroll(
        employee.basic_salary, 
        employee.fixed_allowance, 
        employee.is_malaysian, 
        employee.is_over_60,
        bonus=bonus,
        additional_allowance=additional_allowance 
    )
    
    return {"employee_name": employee.full_name, "payroll": result}

@app.post("/employees/{emp_id}/calculate-monthly")
async def calculate_monthly_payroll(
    emp_id: int,
    request: Request,
    month_year: str = Form(...),
    bonus: float = Form(default=0.0),
    profit_sharing: float = Form(default=0.0),
    additional_allowance: float = Form(default=0.0), # Captured from your new form field
    salary_advanced: float = Form(default=0.0), # Added Salary Advance (Pinjaman Dahulu)
    save: bool = Form(default=False),
    db: Session = Depends(get_db)
):
    employee = crud.get_employee(db, employee_id=emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Validate month_year format
    try:
        datetime.strptime(month_year, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month_year format. Use YYYY-MM")
    
    # Check if record already exists
    existing_record = crud.get_payroll_record_by_month(db, emp_id, month_year)
    if existing_record and save:
        raise HTTPException(status_code=400, detail=f"Payroll record for {month_year} already exists.")
    
    employee_age = calculate_age_from_ic(employee.ic_number, month_year)

    # Logic: Automatically flag as over 60 if age is 60 or more
    if employee_age >= 60:
        is_over_60 = True
    else:
        is_over_60 = False

    # Calculate payroll
    # Note: employee.fixed_allowance is passed into the 'allowance' slot
    payroll_result = calculate_malaysian_payroll(
        employee.basic_salary,
        employee.fixed_allowance, 
        employee.is_malaysian,
        is_over_60=is_over_60,
        bonus=bonus,
        profit_sharing=profit_sharing,
        additional_allowance=additional_allowance
    )
    
    # Add values to result for storage/display
    # Renamed "fixed_allowance" to "allowance" as requested
    payroll_result["salary_advanced"] = salary_advanced
    payroll_result["net_pay"] = payroll_result["net_pay"] - salary_advanced
    payroll_result["basic_salary"] = employee.basic_salary
    payroll_result["fixed_allowance"] = employee.fixed_allowance 
    payroll_result["is_malaysian"] = employee.is_malaysian 
    payroll_result["is_over_60"] = employee.is_over_60
    payroll_result["additional_allowance"] = additional_allowance
    payroll_result["bonus"] = bonus
    payroll_result["profit_sharing"] = profit_sharing
    payroll_result["additional_allowance"] = additional_allowance
    
    # Save to database if requested
    if save:
        # Ensure your crud.create_payroll_record can handle the extra 'additional_allowance' key
        crud.create_payroll_record(db, emp_id, month_year, payroll_result)
    
    # AJAX Response
    accept_header = request.headers.get("accept", "")
    if "application/json" in accept_header or request.headers.get("x-requested-with") == "XMLHttpRequest":
        return {
            "success": True,
            "message": "Payroll calculated successfully",
            "payroll": payroll_result,
            "month_year": month_year,
            "saved": save
        }
    
    # HTML Response
    return templates.TemplateResponse(
        "payroll_result.html",
        {
            "request": request,
            "employee": employee,
            "month_year": month_year,
            "payroll": payroll_result,
            "saved": save
        }
    )

@app.get("/employees/{emp_id}", response_class=HTMLResponse)
async def employee_details(request: Request, emp_id: int, db: Session = Depends(get_db)):
    employee = crud.get_employee(db, employee_id=emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # 1. Get the 12 most recent records
    payroll_records = crud.get_payroll_records(db, emp_id, limit=1000)
    
    # 2. Use the ACTUAL LATEST record for the header display
    if payroll_records:
        # This ensures the header matches your last saved data (Bonus included!)
        latest_payroll = payroll_records[0] 
    else:
        # Fallback to estimate if no history exists
        latest_payroll = calculate_malaysian_payroll(
            employee.basic_salary,
            employee.fixed_allowance,
            employee.is_malaysian,
            employee.is_over_60,
            bonus=0.0,
            profit_sharing=employee.profit_sharing or 0.0
        )
    
    
    return templates.TemplateResponse(
        "employee_details.html",
        {
            "request": request,
            "employee": employee,
            "payroll": latest_payroll,
            "payroll_records": payroll_records
        }
    )

@app.get("/employees/{emp_id}/payroll-dashboard", response_class=HTMLResponse)
async def employee_payroll_dashboard(request: Request, emp_id: int, db: Session = Depends(get_db)):
    employee = crud.get_employee(db, employee_id=emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get all payroll records (no limit for full history)
    payroll_records = crud.get_payroll_records(db, emp_id, limit=1000)
    
    # Calculate totals
    total_gross = sum(record.gross for record in payroll_records) if payroll_records else 0
    total_bonus = sum(record.bonus for record in payroll_records) if payroll_records else 0
    total_profit_sharing = sum(record.profit_sharing for record in payroll_records) if payroll_records else 0
    total_deductions = sum(
        record.epf_employee + record.socso_employee + record.eis_employee 
        for record in payroll_records
    ) if payroll_records else 0
    total_net_pay = sum(record.net_pay for record in payroll_records) if payroll_records else 0
    
    # Calculate column totals for footer
    total_basic_salary = sum(record.basic_salary for record in payroll_records) if payroll_records else 0
    total_fixed_allowance = sum(record.fixed_allowance for record in payroll_records) if payroll_records else 0
    total_epf = sum(record.epf_employee for record in payroll_records) if payroll_records else 0
    total_socso = sum(record.socso_employee for record in payroll_records) if payroll_records else 0
    total_eis = sum(record.eis_employee for record in payroll_records) if payroll_records else 0
    
    # Count months with bonus
    bonus_months = sum(1 for record in payroll_records if record.bonus > 0) if payroll_records else 0
    
    return templates.TemplateResponse(
        "employee_payroll_dashboard.html",
        {
            "request": request,
            "employee": employee,
            "payroll_records": payroll_records,
            "total_gross": total_gross,
            "total_bonus": total_bonus,
            "total_profit_sharing": total_profit_sharing,
            "total_deductions": total_deductions,
            "total_net_pay": total_net_pay,
            "total_basic_salary": total_basic_salary,
            "total_fixed_allowance": total_fixed_allowance,
            "total_epf": total_epf,
            "total_socso": total_socso,
            "total_eis": total_eis,
            "bonus_months": bonus_months,
            "record_count": len(payroll_records)
        }
    )

@app.get("/payroll-records/{record_id}/pdf")
def get_payroll_pdf(record_id: int, db: Session = Depends(get_db)):
    """Generate and return PDF payroll slip"""
    record = crud.get_payroll_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    employee = crud.get_employee(db, record.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    company = db.query(models.Company).filter(models.Company.id == employee.company_id).first()

    # Generate PDF
    pdf_content = generate_payroll_slip_pdf(employee, company, record)
    
    # Return PDF response
    filename = f"Payroll_{employee.full_name.replace(' ', '_')}_{record.month_year}.pdf"
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Content-Type": "application/pdf"
        }
    )

@app.delete("/payroll-records/{record_id}")
def delete_payroll_record(record_id: int, db: Session = Depends(get_db)):
    record = crud.get_payroll_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    
    employee_id = record.employee_id
    success = crud.delete_payroll_record(db, record_id)
    if success:
        return {"message": "Payroll record deleted successfully", "record_id": record_id, "employee_id": employee_id}
    raise HTTPException(status_code=500, detail="Failed to delete payroll record")

@app.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    employee = crud.get_employee(db, employee_id=emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    success = crud.delete_employee(db, employee_id=emp_id)
    if success:
        return {"message": "Employee deleted successfully", "employee_id": emp_id}
    raise HTTPException(status_code=500, detail="Failed to delete employee")

from datetime import datetime

@app.post("/employees/{emp_id}/update")
async def update_employee(
    emp_id: int,
    full_name: str = Form(...),
    job_title: str = Form(...),
    company_name: str = Form(...),
    ic_number: str = Form(None),
    tin_number: str = Form(None),
    basic_salary: float = Form(...),
    fixed_allowance: float = Form(...),
    profit_sharing: float = Form(0.0), # Added consistency with your model
    is_malaysian: bool = Form(False),
    kwsp_number: str = Form(None),
    socso_number: str = Form(None),
    join_date: str = Form(None),
    # ✅ NEW FORM FIELDS
    marital_status: str = Form("Single"),
    number_of_kids: int = Form(0),
    end_date: str = Form(None),
    db: Session = Depends(get_db)
):
    employee = crud.get_employee(db, employee_id=emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # --- Date Conversion Logic ---
    try:
        if join_date:
            employee.join_date = datetime.strptime(join_date, "%Y-%m-%d").date()
        else:
            employee.join_date = None
            
        if end_date: # ✅ Handle End Date
            employee.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            employee.end_date = None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # --- Update Personal & Family Info ---
    employee.full_name = full_name
    employee.marital_status = marital_status # ✅ Updated
    employee.number_of_kids = number_of_kids # ✅ Updated
    employee.ic_number = ic_number
    employee.tin_number = tin_number
    employee.kwsp_number = kwsp_number
    employee.socso_number = socso_number
    employee.is_malaysian = is_malaysian

    # --- Age Logic ---
    employee.age = calculate_age_from_ic(ic_number)
    employee.is_over_60 = True if employee.age >= 60 else False

    # --- Salary & Employment ---
    employee.job_title = job_title
    employee.company_name = company_name # Ensure your DB column matches this (some models use company_id)
    employee.basic_salary = basic_salary
    employee.fixed_allowance = fixed_allowance
    employee.profit_sharing = profit_sharing
    
    db.commit()
    return {"status": "success", "message": "Employee details updated successfully"}

@app.post("/payroll-records/{record_id}/edit")
async def edit_payroll_record(
    record_id: int,
    basic_salary: Optional[float] = Form(None),
    fixed_allowance: Optional[float] = Form(None),
    bonus: Optional[float] = Form(None),
    profit_sharing: Optional[float] = Form(None),
    additional_allowance: Optional[float] = Form(None),
    salary_advanced: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    record = db.query(models.PayrollRecord).filter(models.PayrollRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Only update if the value was actually provided in the request
    if basic_salary is not None: record.basic_salary = basic_salary
    if fixed_allowance is not None: record.fixed_allowance = fixed_allowance
    if bonus is not None: record.bonus = bonus
    if profit_sharing is not None: record.profit_sharing = profit_sharing
    if additional_allowance is not None: record.additional_allowance = additional_allowance
    if salary_advanced is not None: record.salary_advanced = salary_advanced

    # Get the employee to recalculate taxes/contributions
    # employee = db.query(models.Employee).filter(models.Employee.id == record.employee_id).first()

    # Recalculate using the updated record values
    payroll_result = calculate_malaysian_payroll(
        record.basic_salary,
        record.fixed_allowance, 
        record.is_malaysian,
        record.is_over_60,
        bonus=record.bonus,
        profit_sharing=record.profit_sharing,
        additional_allowance=record.additional_allowance
    )
    
    # 4. Map the keys EXACTLY to your return values
    record.gross = payroll_result["gross"]
    record.epf_employee = payroll_result["epf_ee"]   # Mapped from epf_ee
    record.epf_employer = payroll_result["epf_er"]   # Mapped from epf_er
    record.socso_employee = payroll_result["socso_ee"] # Mapped from socso_ee
    record.socso_employer = payroll_result["socso_er"] # Mapped from socso_er
    record.eis_employee = payroll_result["eis_ee"]     # Mapped from eis_ee
    record.eis_employer = payroll_result["eis_er"]     # Mapped from eis_er
    
    # Subtract advance from the newly calculated net pay
    record.net_pay = payroll_result["net_pay"] - record.salary_advanced

    db.commit()
    return {"success": True}

@app.get("/payroll/download-ea/all/{year}")
def download_all_ea_forms(year: str, db: Session = Depends(get_db)):
    employees = db.query(models.Employee).all()

    if not employees:
        return {"error": "No employees found"}

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"EA_Forms_{year}.zip")

    files_added = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for emp in employees:
            try:
                pdf_stream, name, company_name = generate_ea_pdf(db, emp.id, year)

                if not pdf_stream:
                    continue  # ✅ skip if no EA

                filename = f"EA_{year}_{name}_{company_name}.pdf"
                zipf.writestr(filename, pdf_stream.read())
                files_added += 1

            except Exception:
                continue  # ✅ silent skip

    if files_added == 0:
        return {"error": f"No EA forms found for {year}"}

    return FileResponse(
        zip_path,
        filename=f"EA_Forms_{year}.zip",
        media_type="application/zip"
    )

@app.get("/payroll/download-ea/{employee_id}/{year}")
async def download_ea_form(employee_id: int, year: str, db: Session = Depends(get_db)):
    pdf_stream, name, company_name = generate_ea_pdf(db, employee_id, year)

    if not pdf_stream:
        return {"error": "No payroll records found for this year"}

    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=EA_{year}_{name}_{company_name}.pdf"
        }
    )

@app.post("/companies/", response_model=schemas.CompanyResponse)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    # 1. Check if a company with THIS EXACT NAME already exists
    existing_company = db.query(models.Company).filter(models.Company.name == company.name).first()
    
    if existing_company:
        raise HTTPException(status_code=400, detail="Company profile already exists. Use PUT to update it.")

    # Create the new company record
    db_company = models.Company(
        name=company.name,
        e_number=company.e_number,
        address=company.address,
        phone_no=company.phone_no,
        authorized_officer=company.authorized_officer,
        officer_designation=company.officer_designation
    )
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

# @app.get("/companies/", response_model=List[schemas.CompanyResponse])
# def get_all_companies(db: Session = Depends(get_db)):
#     return db.query(models.Company).all()

# Render the companies settings page
@app.get("/companies-page/", response_class=HTMLResponse)
def companies_page(request: Request, db: Session = Depends(get_db)):
    companies = crud.get_companies(db=db, skip=0, limit=100)
    return templates.TemplateResponse("companies.html", {"request": request, "companies": companies})

# Create a new company
@app.post("/companies/", response_model=schemas.CompanyResponse)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    return crud.create_company(db=db, company=company)

# Update a company
@app.post("/companies/{company_id}/update", response_model=schemas.CompanyResponse)
def update_company(company_id: int, company: schemas.CompanyUpdate, db: Session = Depends(get_db)):
    return crud.update_company(db=db, company_id=company_id, company=company)

# Delete a company
@app.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    return crud.delete_company(db=db, company_id=company_id)

@app.get("/companies/{company_id}/cost-dashboard", response_class=HTMLResponse)
async def company_cost_dashboard(request: Request, company_id: int, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    employees = db.query(models.Employee).filter(models.Employee.company_id == company_id).all()
    emp_map = {emp.id: emp.full_name for emp in employees}
    
    records = db.query(models.PayrollRecord).filter(
        models.PayrollRecord.employee_id.in_(list(emp_map.keys()))
    ).order_by(models.PayrollRecord.month_year.desc()).all()

    formatted_data = []
    for r in records:
        # Combine the two allowance types
        combined_allowance = (r.fixed_allowance or 0) + (r.additional_allowance or 0)
        
        # Statutory Employer Costs (KWSP + SOCSO + EIS)
        er_stat_total = r.epf_employer + r.socso_employer + r.eis_employer
        
        formatted_data.append({
            "name": emp_map.get(r.employee_id, "Unknown"),
            "period": r.month_year,
            "basic": r.basic_salary,
            "allowance": combined_allowance, # Summed value
            "bonus": r.bonus or 0,  # MAKE SURE THIS LINE EXISTS
            "profit_sharing": r.profit_sharing or 0,
            "kwsp_er": r.epf_employer,
            "socso_eis_er": r.socso_employer + r.eis_employer,
            "ctc": r.gross + er_stat_total
        })

    return templates.TemplateResponse("company_cost_dashboard.html", {
        "request": request,
        "company": company,
        "records": formatted_data
    })
