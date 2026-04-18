#!/usr/bin/env python3
"""
Debug script to test bank statement upload functionality
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import tempfile
import os

def test_upload_ui():
    """Test the upload UI functionality"""
    st.title("Debug Bank Statement Upload")
    
    # Create a sample CSV file for testing
    sample_data = {
        'Date': ['2026-04-01', '2026-04-02', '2026-04-03'],
        'Description': ['Salary', 'Grocery', 'Electricity'],
        'Amount': [85000, -2500, -1200]
    }
    df = pd.DataFrame(sample_data)
    
    # Save to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_file_path = f.name
    
    st.write(f"Sample CSV created at: {temp_file_path}")
    st.write("Sample data:")
    st.dataframe(df)
    
    # Test file upload
    uploaded_file = st.file_uploader(
        "Upload bank statement",
        type=['csv', 'xlsx', 'pdf'],
        help="Upload your bank statement file"
    )
    
    if uploaded_file is not None:
        st.write(f"File uploaded: {uploaded_file.name}")
        st.write(f"File type: {uploaded_file.type}")
        st.write(f"File size: {uploaded_file.size} bytes")
        
        # Try to read the file
        try:
            if uploaded_file.name.endswith('.csv'):
                df_uploaded = pd.read_csv(uploaded_file)
                st.success("CSV file read successfully!")
                st.dataframe(df_uploaded)
            elif uploaded_file.name.endswith('.xlsx'):
                df_uploaded = pd.read_excel(uploaded_file)
                st.success("Excel file read successfully!")
                st.dataframe(df_uploaded)
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    # Clean up
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)

if __name__ == "__main__":
    test_upload_ui()
