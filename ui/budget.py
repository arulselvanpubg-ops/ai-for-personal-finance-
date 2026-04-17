from datetime import datetime

import streamlit as st

from ai.router import route_ai_task
from core.db import Budget, Category
from core.finance import get_budget_progress
from utils.monitoring import log_event
from utils.validators import sanitize_input


def show_budget():
    st.title("Budget Planner")

    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    progress = get_budget_progress()

    st.subheader("AI Budget Recommendations")
    if st.button("Get Budget Suggestions"):
        with st.spinner("Analyzing your spending..."):
            suggestion = route_ai_task("budget_suggest")
            st.write(suggestion)

    st.subheader("Budget Progress")
    if progress:
        for category, data in progress.items():
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.write(f"**{category}**")
            with col2:
                st.write(f"Budget: ${data['budgeted']:.2f}")
            with col3:
                st.write(f"Spent: ${data['spent']:.2f}")
            with col4:
                percentage = data["percentage"]
                if percentage > 100:
                    st.error(f"Over: {percentage:.1f}%")
                elif percentage > 80:
                    st.warning(f"{percentage:.1f}%")
                else:
                    st.success(f"{percentage:.1f}%")

            st.progress(min(1.0, percentage / 100))
            st.markdown("---")
    else:
        st.info("No budgets set for this month.")

    st.subheader("Set Monthly Budgets")
    categories = Category.find_all()
    category_names = [cat["name"] for cat in categories]

    with st.expander("Add New Category"):
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
        st.write("Set budgets for current month:")

        budget_data = {}
        for cat in categories:
            budget_data[cat["name"]] = st.number_input(
                f"{cat['name']} Budget ($)",
                value=cat.get("budget", 0.0),
                min_value=0.0,
                step=10.0,
            )

        if st.form_submit_button("Save Budgets"):
            for cat in categories:
                new_budget = budget_data[cat["name"]]
                Category.update_budget(cat["name"], new_budget)
                Budget.create(cat["name"], month_str, new_budget)

            log_event("info", "budgets_saved", month=month_str, categories=len(categories))
            st.success("Budgets saved!")
            st.rerun()
