#!/usr/bin/env python3
"""
Comprehensive PDF upload debugging tool
"""

import streamlit as st
import tempfile
import os
from datetime import datetime

def debug_pdf_upload():
    st.title("PDF Upload Debug Tool")
    
    st.markdown("### Step 1: Check PDF File")
    
    # Check if sample PDF exists
    pdf_exists = os.path.exists("sample_bank_statement.pdf")
    st.write(f"Sample PDF exists: {pdf_exists}")
    
    if pdf_exists:
        st.info("Sample PDF found in project directory")
        
        # Show PDF info
        file_size = os.path.getsize("sample_bank_statement.pdf")
        st.write(f"File size: {file_size} bytes")
        
        # Provide download link
        with open("sample_bank_statement.pdf", "rb") as f:
            st.download_button(
                label="Download Sample PDF",
                data=f.read(),
                file_name="sample_bank_statement.pdf",
                mime="application/pdf"
            )
    
    st.markdown("### Step 2: Upload PDF File")
    
    uploaded_file = st.file_uploader(
        "Upload PDF bank statement",
        type=['pdf'],
        help="Upload your PDF bank statement"
    )
    
    if uploaded_file:
        st.write(f"Uploaded file: {uploaded_file.name}")
        st.write(f"File type: {uploaded_file.type}")
        st.write(f"File size: {uploaded_file.size} bytes")
        
        # Test file content
        try:
            content = uploaded_file.getbuffer()
            st.write(f"Content length: {len(content)} bytes")
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            st.write(f"Temp file saved: {temp_path}")
            
            # Test parsing
            st.markdown("### Step 3: Test PDF Parsing")
            
            if st.button("Test PDF Parsing"):
                with st.spinner("Testing PDF parsing..."):
                    try:
                        from core.parser import import_transactions
                        
                        transactions = import_transactions(temp_path)
                        st.success(f"Successfully parsed {len(transactions)} transactions")
                        
                        if transactions:
                            st.write("First 3 transactions:")
                            for i, tx in enumerate(transactions[:3]):
                                st.write(f"{i+1}. {tx['date'].strftime('%Y-%m-%d')} - {tx['description']} - {tx['amount']}")
                        
                    except Exception as e:
                        st.error(f"Error parsing PDF: {e}")
                        st.exception(e)
            
            # Test full upload process
            st.markdown("### Step 4: Test Full Upload Process")
            
            if st.button("Test Full Upload"):
                with st.spinner("Testing full upload process..."):
                    try:
                        from ui.statement_import import process_uploaded_statement
                        
                        # Mock the uploaded file
                        class MockFile:
                            def __init__(self, name, content):
                                self.name = name
                                self._content = content
                                self.invert_amounts = False
                            
                            def getbuffer(self):
                                return self._content
                        
                        mock_file = MockFile(uploaded_file.name, content)
                        outcome = process_uploaded_statement(mock_file)
                        
                        if outcome.success:
                            st.success(f"Upload successful: {outcome.message}")
                            st.info(f"Processed {outcome.count} transactions")
                        else:
                            st.error(f"Upload failed: {outcome.message}")
                    
                    except Exception as e:
                        st.error(f"Error in upload process: {e}")
                        st.exception(e)
            
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
        except Exception as e:
            st.error(f"Error processing uploaded file: {e}")
            st.exception(e)
    
    st.markdown("### Step 5: Check Database")
    
    if st.button("Check Database"):
        try:
            from core.db import Transaction
            
            transactions = Transaction.find_all()
            st.write(f"Total transactions in database: {len(transactions)}")
            
            if transactions:
                st.write("Recent transactions:")
                for tx in transactions[:5]:
                    st.write(f"- {tx['date'].strftime('%Y-%m-%d')} - {tx['description']} - {tx['amount']}")
            else:
                st.info("No transactions in database")
        
        except Exception as e:
            st.error(f"Error checking database: {e}")
            st.exception(e)

if __name__ == "__main__":
    debug_pdf_upload()
