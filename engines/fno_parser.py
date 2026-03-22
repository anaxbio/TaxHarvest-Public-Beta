import pandas as pd
import numpy as np
from .core_utils import get_indian_fy

def clean_zerodha_fno(file):
    try:
        raw_df = pd.read_csv(file, header=None, skip_blank_lines=True)
    except Exception:
        raw_df = pd.read_excel(file, header=None)

    anchor_row_series = raw_df.astype(str).apply(lambda x: x.str.contains('Trade Date', case=False, na=False)).any(axis=1)
    if not anchor_row_series.any():
        raise ValueError("Could not find 'Trade Date'. Please ensure it is a raw F&O Tradebook.")
        
    header_idx = anchor_row_series.idxmax()
    raw_df.columns = raw_df.iloc[header_idx].astype(str).str.strip()
    clean_df = raw_df.iloc[header_idx + 1:].reset_index(drop=True)
    return clean_df.dropna(axis=1, how='all').dropna(subset=['Trade Date'])

def process_fno_tradebook(df, client_pan):
    df['Trade Date'] = pd.to_datetime(df['Trade Date'].astype(str).str.strip().str.split('T').str[0], errors='coerce')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
    df['Trade Type'] = df['Trade Type'].astype(str).str.strip().str.lower()
    
    df['Signed Qty'] = np.where(df['Trade Type'] == 'buy', df['Quantity'], -df['Quantity'])
    df['Cash Flow'] = np.where(df['Trade Type'] == 'buy', -df['Quantity'] * df['Price'], df['Quantity'] * df['Price'])
    
    grouped = df.groupby('Symbol').agg(
        Net_Quantity=('Signed Qty', 'sum'),
        Total_Cash_Flow=('Cash Flow', 'sum'),
        Last_Trade_Date=('Trade Date', 'max'),
        Total_Trades=('Trade Date', 'count')
    ).reset_index()
    
    grouped['Status'] = np.where(grouped['Net_Quantity'] == 0, 'Closed', 'Open')
    grouped['Financial Year'] = grouped['Last_Trade_Date'].apply(get_indian_fy)
    grouped['PAN'] = client_pan
    return grouped

def merge_fno_ledgers(old_df, new_df):
    if old_df.empty: return new_df
    if new_df.empty: return old_df
    
    old_df['Last_Trade_Date'] = pd.to_datetime(old_df['Last_Trade_Date'], errors='coerce')
    new_df['Last_Trade_Date'] = pd.to_datetime(new_df['Last_Trade_Date'], errors='coerce')

    combined = pd.concat([old_df, new_df], ignore_index=True)
    merged = combined.groupby(['PAN', 'Symbol']).agg(
        Net_Quantity=('Net_Quantity', 'sum'),
        Total_Cash_Flow=('Total_Cash_Flow', 'sum'),
        Last_Trade_Date=('Last_Trade_Date', 'max'),
        Total_Trades=('Total_Trades', 'sum')
    ).reset_index()
    
    merged['Status'] = np.where(merged['Net_Quantity'] == 0, 'Closed', 'Open')
    merged['Financial Year'] = merged['Last_Trade_Date'].apply(get_indian_fy)
    return merged
