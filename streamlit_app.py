import streamlit as st
import pandas as pd
import json
from engines.fno_parser import clean_zerodha_fno, process_fno_tradebook, merge_fno_ledgers
from engines.equity_parser import clean_zerodha_equity, process_equity_fifo, merge_equity_ledgers

st.set_page_config(page_title="TaxHarvest Beta", layout="wide", page_icon="⚖️")

# --- CSS FIX: Visible Dark Text on White Metric Cards ---
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #ffffff !important; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #1f2937 !important; }
    </style>
    """, unsafe_allow_html=True)

if 'master_vault' not in st.session_state:
    st.session_state.master_vault = {"fno_ledger": [], "equity_ledger": []}

st.sidebar.title("🔐 Master Vault")
vault_file = st.sidebar.file_uploader("Restore Vault (.json)", type=['json'])

if vault_file:
    try:
        st.session_state.master_vault = json.load(vault_file)
        st.sidebar.success("Vault Restored!")
    except:
        st.sidebar.error("Invalid Vault Format")

st.sidebar.divider()
active_pan = st.sidebar.text_input("Active Client/PAN", value="DEFAULT_PAN").upper()
module = st.sidebar.radio("Navigate", ["📈 F&O Audit", "🏛️ Equity (FIFO)"])

if module == "📈 F&O Audit":
    st.title(f"Derivatives Audit | PAN: {active_pan}")
    
    files = st.file_uploader("Upload F&O Tradebook", type=['csv', 'xlsx'], accept_multiple_files=True)
    if files:
        old_fno = pd.DataFrame(st.session_state.master_vault.get("fno_ledger", []))
        new_list = [process_fno_tradebook(clean_zerodha_fno(f), active_pan) for f in files]
        merged = merge_fno_ledgers(old_fno, pd.concat(new_list))
        merged['Last_Trade_Date'] = merged['Last_Trade_Date'].astype(str)
        st.session_state.master_vault["fno_ledger"] = merged.to_dict(orient="records")
        st.rerun()

    fno_df = pd.DataFrame(st.session_state.master_vault["fno_ledger"])
    if not fno_df.empty:
        client_fno = fno_df[fno_df['PAN'] == active_pan]
        if not client_fno.empty:
            fys = ["All"] + sorted(client_fno['Financial Year'].unique().tolist(), reverse=True)
            sel_fy = st.selectbox("Filter by Financial Year", fys)
            disp_df = client_fno if sel_fy == "All" else client_fno[client_fno['Financial Year'] == sel_fy]
            
            pnl = disp_df[disp_df['Status'] == 'Closed']['Total_Cash_Flow'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Realized F&O P&L", f"₹{pnl:,.2f}")
            c2.metric("Open Contracts", len(disp_df[disp_df['Status'] == 'Open']))
            st.dataframe(disp_df, use_container_width=True)

elif module == "🏛️ Equity (FIFO)":
    st.title(f"Capital Gains Engine | PAN: {active_pan}")
    
    files = st.file_uploader("Upload Equity Tradebook", type=['csv', 'xlsx'], accept_multiple_files=True)
    if files:
        old_eq = pd.DataFrame(st.session_state.master_vault.get("equity_ledger", []))
        new_list = [process_equity_fifo(clean_zerodha_equity(f), active_pan) for f in files]
        merged = merge_equity_ledgers(old_eq, pd.concat(new_list))
        merged['Buy Date'] = merged['Buy Date'].astype(str)
        merged['Sell Date'] = merged['Sell Date'].astype(str)
        st.session_state.master_vault["equity_ledger"] = merged.to_dict(orient="records")
        st.rerun()

    eq_df = pd.DataFrame(st.session_state.master_vault["equity_ledger"])
    if not eq_df.empty:
        client_eq = eq_df[eq_df['PAN'] == active_pan]
        if not client_eq.empty:
            fys = ["All"] + sorted(client_eq['FY'].unique().tolist(), reverse=True)
            sel_fy = st.selectbox("Filter by Financial Year", fys)
            disp_eq = client_eq if sel_fy == "All" else client_eq[client_eq['FY'] == sel_fy]
            
            stcg = disp_eq[disp_eq['Category'] == 'STCG']['Realized P&L'].sum()
            ltcg = disp_eq[disp_eq['Category'] == 'LTCG']['Realized P&L'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Total STCG", f"₹{stcg:,.2f}")
            c2.metric("Total LTCG", f"₹{ltcg:,.2f}")
            st.dataframe(disp_eq, use_container_width=True)

st.sidebar.divider()
st.sidebar.download_button("⬇️ Export Master Vault", json.dumps(st.session_state.master_vault, indent=4), "vault.json", "application/json")
