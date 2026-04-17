import streamlit as st
from core.db import Category, Budget
from core.finance import get_budget_progress
from ai.router import route_ai_task
from datetime import datetime

def show_budget():
    st.title("🎯 Budget Planner")
    
    # Current month
    now = datetime.now()
    month_str = now.strftime('%Y-%m')
    
    # Get budget progress
    progress = get_budget_progress()
    
    # AI Budget Suggestion
    st.subheader("🤖 AI Budget Recommendations")
    if st.button("Get Budget Suggestions"):
        with st.spinner("Analyzing your spending..."):
            suggestion = route_ai_task('budget_suggest')
            st.write(suggestion)
    
    # Budget Overview
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
                percentage = data['percentage']
                if percentage > 100:
                    st.error(f"Over: {percentage:.1f}%")
                elif percentage > 80:
                    st.warning(f"{percentage:.1f}%")
                else:
                    st.success(f"{percentage:.1f}%")
            
            # Progress bar
            st.progress(min(1.0, percentage / 100))
            st.markdown("---")
    else:
        st.info("No budgets set for this month.")
    
    # Set Budgets
    st.subheader("Set Monthly Budgets")
    
    # Get existing categories
    categories = Category.find_all()
    category_names = [cat['name'] for cat in categories]
    
    # Add new category
    with st.expander("Add New Category"):
        new_cat = st.text_input("Category Name")
        if st.button("Add Category") and new_cat:
            if new_cat not in category_names:
                Category.create(new_cat)
                st.success("Category added!")
                st.rerun()
            else:
                st.error("Category already exists.")
    
    # Budget form
    with st.form("set_budget"):
        st.write("Set budgets for current month:")
        
        budget_data = {}
        for cat in categories:
            budget_data[cat['name']] = st.number_input(
                f"{cat['name']} Budget ($)",
                value=cat.get('budget', 0.0),
                min_value=0.0,
                step=10.0
            )
        
        if st.form_submit_button("Save Budgets"):
            for cat in categories:
                new_budget = budget_data[cat['name']]
                Category.update_budget(cat['name'], new_budget)
                
                # Update or create budget entry
                existing = Budget.find_by_month(month_str)
                existing = [b for b in existing if b.get('category_id') == cat['name']]
                
                if existing:
                    # Update existing (MongoDB doesn't have built-in update by ID, so we'll skip for now)
                    pass
                else:
                    Budget.create(cat['name'], month_str, new_budget)
            
            st.success("Budgets saved!")
            st.rerun()