import streamlit as st
import pandas as pd
from core.db import Transaction
from core.parser import import_transactions
from ai.router import route_ai_task
from datetime import datetime

def show_expenses():
    st.title("📊 Expense Tracker")
    
    # Import section
    st.subheader("Import Transactions")
    uploaded_file = st.file_uploader("Upload CSV or PDF", type=['csv', 'pdf'])
    
    if uploaded_file and st.button("Import"):
        # Save file temporarily
        with open("temp_import_file", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            transactions = import_transactions("temp_import_file")
            
            # Auto-categorize
            for tx in transactions:
                tx['category'] = route_ai_task('categorize', description=tx['description'])
            
            # Save to DB
            for tx in transactions:
                Transaction.create(
                    date=tx['date'],
                    amount=tx['amount'],
                    description=tx['description'],
                    category=tx['category']
                )
            
            st.success(f"Imported {len(transactions)} transactions!")
            
            # Clean up
            import os
            os.remove("temp_import_file")
            
        except Exception as e:
            st.error(f"Import failed: {str(e)}")
    
    # Manual entry
    st.subheader("Add Transaction")
    with st.form("add_transaction"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date")
            amount = st.number_input("Amount", step=0.01)
        
        with col2:
            description = st.text_input("Description")
            category = st.selectbox("Category", [
                "Food & Dining", "Transportation", "Shopping", "Entertainment",
                "Bills & Utilities", "Healthcare", "Education", "Travel", "Other"
            ])
        
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Add Transaction"):
            if description and amount != 0:
                Transaction.create(
                    date=datetime.combine(date, datetime.min.time()),
                    amount=amount,
                    description=description,
                    category=category,
                    notes=notes
                )
                st.success("Transaction added!")
            else:
                st.error("Please fill in description and amount.")
    
    # Transaction table
    st.subheader("Recent Transactions")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_category = st.selectbox("Filter by Category", ["All"] + [
            "Food & Dining", "Transportation", "Shopping", "Entertainment",
            "Bills & Utilities", "Healthcare", "Education", "Travel", "Other"
        ])
    
    with col2:
        filter_date = st.date_input("From Date", value=datetime.now() - pd.DateOffset(months=1))
    
    with col3:
        search = st.text_input("Search Description")
    
    # Query transactions
    transactions = Transaction.find_all()
    
    # Filter
    filtered = transactions
    if filter_category != "All":
        filtered = [t for t in filtered if t['category'] == filter_category]
    
    if filter_date:
        filtered = [t for t in filtered if t['date'] >= datetime.combine(filter_date, datetime.min.time())]
    
    if search:
        filtered = [t for t in filtered if search.lower() in t['description'].lower()]
    
    if filtered:
        df = pd.DataFrame([{
            'Date': t['date'].strftime('%Y-%m-%d'),
            'Amount': f"${t['amount']:.2f}",
            'Description': t['description'],
            'Category': t['category'],
            'Notes': t.get('notes', '') or ''
        } for t in filtered])
        
        st.dataframe(df, width='stretch')
    else:
        st.info("No transactions found.")