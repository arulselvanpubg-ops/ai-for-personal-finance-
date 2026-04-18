import streamlit as st
from core.db import Goal
from core.finance import calculate_financial_health_score
from datetime import datetime

def format_rupee(amount: float) -> str:
    """Format a number as Indian Rupees with comma separators."""
    return f"₹{amount:,.2f}"

def show_goals():
    st.title("🎯 Savings Goals")
    
    # Load existing goals
    goals = Goal.find_all()
    
    if not goals:
        from ui.dummy_data import DUMMY_GOALS
        st.info(
            "🎯 **Sample Preview** — These are example savings goals. "
            "Create your own real goals using the form below!",
            icon="🔍",
        )
        # Show read-only dummy goal cards
        for goal in DUMMY_GOALS:
            with st.container(border=True):
                target = float(goal["target_amount"])
                current = float(goal["current_amount"])
                target_date = goal["target_date"].date() if isinstance(goal["target_date"], datetime) else goal["target_date"]
                days_left = (target_date - datetime.now().date()).days
                progress = min(current / target if target else 0, 1)

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"{goal['name']} *(Sample)*")
                    st.progress(progress)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Target", format_rupee(target))
                    m2.metric("Saved", format_rupee(current), delta=f"{progress*100:.1f}%")
                    m3.metric("Remaining", format_rupee(max(0.0, target - current)), delta_color="inverse")
                    if days_left > 0:
                        monthly_needed = (max(0.0, target - current) / (days_left / 30.44)) if days_left > 30 else max(0.0, target - current)
                        st.info(f"💡 Save **{format_rupee(monthly_needed)}/month** to reach this by **{target_date.strftime('%d %b %Y')}** ({days_left} days left).")
                with col2:
                    st.caption("*Sample goal — create your own below*")
    else:
        for goal in goals:
            with st.container(border=True):
                target = float(goal.get("target_amount", 0))
                current = float(goal.get("current_amount", 0))
                name = goal.get("name", "Untitled Goal")
                goal_id = goal.get("_id")
                
                target_date = goal.get("target_date")
                if isinstance(target_date, str):
                    target_date = datetime.fromisoformat(target_date).date()
                elif isinstance(target_date, datetime):
                    target_date = target_date.date()
                
                today = datetime.now().date()
                days_left = (target_date - today).days
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(name)
                    progress = min(current / target if target else 0, 1)
                    
                    # Color coding for progress bar
                    if progress >= 1:
                        st.success(f"Goal Achieved! 🎊")
                        st.progress(1.0)
                    else:
                        st.progress(progress)
                        
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Target", format_rupee(target))
                    m2.metric("Saved", format_rupee(current), delta=f"{progress*100:.1f}%")
                    
                    remaining = max(0.0, target - current)
                    m3.metric("Remaining", format_rupee(remaining), delta_color="inverse")
                    
                    if progress < 1:
                        if days_left > 0:
                            monthly_needed = (remaining / (days_left / 30.44)) if days_left > 30 else remaining
                            daily_needed = remaining / days_left
                            
                            st.info(f"💡 To reach this goal by **{target_date.strftime('%d %b %Y')}** ({days_left} days left), "
                                    f"you need to save approximately **{format_rupee(monthly_needed)}/month**.")
                        else:
                            st.warning(f"⚠️ Target date has passed! You still need {format_rupee(remaining)} to reach your goal.")
                
                with col2:
                    st.write("### Actions")
                    # Contribution feature
                    contrib_amount = st.number_input("Add Contribution", min_value=0.0, step=100.0, key=f"contrib_{goal_id}")
                    if st.button("➕ Add", key=f"add_btn_{goal_id}", use_container_width=True):
                        if contrib_amount > 0:
                            new_amount = current + contrib_amount
                            Goal.update(goal_id, {"current_amount": new_amount})
                            st.success(f"Added {format_rupee(contrib_amount)}!")
                            st.rerun()
                    
                    st.divider()
                    
                    if st.button("🗑️ Delete Goal", key=f"del_{goal_id}", use_container_width=True, type="secondary"):
                        Goal.delete(goal_id)
                        st.rerun()

    st.markdown("---")
    st.subheader("🚀 Create a New Goal")
    with st.form("add_goal_form", clear_on_submit=True):
        name = st.text_input("What are you saving for? (e.g., New Car, Emergency Fund)")
        col_a, col_b = st.columns(2)
        with col_a:
            target_amount = st.number_input("Target amount (₹)", min_value=0.0, step=1000.0)
        with col_b:
            current_amount = st.number_input("Starting amount (₹)", min_value=0.0, step=100.0)
        
        target_date = st.date_input("Target date", min_value=datetime.now().date())
        
        submitted = st.form_submit_button("Create Goal", use_container_width=True)
        if submitted:
            if name and target_amount > 0:
                Goal.create(name=name, target_amount=target_amount, current_amount=current_amount, target_date=target_date)
                st.success(f"Goal '{name}' created successfully!")
                st.rerun()
            elif target_amount <= 0:
                st.error("Target amount must be greater than zero.")
            else:
                st.error("Please provide a goal name.")