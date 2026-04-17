from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import streamlit as st

from ai.router import route_ai_task
from core.db import Transaction
from core.parser import import_transactions
from utils.monitoring import log_event, log_exception
from utils.validators import sanitize_input, validate_amount


def show_expenses():
    st.title("Expense Tracker")

    st.subheader("Import Transactions")
    uploaded_file = st.file_uploader("Upload CSV or PDF", type=["csv", "pdf"])

    if uploaded_file and st.button("Import"):
        temp_path = None
        try:
            suffix = Path(uploaded_file.name).suffix.lower()
            with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_path = temp_file.name

            transactions = import_transactions(temp_path)
            if not transactions:
                st.warning("No valid transactions were found in that file.")
                return

            for tx in transactions:
                tx["category"] = route_ai_task(
                    "categorize",
                    description=tx["description"],
                )

            for tx in transactions:
                Transaction.create(
                    date=tx["date"],
                    amount=tx["amount"],
                    description=tx["description"],
                    category=tx["category"],
                )

            log_event(
                "info",
                "transactions_imported",
                count=len(transactions),
                filename=uploaded_file.name,
            )
            st.success(f"Imported {len(transactions)} transactions!")
        except Exception as exc:
            log_exception("transaction_import_failed", exc, filename=uploaded_file.name)
            st.error("Import failed. Please check the file format and try again.")
        finally:
            if temp_path and Path(temp_path).exists():
                Path(temp_path).unlink(missing_ok=True)

    st.subheader("Add Transaction")
    with st.form("add_transaction"):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date")
            amount = st.number_input("Amount", step=0.01)

        with col2:
            description = st.text_input("Description")
            category = st.selectbox(
                "Category",
                [
                    "Food & Dining",
                    "Transportation",
                    "Shopping",
                    "Entertainment",
                    "Bills & Utilities",
                    "Healthcare",
                    "Education",
                    "Travel",
                    "Other",
                ],
            )

        notes = st.text_area("Notes")

        if st.form_submit_button("Add Transaction"):
            description = sanitize_input(description, max_length=200)
            notes = sanitize_input(notes, max_length=500)
            if description and validate_amount(amount):
                Transaction.create(
                    date=datetime.combine(date, datetime.min.time()),
                    amount=amount,
                    description=description,
                    category=category,
                    notes=notes,
                )
                log_event("info", "transaction_created", category=category, amount=amount)
                st.success("Transaction added!")
            else:
                st.error("Please enter a description and a non-zero amount.")

    st.subheader("Recent Transactions")

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All"]
            + [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Education",
                "Travel",
                "Other",
            ],
        )

    with col2:
        filter_date = st.date_input(
            "From Date",
            value=datetime.now() - pd.DateOffset(months=1),
        )

    with col3:
        search = st.text_input("Search Description")

    transactions = Transaction.find_all()

    filtered = transactions
    if filter_category != "All":
        filtered = [t for t in filtered if t["category"] == filter_category]

    if filter_date:
        start_date = datetime.combine(filter_date, datetime.min.time())
        filtered = [t for t in filtered if t["date"] >= start_date]

    if search:
        query = search.lower().strip()
        filtered = [t for t in filtered if query in t["description"].lower()]

    if filtered:
        df = pd.DataFrame(
            [
                {
                    "Date": t["date"].strftime("%Y-%m-%d"),
                    "Amount": f"${t['amount']:.2f}",
                    "Description": t["description"],
                    "Category": t["category"],
                    "Notes": t.get("notes", "") or "",
                }
                for t in filtered
            ]
        )

        st.dataframe(df, width="stretch")
    else:
        st.info("No transactions found.")
