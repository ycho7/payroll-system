"""
Database migration script to add new columns to payroll_records table
Run this once to update your existing database schema
"""
import sqlite3
from database import SQLALCHEMY_DATABASE_URL

# Extract database path from SQLAlchemy URL
db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")

print(f"Migrating database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if columns exist, if not add them
    cursor.execute("PRAGMA table_info(payroll_records)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'basic_salary' not in columns:
        print("Adding basic_salary column...")
        cursor.execute("ALTER TABLE payroll_records ADD COLUMN basic_salary REAL")
    
    if 'fixed_allowance' not in columns:
        print("Adding fixed_allowance column...")
        cursor.execute("ALTER TABLE payroll_records ADD COLUMN fixed_allowance REAL DEFAULT 0.0")
    
    if 'bonus' not in columns:
        print("Adding bonus column...")
        cursor.execute("ALTER TABLE payroll_records ADD COLUMN bonus REAL DEFAULT 0.0")
    
    if 'gross' not in columns:
        print("Adding gross column...")
        cursor.execute("ALTER TABLE payroll_records ADD COLUMN gross REAL")
    
    conn.commit()
    print("Migration completed successfully!")
    
except Exception as e:
    print(f"Error during migration: {e}")
    conn.rollback()
finally:
    conn.close()

