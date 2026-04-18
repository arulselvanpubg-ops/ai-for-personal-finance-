#!/usr/bin/env python3
"""
Direct test of the upload functionality
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime

from ui.statement_import import process_uploaded_statement, StatementImportOutcome
from core.db import Transaction

def test_direct_upload():
    st.title("Direct Upload Test")
    
    # Create a sample file for download
    sample_data = {
        'Date': ['2026-04-01', '2026-04-02', '2026-04-03', '2026-04-04'],
        'Description': ['Salary Credit', 'Grocery Store', 'Electricity Bill', 'Restaurant'],
        'Amount': [85000, -2500, -1200, -800]
    }
    df = pd.DataFrame(sample_data)
    
    # Provide download link
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Sample CSV",
        data=csv,
        file_name="sample_bank_statement.csv",
        mime="text/csv"
    )
    
    st.write("Sample data preview:")
    st.dataframe(df)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your bank statement",
        type=['csv', 'xlsx', 'pdf'],
        help="Upload CSV, Excel, or PDF bank statement"
    )
    
    if uploaded_file:
        st.write(f"File uploaded: {uploaded_file.name}")
        
        if st.button("Process Upload"):
            with st.spinner("Processing..."):
                try:
                    outcome = process_uploaded_statement(uploaded_file)
                    
                    if outcome.success:
                        st.success(f"Success: {outcome.message}")
                        st.info(f"Processed {outcome.count} transactions")
                        
                        # Show current database state
                        transactions = Transaction.find_all()
                        st.write(f"Total transactions in database: {len(transactions)}")
                        
                        if transactions:
                            df_result = pd.DataFrame([
                                {
                                    'Date': tx['date'].strftime('%Y-%m-%d'),
                                    'Description': tx['description'],
                                    'Amount': tx['amount'],
                                    'Category': tx['category']
                                }
                                for tx in transactions[:10]  # Show first 10
                            ])
                            st.dataframe(df_result)
                    else:
                        st.error(f"Failed: {outcome.message}")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.exception(e)

if __name__ == "__main__":
    test_direct_upload()
