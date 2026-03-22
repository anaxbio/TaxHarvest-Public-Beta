import pandas as pd

def get_indian_fy(date):
    """Strictly returns FY string like 'FY 2024-25' for any given date"""
    if pd.isna(date): return "Unknown FY"
    date = pd.to_datetime(date, errors='coerce')
    if pd.isna(date): return "Unknown FY"
    
    year = date.year
    return f"FY {year}-{str(year+1)[2:]}" if date.month > 3 else f"FY {year-1}-{str(year)[2:]}"
