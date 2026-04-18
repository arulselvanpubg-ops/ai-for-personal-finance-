import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from ai.router import route_ai_task
from ai.enhanced_services import enhanced_ai
from core.finance import calculate_financial_health_score, detect_anomalies, get_monthly_summary
from ui.statement_import import render_statement_import_ui


def show_dashboard():
    st.title("💰 FinSight AI Dashboard")

    render_statement_import_ui(
        key_prefix="dashboard",
        heading="📤 Import bank statement",
        show_sync_hint=True,
    )
    st.markdown("---")

    # Check if any real transactions exist
    from core.db import Transaction
    all_transactions = Transaction.find_all()
    has_data = bool(all_transactions)

    if not has_data:
        # ---- DUMMY / PREVIEW MODE ----
        from ui.dummy_data import (
            DUMMY_SUMMARY, DUMMY_HEALTH_SCORE, DUMMY_ANOMALIES
        )
        st.info(
            "👋 **Welcome to FinSight AI!** Below is a **sample preview** of what your dashboard "
            "will look like once you upload a bank statement above. All numbers are illustrative.",
            icon="🔍",
        )

        summary = DUMMY_SUMMARY
        score = DUMMY_HEALTH_SCORE
        anomalies = DUMMY_ANOMALIES
        is_dummy = True
    else:
        # ---- REAL DATA MODE ----
        now = datetime.now()

        available_years = set(
            t["date"].year for t in all_transactions if hasattr(t["date"], "year")
        )
        available_years.update(range(now.year - 2, now.year + 1))
        years_list = sorted(list(available_years))

        col_yr, col_mo, _ = st.columns([1, 1, 2])
        with col_yr:
            if "selected_year" not in st.session_state:
                st.session_state["selected_year"] = now.year
            st.selectbox("Year", years_list, key="selected_year")
        with col_mo:
            if "selected_month" not in st.session_state:
                st.session_state["selected_month"] = now.month
            st.selectbox("Month", range(1, 13), key="selected_month")

        summary = get_monthly_summary(
            st.session_state["selected_year"], st.session_state["selected_month"]
        )
        score = calculate_financial_health_score(
            st.session_state["selected_year"], st.session_state["selected_month"]
        )
        anomalies = detect_anomalies()
        is_dummy = False

    # ---- METRICS ----
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Financial Health Score",
            f"{score:.1f}/100",
            delta="Sample" if is_dummy else None,
        )
        if score >= 80:
            st.success("Excellent! 🌟")
        elif score >= 60:
            st.warning("Good, but room for improvement")
        else:
            st.error("Needs attention")

    with col2:
        st.metric(
            "Monthly Income",
            f"₹{summary['income']:,.2f}",
            delta="Sample" if is_dummy else None,
        )

    with col3:
        st.metric(
            "Monthly Expenses",
            f"₹{summary['expenses']:,.2f}",
            delta="Sample" if is_dummy else None,
        )

    # ---- INCOME vs EXPENSES CHART ----
    st.subheader("Income vs Expenses")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Income", "Expenses"],
            y=[summary["income"], summary["expenses"]],
            marker_color=["#0F4C5C", "#EE9B00"],
            text=[f"₹{summary['income']:,.0f}", f"₹{summary['expenses']:,.0f}"],
            textposition="auto",
        )
    )
    fig.update_layout(
        title="Current Month Overview" + (" (Sample Data)" if is_dummy else ""),
        yaxis_title="Amount (₹)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---- CATEGORY PIE ----
    st.subheader("Spending by Category")
    if summary["categories"]:
        fig2 = px.pie(
            values=list(summary["categories"].values()),
            names=list(summary["categories"].keys()),
            title="Expense Categories" + (" (Sample)" if is_dummy else ""),
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Teal,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No expense data available for this period.")

    # ---- NET SAVINGS BAR ----
    st.subheader("Net Savings")
    net = summary["income"] - summary["expenses"]
    st.metric("Net Cash Flow", f"₹{net:,.2f}", delta=f"₹{net:,.2f}")

    # ---- ANOMALIES ----
    st.subheader("⚠️ Anomalous Transactions")
    if anomalies:
        for a in anomalies[:5]:
            st.warning(f"High amount: ₹{a['amount']:,.2f} — {a['description']}")
    else:
        st.success("No anomalies detected.")

    # ---- AI INSIGHTS ----
    st.subheader("AI Insights")
    if is_dummy:
        st.caption("Upload your statement to get personalised AI insights.")
    else:
        # Show API provider status
        from ai.enhanced_services import get_api_provider_status
        provider_status = get_api_provider_status()
        
        # Show which APIs are available
        available_providers = [name for name, status in provider_status.items() if status['available']]
        
        if available_providers:
            st.success(f"AI Services: {', '.join(available_providers).title()}")
        else:
            st.warning("No API keys configured. Using basic insights.")
        
        # Enhanced insights with multiple providers
        if st.button("Generate Enhanced Insights"):
            with st.spinner("Generating AI insights..."):
                try:
                    from ai.enhanced_services import get_enhanced_dashboard_insights
                    
                    financial_data = {
                        'income': summary['income'],
                        'expenses': summary['expenses'],
                        'net': summary['income'] - summary['expenses'],
                        'categories': summary['categories']
                    }
                    
                    insights = get_enhanced_dashboard_insights(financial_data)
                    
                    # Display insights in organized sections
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Financial Health Analysis")
                        st.write(insights.get('health_analysis', 'Analysis unavailable'))
                        
                        st.markdown("### Spending Patterns")
                        st.write(insights.get('spending_analysis', 'Analysis unavailable'))
                    
                    with col2:
                        st.markdown("### Goals & Recommendations")
                        st.write(insights.get('goals_recommendations', 'Recommendations unavailable'))
                        
                        # Show API provider info
                        st.markdown("### API Provider")
                        st.info(f"Using: {enhanced_ai.primary_provider.title()}")
                    
                except Exception as e:
                    st.error(f"Enhanced insights unavailable: {e}")
                    # Fallback to original insights
                    insight = route_ai_task(
                        "insights",
                        year=st.session_state["selected_year"],
                        month=st.session_state["selected_month"],
                    )
                    st.write(insight)
        
        # Show setup guide if no APIs available
        if not available_providers:
            with st.expander("Setup AI API Keys"):
                st.markdown("""
                ### Enhance AI Insights with API Keys
                
                Configure API keys to get advanced AI-powered insights:
                
                **NVIDIA NIM** (Recommended): Free tier available
                **Google Gemini**: Free tier available  
                **Hugging Face**: Free tier available
                **OpenAI**: Paid API
                
                Add API keys to your environment variables or Streamlit secrets to enable enhanced features.
                """)