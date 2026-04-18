#!/usr/bin/env python3
"""
Improved bank statement upload interface
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime

from ui.statement_import import process_uploaded_statement
from core.db import Transaction

def improved_upload_interface():
    st.title("Improved Bank Statement Upload")
    
    # Step 1: File selection
    st.markdown("### Step 1: Choose Your Bank Statement")
    
    # Create tabs for different upload methods
    tab1, tab2, tab3 = st.tabs(["Upload PDF", "Use Sample", "Create Sample"])
    
    with tab1:
        st.markdown("#### Upload Your PDF Bank Statement")
        
        # Enhanced file uploader with better instructions
        uploaded_file = st.file_uploader(
            "Select PDF bank statement",
            type=['pdf'],
            help="Upload a text-based PDF bank statement (not scanned images)",
            key="pdf_uploader"
        )
        
        if uploaded_file:
            st.success(f"File selected: {uploaded_file.name}")
            
            # Show file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Type", uploaded_file.type)
            with col2:
                st.metric("Size", f"{uploaded_file.size:,} bytes")
            with col3:
                st.metric("Status", "Ready to upload")
    
    with tab2:
        st.markdown("#### Use Sample PDF")
        
        if os.path.exists("sample_bank_statement.pdf"):
            st.info("Sample PDF bank statement is available for testing")
            
            # Show sample info
            with open("sample_bank_statement.pdf", "rb") as f:
                sample_data = f.read()
            
            st.download_button(
                label="Download Sample PDF",
                data=sample_data,
                file_name="sample_bank_statement.pdf",
                mime="application/pdf"
            )
            
            if st.button("Use Sample PDF Directly", key="use_sample"):
                # Create a mock uploaded file
                class MockUploadedFile:
                    def __init__(self, name, data):
                        self.name = name
                        self._data = data
                        self.invert_amounts = False
                    
                    def getbuffer(self):
                        return self._data
                
                mock_file = MockUploadedFile("sample_bank_statement.pdf", sample_data)
                st.session_state.uploaded_file = mock_file
                st.success("Sample PDF loaded! Click 'Process Upload' below.")
        else:
            st.error("Sample PDF not found. Please create it first.")
    
    with tab3:
        st.markdown("#### Create Custom Sample")
        
        st.info("Create your own sample bank statement")
        
        # Simple form to create sample data
        with st.form("create_sample"):
            st.write("Enter sample transactions:")
            
            # Default sample data
            sample_transactions = [
                {"date": "2026-04-01", "description": "Salary Credit", "amount": 85000.00},
                {"date": "2026-04-02", "description": "Grocery Store", "amount": -2500.00},
                {"date": "2026-04-03", "description": "Electricity Bill", "amount": -1200.00},
                {"date": "2026-04-04", "description": "Restaurant", "amount": -800.00},
                {"date": "2026-04-05", "description": "Fuel Station", "amount": -2000.00},
            ]
            
            # Allow editing
            edited_data = []
            for i, tx in enumerate(sample_transactions):
                col1, col2, col3 = st.columns(3)
                with col1:
                    date = st.date_input(f"Date {i+1}", value=datetime.strptime(tx["date"], "%Y-%m-%d").date(), key=f"date_{i}")
                with col2:
                    desc = st.text_input(f"Description {i+1}", value=tx["description"], key=f"desc_{i}")
                with col3:
                    amount = st.number_input(f"Amount {i+1}", value=tx["amount"], key=f"amt_{i}")
                
                edited_data.append({"date": date, "description": desc, "amount": amount})
            
            if st.form_submit_button("Create Sample PDF"):
                # Create CSV from the data
                df = pd.DataFrame(edited_data)
                csv_data = df.to_csv(index=False)
                
                # Store in session state
                st.session_state.sample_csv = csv_data
                st.success("Sample data created! You can now download and convert to PDF.")
                
                st.download_button(
                    label="Download Sample CSV",
                    data=csv_data,
                    file_name="custom_sample.csv",
                    mime="text/csv"
                )
    
    # Step 2: Upload options
    st.markdown("---")
    st.markdown("### Step 2: Upload Options")
    
    # Invert amounts checkbox
    invert_amounts = st.checkbox(
        "Treat all amounts as expenses (invert signs)",
        value=True,
        help="Check this if your bank exports expenses as positive numbers"
    )
    
    # Step 3: Process upload
    st.markdown("---")
    st.markdown("### Step 3: Process Upload")
    
    # Check if we have a file to process
    uploaded_file = uploaded_file or st.session_state.get("uploaded_file")
    
    if uploaded_file:
        st.info("File ready for processing")
        
        if st.button("Process Upload", type="primary", key="process_upload"):
            with st.spinner("Processing your bank statement..."):
                try:
                    # Set invert amounts
                    uploaded_file.invert_amounts = invert_amounts
                    
                    # Process the upload
                    outcome = process_uploaded_statement(uploaded_file)
                    
                    if outcome.success:
                        st.success(f"Success! {outcome.message}")
                        st.info(f"Processed {outcome.count} transactions")
                        
                        # Show results
                        st.markdown("### Upload Results")
                        
                        transactions = Transaction.find_all()
                        st.write(f"Total transactions in database: {len(transactions)}")
                        
                        if transactions:
                            # Show summary
                            income = sum(tx['amount'] for tx in transactions if tx['amount'] > 0)
                            expenses = abs(sum(tx['amount'] for tx in transactions if tx['amount'] < 0))
                            net = income - expenses
                            
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Total Income", f"Rs.{income:,.2f}")
                            col2.metric("Total Expenses", f"Rs.{expenses:,.2f}")
                            col3.metric("Net Cash Flow", f"Rs.{net:,.2f}")
                            
                            # Show recent transactions
                            st.markdown("#### Recent Transactions")
                            df_display = pd.DataFrame([
                                {
                                    "Date": tx["date"].strftime("%Y-%m-%d"),
                                    "Description": tx["description"],
                                    "Amount": tx["amount"],
                                    "Category": tx["category"]
                                }
                                for tx in transactions[:10]
                            ])
                            st.dataframe(df_display, use_container_width=True)
                        
                        # Clear session state
                        if "uploaded_file" in st.session_state:
                            del st.session_state.uploaded_file
                        
                    else:
                        st.error(f"Upload failed: {outcome.message}")
                        
                except Exception as e:
                    st.error(f"Error processing upload: {e}")
                    st.exception(e)
    else:
        st.warning("Please select a file to upload first")
    
    # Step 4: Check current database
    st.markdown("---")
    st.markdown("### Current Database Status")
    
    if st.button("Check Database"):
        try:
            transactions = Transaction.find_all()
            st.write(f"Total transactions: {len(transactions)}")
            
            if transactions:
                # Show summary stats
                income = sum(tx['amount'] for tx in transactions if tx['amount'] > 0)
                expenses = abs(sum(tx['amount'] for tx in transactions if tx['amount'] < 0))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Income", f"Rs.{income:,.2f}")
                    st.metric("Expenses", f"Rs.{expenses:,.2f}")
                with col2:
                    st.metric("Transactions", len(transactions))
                    st.metric("Categories", len(set(tx['category'] for tx in transactions)))
                
                # Show recent transactions
                with st.expander("View Recent Transactions"):
                    df_display = pd.DataFrame([
                        {
                            "Date": tx["date"].strftime("%Y-%m-%d"),
                            "Description": tx["description"][:30],
                            "Amount": tx["amount"],
                            "Category": tx["category"]
                        }
                        for tx in transactions[:20]
                    ])
                    st.dataframe(df_display, use_container_width=True)
            else:
                st.info("No transactions in database")
                
        except Exception as e:
            st.error(f"Error checking database: {e}")

if __name__ == "__main__":
    improved_upload_interface()
