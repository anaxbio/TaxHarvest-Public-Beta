import pandas as pd

def get_indian_fy(date):
    if pd.isna(date): return "Unknown FY"
    date = pd.to_datetime(date, errors='coerce')
    if pd.isna(date): return "Unknown FY"
    year = date.year
    return f"FY {year}-{str(year+1)[2:]}" if date.month > 3 else f"FY {year-1}-{str(year)[2:]}"

def clean_zerodha_tradebook(file):
    try:
        try:
            raw_df = pd.read_csv(file, header=None, skip_blank_lines=True)
        except Exception:
            raw_df = pd.read_excel(file, header=None)

        mask = raw_df.astype(str).apply(lambda x: x.str.contains('Trade Date', case=False, na=False)).any(axis=1)
        if not mask.any(): raise ValueError("Could not find 'Trade Date' header.")
            
        header_idx = mask.idxmax()
        raw_df.columns = raw_df.iloc[header_idx].astype(str).str.strip()
        clean_df = raw_df.iloc[header_idx + 1:].reset_index(drop=True)
        return clean_df.dropna(axis=1, how='all').dropna(subset=['Trade Date'])
    except Exception as e:
        raise ValueError(f"File cleaning error: {e}")
