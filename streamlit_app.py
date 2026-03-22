  import streamlit as st
import pandas as pd
import json
from datetime import datetime
from engines.core_utils import clean_zerodha_tradebook
from engines.fno_parser import process_fno_tradebook, merge_fno_ledgers
from engines.equity_parser import process_equity_fifo, merge_equity_ledgers

st.set_page_config(page_title="TaxHarvest Beta", layout="wide", page_icon="⚖️")

if 'master_vault' not in st.session_state:
    st.session_state.master_vault = {"fno_ledger": [], "equity_ledger": []}

st.sidebar.title("🔐 Master Vault")
vault_file = st.sidebar.file_uploader("Upload Vault (.json)", type=['json'])

if vault_file:
    try:
        st.session_state.master_vault = json.load(vault_file)
        st.sidebar.success("Vault Loaded!")
    except:
        st.sidebar.error("Invalid Vault Format")

module = st.sidebar.radio("Navigate", ["📈 F&O", "🏛️ Equity (FIFO)"])

if module == "📈 F&O":
    st.title("Derivatives Audit (F&O)")
    old_fno = pd.DataFrame(st.session_state.master_vault.get("fno_ledger", []))
    files = st.file_uploader("Upload F&O Tradebook", type=['csv', 'xlsx'], accept_multiple_files=True)
    
    if files:
        new_list = [process_fno_tradebook(clean_zerodha_tradebook(f)) for f in files]
        merged = merge_fno_ledgers(old_fno, pd.concat(new_list))
        merged['Last_Trade_Date'] = merged['Last_Trade_Date'].astype(str)
        st.session_state.master_vault["fno_ledger"] = merged.to_dict(orient="records")
        st.rerun()

    fno_df = pd.DataFrame(st.session_state.master_vault["fno_ledger"])
    if not fno_df.empty:
        pnl = fno_df[fno_df['Status'] == 'Closed']['Total_Cash_Flow'].sum()
        st.metric("Realized F&O P&L", f"₹{pnl:,.2f}")
        st.dataframe(fno_df, use_container_width=True)

elif module == "🏛️ Equity (FIFO)":
    st.title("Capital Gains Engine (FIFO)")
    old_eq = pd.DataFrame(st.session_state.master_vault.get("equity_ledger", []))
    files = st.file_uploader("Upload Equity Tradebook", type=['csv', 'xlsx'], accept_multiple_files=True)
    
    if files:
        new_list = [process_equity_fifo(clean_zerodha_tradebook(f)) for f in files]
        merged = merge_equity_ledgers(old_eq, pd.concat(new_list))
        merged['Buy Date'] = merged['Buy Date'].astype(str)
        merged['Sell Date'] = merged['Sell Date'].astype(str)
        st.session_state.master_vault["equity_ledger"] = merged.to_dict(orient="records")
        st.rerun()

    eq_df = pd.DataFrame(st.session_state.master_vault["equity_ledger"])
    if not eq_df.empty:
        stcg = eq_df[eq_df['Category'] == 'STCG']['Realized P&L'].sum()
        ltcg = eq_df[eq_df['Category'] == 'LTCG']['Realized P&L'].sum()
        c1, c2 = st.columns(2)
        c1.metric("Total STCG", f"₹{stcg:,.2f}")
        c2.metric("Total LTCG", f"₹{ltcg:,.2f}")
        st.dataframe(eq_df, use_container_width=True)

st.sidebar.divider()
st.sidebar.download_button("⬇️ Export Master Vault", json.dumps(st.session_state.master_vault, indent=4), "vault.json", "application/json")
