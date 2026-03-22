import pandas as pd
from .core_utils import get_indian_fy

def clean_zerodha_equity(file):
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

def process_equity_fifo(df, client_pan):
    df['Trade Date'] = pd.to_datetime(df['Trade Date'].astype(str).str.strip().str.split('T').str[0], errors='coerce')
    df = df.sort_values(['Symbol', 'Trade Date']).reset_index(drop=True)
    
    realized_trades = []
    inventory = {}

    for _, row in df.iterrows():
        sym, q, p = row['Symbol'], float(row['Quantity']), float(row['Price'])
        t_date, t_type = row['Trade Date'], str(row['Trade Type']).lower().strip()

        if t_type == 'buy':
            if sym not in inventory: inventory[sym] = []
            inventory[sym].append({'q': q, 'p': p, 'd': t_date})
        elif t_type == 'sell':
            if sym not in inventory or not inventory[sym]: continue
            rem_q = q
            while rem_q > 0 and inventory[sym]:
                buy = inventory[sym][0]
                m_q = min(rem_q, buy['q'])
                
                is_ltcg = (t_date - buy['d']).days > 365
                cutoff = pd.Timestamp('2024-07-23')
                
                if is_ltcg:
                    rate, cat = (12.5, "LTCG") if t_date >= cutoff else (10.0, "LTCG")
                else:
                    rate, cat = (20.0, "STCG") if t_date >= cutoff else (15.0, "STCG")

                realized_trades.append({
                    'PAN': client_pan, 'Symbol': sym, 'Buy Date': buy['d'], 'Sell Date': t_date,
                    'Qty': m_q, 'Realized P&L': round(m_q * (p - buy['p']), 2), 
                    'Category': cat, 'Rate (%)': rate, 'FY': get_indian_fy(t_date)
                })

                rem_q -= m_q
                inventory[sym][0]['q'] -= m_q
                if inventory[sym][0]['q'] == 0: inventory[sym].pop(0)

    return pd.DataFrame(realized_trades)

def merge_equity_ledgers(old_df, new_df):
    if old_df.empty: return new_df
    if new_df.empty: return old_df
    return pd.concat([old_df, new_df], ignore_index=True).drop_duplicates().reset_index(drop=True)
