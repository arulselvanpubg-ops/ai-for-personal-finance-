from datetime import datetime

import streamlit as st

from ai.router import route_ai_task
from core.db import Budget, Category, Transaction
from core.finance import get_budget_progress
from utils.monitoring import log_event
from utils.validators import sanitize_input


def show_budget():
    st.title("📊 Budget Planner")

    now = datetime.now()
    month_str = now.strftime("%Y-%m")

    # Check if real data exists
    real_transactions = Transaction.find_all()
    has_data = bool(real_transactions)

    # ---- AI Budget Suggestions ----
    st.subheader("🤖 AI Budget Recommendations")
    if has_data:
        if st.button("Get Budget Suggestions"):
            with st.spinner("Analyzing your spending..."):
                suggestion = route_ai_task("budget_suggest")
                st.write(suggestion)
    else:
        st.caption("Upload a bank statement to get personalised AI budget suggestions.")

    # ---- Budget Progress ----
    st.subheader("Budget Progress")

    if not has_data:
        # ---- DUMMY / PREVIEW MODE ----
        from ui.dummy_data import DUMMY_BUDGET_PROGRESS

        st.info(
            "📋 **Sample Preview** — Set your budgets below and upload statements to track real spending.",
            icon="🔍",
        )

        for category, data in DUMMY_BUDGET_PROGRESS.items():
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                col1.write(f"**{category}**")
                col2.write(f"Budget: ₹{data['budgeted']:,.0f}")
                col3.write(f"Spent: ₹{data['spent']:,.0f}")
                pct = data["percentage"]
                with col4:
                    if pct > 100:
                        st.error(f"Over: {pct:.1f}%")
                    elif pct > 80:
                        st.warning(f"{pct:.1f}%")
                    else:
                        st.success(f"{pct:.1f}%")
                st.progress(min(1.0, pct / 100))
    else:
        # ---- REAL DATA MODE ----
        progress = get_budget_progress()
        if progress:
            for category, data in progress.items():
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    col1.write(f"**{category}**")
                    col2.write(f"Budget: ₹{data['budgeted']:,.2f}")
                    col3.write(f"Spent: ₹{data['spent']:,.2f}")
                    pct = data["percentage"]
                    with col4:
                        if pct > 100:
                            st.error(f"Over: {pct:.1f}%")
                        elif pct > 80:
                            st.warning(f"{pct:.1f}%")
                        else:
                            st.success(f"{pct:.1f}%")
                    st.progress(min(1.0, pct / 100))
        else:
            st.info("No budgets set for this month. Use the form below to set budgets.")

    # ---- Set Monthly Budgets (always visible) ----
    st.markdown("---")
    st.subheader("Set Monthly Budgets")
    categories = Category.find_all()
    category_names = [cat["name"] for cat in categories]

    with st.expander("➕ Add New Category"):
        new_cat = st.text_input("Category Name")
        if st.button("Add Category") and new_cat:
            new_cat = sanitize_input(new_cat, max_length=80)
            if new_cat not in category_names:
                Category.create(new_cat)
                log_event("info", "category_created", category=new_cat)
                st.success("Category added!")
                st.rerun()
            else:
                st.error("Category already exists.")

    with st.form("set_budget"):
        st.write(f"Set budgets for **{now.strftime('%B %Y')}**:")

        budget_data = {}
        for cat in categories:
            budget_data[cat["name"]] = st.number_input(
                f"{cat['name']} Budget (₹)",
                value=cat.get("budget", 0.0),
                min_value=0.0,
                step=500.0,
            )

        if st.form_submit_button("💾 Save Budgets", use_container_width=True):
            for cat in categories:
                new_budget = budget_data[cat["name"]]
                Category.update_budget(cat["name"], new_budget)
                Budget.create(cat["name"], month_str, new_budget)

            log_event("info", "budgets_saved", month=month_str, categories=len(categories))
            st.success("Budgets saved successfully!")
            st.rerun()
