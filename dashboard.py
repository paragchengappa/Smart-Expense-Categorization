import streamlit as st
import pandas as pd
from supabase import create_client

# 1. Connect to your Supabase (same credentials from your pipeline.py)
SUPABASE_URL = "https://bpkwwwsctogbomsrizmt.supabase.co"
SUPABASE_KEY = "sb_publishable_dPF3gE09KYwNKMDT6uhG1A_lHc3EBAe"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Smart Expense Tracker")

# 2. Fetch the extracted invoices from the database
st.header("Recent Invoices")
invoices_response = supabase.table("invoices").select("*").execute()
invoices_data = invoices_response.data

if invoices_data:
    # Convert data into a Pandas DataFrame to make it look clean
    df_invoices = pd.DataFrame(invoices_data)
    
    # Display as an interactive table
    st.dataframe(df_invoices, use_container_width=True)
    
    # Create a simple bar chart to show spending per merchant
    st.header("Spending by Merchant")
    spend_by_merchant = df_invoices.groupby("merchant_name")["grand_total"].sum()
    st.bar_chart(spend_by_merchant)
else:
    st.warning("No invoices found! Make sure you run pipeline.py first.")

# 3. Fetch the individual items 
st.header("Itemized Breakdown")
items_response = supabase.table("invoice_items").select("*").execute()
if items_response.data:
    df_items = pd.DataFrame(items_response.data)
    # Hide the raw IDs to make the presentation look cleaner
    st.dataframe(df_items.drop(columns=["id", "invoice_id"], errors='ignore'), use_container_width=True)