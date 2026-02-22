# Multi-Company Update Checklist

## Current State Analysis
Your system already has some multi-company support (company_name field in Employee model, tabs in dashboard), but several areas need updates.

---

## ✅ Already Implemented
1. **models.py** - Has `company_name` field in Employee model (line 9)
2. **dashboard.html** - Has tabs for "CH Hotel" and "Leong Car Service" with filtering

---

## ❌ NEEDS UPDATES

### 1. **schemas.py** - MISSING company_name field
**Issue:** EmployeeBase, EmployeeCreate, and Employee schemas don't include `company_name`
**Impact:** Cannot create employees with company assignment via API
**Location:** Lines 5-21

**Required Changes:**
- Add `company_name: str` to `EmployeeBase` class
- Consider making it optional with default or required field

---

### 2. **crud.py** - NO company filtering
**Issue:** All CRUD functions return/filter employees without considering company
**Impact:** 
- `get_employees()` returns ALL employees from both companies
- No way to filter by company in queries
- Dashboard works but inefficient (loads all then filters in template)

**Required Changes:**
- Add `company_name` parameter to `get_employees()` function
- Add `company_name` parameter to `create_employee()` function (or extract from employee schema)
- Consider adding `get_employees_by_company()` helper function

---

### 3. **main.py** - Missing company filtering in endpoints
**Issue:** 
- Dashboard endpoint loads all employees (line 30)
- Create employee endpoint doesn't handle company_name (line 37)
- No company-specific endpoints

**Required Changes:**
- Update `/employees/` GET endpoint to accept optional `company_name` query parameter
- Ensure `/employees/` POST endpoint accepts and saves `company_name`
- Consider adding `/companies/{company_name}/employees/` endpoint

---

### 4. **dashboard.html** - Incomplete form
**Issue:** 
- Has company selector dropdown (lines 48-54) but no form wrapper or submit functionality
- No way to add new employees from the UI

**Required Changes:**
- Create proper form to add employees with company selection
- Add JavaScript to submit form to `/employees/` endpoint
- Add form validation

---

### 5. **models.py** - Consider Company table (OPTIONAL but RECOMMENDED)
**Issue:** Company names are stored as strings, which can lead to typos/inconsistencies
**Recommendation:** Create a Company model with foreign key relationship

**Optional Enhancement:**
```python
class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    
# Then in Employee:
company_id = Column(Integer, ForeignKey("companies.id"))
```

---

## Priority Order for Updates

1. **HIGH PRIORITY:**
   - Update `schemas.py` to include `company_name`
   - Update `crud.py` to filter by company
   - Update `main.py` endpoints to handle company filtering

2. **MEDIUM PRIORITY:**
   - Complete the employee creation form in `dashboard.html`
   - Add company filtering to GET endpoints

3. **LOW PRIORITY (Nice to have):**
   - Create Company model for better data integrity
   - Add company management endpoints

---

## Testing Checklist After Updates

- [ ] Can create employee for "CH Hotel"
- [ ] Can create employee for "Leong Car Service"
- [ ] Dashboard shows correct employees per company tab
- [ ] API endpoints filter by company correctly
- [ ] Payroll calculation works for employees from both companies
- [ ] No duplicate company names (typos)

