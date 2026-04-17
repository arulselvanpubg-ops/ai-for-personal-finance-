import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from core.finance import calculate_financial_health_score, get_monthly_summary, detect_anomalies
from ai.router import route_ai_task
from datetime import datetime

def show_dashboard():
    st.title("💰 FinSight AI Dashboard")
    
    # Financial Health Score
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = calculate_financial_health_score()
        st.metric("Financial Health Score", f"{score:.1f}/100")
        
        # Color coding
        if score >= 80:
            st.success("Excellent!")
        elif score >= 60:
            st.warning("Good, but room for improvement")
        else:
            st.error("Needs attention")
    
    # Current month summary
    now = datetime.now()
    summary = get_monthly_summary(now.year, now.month)
    
    with col2:
        st.metric("Monthly Income", f"${summary['income']:.2f}")
    
    with col3:
        st.metric("Monthly Expenses", f"${summary['expenses']:.2f}")
    
    # Income vs Expenses Chart
    st.subheader("Income vs Expenses")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Income', 'Expenses'],
        y=[summary['income'], summary['expenses']],
        marker_color=['#0F4C5C', '#EE9B00']
    ))
    fig.update_layout(
        title="Current Month Overview",
        yaxis_title="Amount ($)"
    )
    st.plotly_chart(fig, width='stretch')
    
    # Category Breakdown
    st.subheader("Spending by Category")
    
    if summary['categories']:
        categories = list(summary['categories'].keys())
        amounts = list(summary['categories'].values())
        
        fig2 = px.pie(
            values=amounts,
            names=categories,
            title="Expense Categories",
            color_discrete_sequence=px.colors.sequential.Teal
        )
        st.plotly_chart(fig2, width='stretch')
    else:
        st.info("No expense data available yet.")
    
    # Anomalies
    st.subheader("⚠️ Anomalous Transactions")
    anomalies = detect_anomalies()
    
    if anomalies:
        for anomaly in anomalies[:5]:  # Show top 5
            st.warning(f"High amount transaction: ${anomaly['amount']:.2f} - {anomaly['description']}")
    else:
        st.success("No anomalies detected.")
    
    # AI Insights
    st.subheader("🤖 AI Insights")
    if st.button("Generate Monthly Summary"):
        with st.spinner("Generating insights..."):
            insight = route_ai_task('insights', year=now.year, month=now.month)
            st.write(insight)