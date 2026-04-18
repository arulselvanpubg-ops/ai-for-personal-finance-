import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

from core.db import Transaction
from core.export import generate_excel_report, generate_pdf_report

def show_reports():
    st.title("📄 Reports & Export")

    # Check if real data exists
    transactions = Transaction.find_all()
    has_data = bool(transactions)

    if not has_data:
        # ---- DUMMY / PREVIEW MODE ----
        from ui.dummy_data import DUMMY_TRANSACTIONS, DUMMY_REPORT_SUMMARY

        st.info(
            "📋 **Sample Preview** — Upload a bank statement to generate real reports and export your actual financial data.",
            icon="🔍",
        )

        df = DUMMY_TRANSACTIONS.drop(columns=["_id"]).copy()
        income = DUMMY_REPORT_SUMMARY["income"]
        expenses = DUMMY_REPORT_SUMMARY["expenses"]
        net = DUMMY_REPORT_SUMMARY["net"]

        col_inc, col_exp, col_net = st.columns(3)
        col_inc.metric("Total Income (Sample)", f"₹{income:,.2f}")
        col_exp.metric("Total Expenses (Sample)", f"₹{expenses:,.2f}")
        col_net.metric("Net Cash Flow (Sample)", f"₹{net:,.2f}")

        st.markdown("---")
        st.subheader("Visual Analytics (Sample)")

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            exp_df = df[df["Amount"] < 0].copy()
            exp_df["Amount"] = exp_df["Amount"].abs()
            cat_totals = exp_df.groupby("Category")["Amount"].sum().reset_index()
            fig_pie = px.pie(cat_totals, values="Amount", names="Category", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.Teal,
                             title="Expenses by Category")
            st.plotly_chart(fig_pie, use_container_width=True)

        with chart_col2:
            trend_df = df.copy()
            trend_df["Type"] = trend_df["Amount"].apply(lambda x: "Income" if x > 0 else "Expense")
            trend_df["Amount"] = trend_df["Amount"].abs()
            daily = trend_df.groupby(["Date", "Type"])["Amount"].sum().reset_index()
            fig_bar = px.bar(daily, x="Date", y="Amount", color="Type",
                             color_discrete_map={"Income": "#0F4C5C", "Expense": "#EE9B00"},
                             barmode="group", title="Cash Flow Trend")
            fig_bar.update_layout(yaxis_title="Amount (₹)")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        st.subheader("Data Preview (Sample)")
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Amount": st.column_config.NumberColumn("Amount", format="₹%.2f")})
        return

    # ---- REAL DATA MODE ----
    st.subheader("Filter Data")
        
    data = []
    for t in transactions:
        tx_date = t.get('date')
        try:
            if hasattr(tx_date, 'date'):
                d = tx_date.date()
            else:
                d = pd.to_datetime(tx_date).date()
            
            # Sanity check: ignore extremely old/invalid dates (like 0001-11-11)
            if d.year < 2000: # Assuming data should be recent
                d = date.today()
        except Exception:
            d = date.today()
            
        data.append({
            '_id': str(t.get('_id', t.get('id'))),
            'Date': d,
            'Amount': float(t.get('amount', 0)),
            'Description': t.get('description', 'No Description'),
            'Category': t.get('category', 'Other'),
            'Notes': t.get('notes', '')
        })
    df = pd.DataFrame(data)
    
    # Calculate sensible default boundaries
    today = date.today()
    default_start = date(today.year, 1, 1)
    
    # Data bounds for constraints
    data_min = df['Date'].min()
    data_max = df['Date'].max()
    
    # Ensure defaults are within data bounds for st.date_input if possible, 
    # but allow user to see what they expect (Jan 2026 to Now)
    start_val = max(data_min, default_start) if data_min else default_start
    end_val = today
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        start_date = st.date_input("Start Date", value=start_val)
    with col2:
        end_date = st.date_input("End Date", value=end_val)
        
    with col3:
        all_categories = sorted(df['Category'].unique())
        selected_categories = st.multiselect("Categories", options=all_categories, default=all_categories)
        
    # Apply filters
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date) & (df['Category'].isin(selected_categories))
    filtered_df = df.loc[mask].copy()
    
    if filtered_df.empty:
        st.warning("No data found for the selected filters.")
        return
        
    # 2. Key Metrics
    st.markdown("---")
    
    income = filtered_df[filtered_df['Amount'] > 0]['Amount'].sum()
    expenses = abs(filtered_df[filtered_df['Amount'] < 0]['Amount'].sum())
    net = income - expenses
    
    col_inc, col_exp, col_net = st.columns(3)
    col_inc.metric("Total Income", f"₹{income:,.2f}")
    col_exp.metric("Total Expenses", f"₹{expenses:,.2f}")
    col_net.metric("Net Cash Flow", f"₹{net:,.2f}", delta=f"₹{net:,.2f}", delta_color="normal")
    
    # 3. Charts
    st.markdown("---")
    st.subheader("Visual Analytics")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Expenses by Category**")
        exp_df = filtered_df[filtered_df['Amount'] < 0].copy()
        if not exp_df.empty:
            exp_df['Amount'] = exp_df['Amount'].abs()
            cat_totals = exp_df.groupby('Category')['Amount'].sum().reset_index()
            fig_pie = px.pie(cat_totals, values='Amount', names='Category', hole=0.4, 
                             color_discrete_sequence=px.colors.sequential.Teal)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expenses in this period.")
            
    with chart_col2:
        st.markdown("**Cash Flow Trend**")
        # Aggregate by day
        trend_df = filtered_df.copy()
        trend_df['Type'] = trend_df['Amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
        trend_df['Amount'] = trend_df['Amount'].abs()
        
        daily_trend = trend_df.groupby(['Date', 'Type'])['Amount'].sum().reset_index()
        
        fig_bar = px.bar(daily_trend, x='Date', y='Amount', color='Type', 
                         color_discrete_map={'Income': '#0F4C5C', 'Expense': '#EE9B00'},
                         barmode='group')
        fig_bar.update_layout(yaxis_title="Amount (₹)")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    # 4. AI Financial Analysis
    st.markdown("---")
    st.subheader("🤖 AI Financial Analysis")
    
    if st.button("Generate AI Insights for this Period", type="primary"):
        with st.spinner("Analyzing your spending patterns..."):
            # Prepare summary for AI
            report_summary = {
                "period": f"{start_date} to {end_date}",
                "total_income": income,
                "total_expenses": expenses,
                "net_cash_flow": net,
                "top_categories": filtered_df[filtered_df['Amount'] < 0].groupby('Category')['Amount'].sum().abs().sort_values(ascending=False).head(3).to_dict()
            }
            
            # Use the AI router
            analysis = route_ai_task('insights', summary_data=report_summary)
            st.info("### AI Advice")
            st.markdown(analysis)
            
            if income < expenses:
                st.warning("⚠️ **Note:** Your expenses are higher than your income for this period. The AI has provided specific suggestions above to help you balance your budget.")

    # 5. Export & Tools Section
    st.markdown("---")
    col_tools1, col_tools2 = st.columns([2, 1])
    
    with col_tools1:
        st.subheader("Export Data")
        st.caption(f"Exporting {len(filtered_df)} transactions from {start_date} to {end_date}.")
    
    with col_tools2:
        # Tool to invert signs if needed
        invert_signs = st.toggle("🔄 Invert Signs", help="Toggle this if your bank uses positive numbers for expenses and negative for income.")
        if invert_signs:
            filtered_df['Amount'] = -filtered_df['Amount']
            # Re-calculate metrics for the export and preview if inverted
            income = filtered_df[filtered_df['Amount'] > 0]['Amount'].sum()
            expenses = abs(filtered_df[filtered_df['Amount'] < 0]['Amount'].sum())
            net = income - expenses

    export_df = filtered_df.drop(columns=['_id'])
    
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    
    # CSV
    csv_data = export_df.to_csv(index=False).encode('utf-8')
    dl_col1.download_button(
        label="📄 Download CSV",
        data=csv_data,
        file_name=f"finsight_export_{start_date}_to_{end_date}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # Excel
    excel_buffer = generate_excel_report(export_df)
    dl_col2.download_button(
        label="📊 Download Excel",
        data=excel_buffer,
        file_name=f"finsight_export_{start_date}_to_{end_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    # PDF
    summary_dict = {'income': income, 'expenses': expenses, 'net': net}
    # Pass python datetime or date to the pdf generator
    pdf_buffer = generate_pdf_report(export_df, summary_dict, start_date, end_date)
    dl_col3.download_button(
        label="📉 Download PDF Report",
        data=pdf_buffer,
        file_name=f"finsight_report_{start_date}_to_{end_date}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    # Data Preview
    st.markdown("---")
    st.subheader("Data Preview")
    st.dataframe(export_df, use_container_width=True, hide_index=True)