from datetime import datetime

import pandas as pd
import streamlit as st

from core.db import Transaction
from ui.statement_import import render_statement_import_ui
from utils.monitoring import log_event
from utils.validators import sanitize_input, validate_amount


def show_expenses():
    st.title("💳 Expense Tracker")

    render_statement_import_ui(
        key_prefix="expenses",
        heading="Import Transactions",
        show_sync_hint=False,
    )
    st.caption(
        "You can also import from **Dashboard**. All pages use the same saved transactions."
    )

    # ---- Add Transaction Form (always visible) ----
    st.subheader("Add Transaction")
    with st.form("add_transaction"):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date")
            amount = st.number_input("Amount (positive = income, negative = expense)", step=0.01)

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
                st.rerun()
            else:
                st.error("Please enter a description and a non-zero amount.")

    st.markdown("---")
    st.subheader("Recent Transactions")

    # Check real data
    transactions = Transaction.find_all()
    has_data = bool(transactions)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All"] + [
                "Food & Dining", "Transportation", "Shopping", "Entertainment",
                "Bills & Utilities", "Healthcare", "Education", "Travel", "Other",
            ],
        )
    with col2:
        filter_date = st.date_input(
            "From Date",
            value=datetime.now() - pd.DateOffset(months=1),
        )
    with col3:
        search = st.text_input("Search Description")

    if not has_data:
        # ---- DUMMY / PREVIEW MODE ----
        from ui.dummy_data import DUMMY_TRANSACTIONS

        st.info(
            "📋 **Sample Preview** — No real transactions yet. "
            "Upload a bank statement to see your actual data.",
            icon="🔍",
        )

        display_df = DUMMY_TRANSACTIONS.copy()

        # Apply filters on dummy data too
        if filter_category != "All":
            display_df = display_df[display_df["Category"] == filter_category]
        if search:
            display_df = display_df[
                display_df["Description"].str.contains(search, case=False, na=False)
            ]

        st.dataframe(
            display_df.drop(columns=["_id"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
                "Date": st.column_config.DateColumn("Date"),
            },
        )
        return

    # ---- REAL DATA MODE ----
    filtered = transactions
    if filter_category != "All":
        filtered = [t for t in filtered if t["category"] == filter_category]
    if filter_date:
        start_dt = datetime.combine(filter_date, datetime.min.time())
        filtered = [t for t in filtered if t["date"] >= start_dt]
    if search:
        q = search.lower().strip()
        filtered = [t for t in filtered if q in t["description"].lower()]

    def save_changes():
        changes = st.session_state.get("expense_editor", {})
        has_changes = False

        for row_idx, edits in changes.get("edited_rows", {}).items():
            tx_id = st.session_state["current_df"].iloc[row_idx]["_id"]
            update_data = {}
            if "Amount" in edits:
                update_data["amount"] = float(edits["Amount"])
            if "Description" in edits:
                update_data["description"] = edits["Description"]
            if "Category" in edits:
                update_data["category"] = edits["Category"]
            if "Notes" in edits:
                update_data["notes"] = edits["Notes"]
            if "Date" in edits:
                try:
                    update_data["date"] = datetime.strptime(str(edits["Date"])[:10], "%Y-%m-%d")
                except Exception:
                    pass
            if update_data:
                Transaction.update(tx_id, update_data)
                has_changes = True

        for row_idx in changes.get("deleted_rows", []):
            tx_id = st.session_state["current_df"].iloc[row_idx]["_id"]
            Transaction.delete(tx_id)
            has_changes = True

        if has_changes:
            st.toast("Transactions updated successfully!", icon="✅")

    if filtered:
        df = pd.DataFrame(
            [
                {
                    "_id": str(t.get("_id", t.get("id"))),
                    "Date": t["date"].date() if hasattr(t["date"], "date") else t["date"],
                    "Amount": float(t["amount"]),
                    "Description": t["description"],
                    "Category": t["category"],
                    "Notes": t.get("notes", "") or "",
                }
                for t in filtered
            ]
        )
        st.session_state["current_df"] = df

        csv_data = df.drop(columns=["_id"]).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv_data,
            file_name="finsight_transactions.csv",
            mime="text/csv",
        )

        st.data_editor(
            df,
            column_config={
                "_id": None,
                "Amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
                "Date": st.column_config.DateColumn("Date"),
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    options=[
                        "Food & Dining", "Transportation", "Shopping", "Entertainment",
                        "Bills & Utilities", "Healthcare", "Education", "Travel", "Other",
                    ],
                ),
            },
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
            key="expense_editor",
            on_change=save_changes,
        )
    else:
        st.info("No transactions match the current filters.")
