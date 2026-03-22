import pandas as pd
import numpy as np
from .core_utils import get_indian_fy

def process_fno_tradebook(df):
    df['Trade Date'] = pd.to_datetime(df['Trade Date'], errors='coerce')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
    df['Trade Type'] = df['Trade Type'].astype(str).str.strip().str.lower()
    
    df['Signed Qty'] = np.where(df['Trade Type'] == 'buy', df['Quantity'], -df['Quantity'])
    df['Cash Flow'] = np.where(df['Trade Type'] == 'buy', -df['Quantity'] * df['Price'], df['Quantity'] * df['Price'])
    
    grouped = df.groupby('Symbol').agg(
        Net_Quantity=('Signed Qty', 'sum'),
        Total_Cash_Flow=('Cash Flow', 'sum'),
        Last_Trade_Date=('Trade Date', 'max')
    ).reset_index()
    
    grouped['Status'] = np.where(grouped['Net_Quantity'] == 0, 'Closed', 'Open')
    grouped['Financial Year'] = grouped['Last_Trade_Date'].apply(get_indian_fy)
    return grouped

def merge_fno_ledgers(old_df, new_df):
    if old_df.empty: return new_df
    combined = pd.concat([old_df, new_df], ignore_index=True)
    merged = combined.groupby('Symbol').agg(
        Net_Quantity=('Net_Quantity', 'sum'),
        Total_Cash_Flow=('Total_Cash_Flow', 'sum'),
        Last_Trade_Date=('Last_Trade_Date', 'max')
    ).reset_index()
    merged['Status'] = np.where(merged['Net_Quantity'] == 0, 'Closed', 'Open')
    merged['Financial Year'] = merged['Last_Trade_Date'].apply(get_indian_fy)
    return merged
