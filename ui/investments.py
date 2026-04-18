import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from core.db import Investment
from ai.router import route_ai_task

@st.cache_data(ttl=900) # Cache for 15 minutes
def get_current_price(ticker):
    """Fetch current price for a ticker using yfinance with caching."""
    if not ticker:
        return 0.0
    try:
        data = yf.Ticker(ticker)
        # Fetch 1 day of data
        hist = data.history(period="1d")
        if not hist.empty:
            price = hist["Close"].iloc[-1]
            return float(price)
        return 0.0
    except Exception:
        return 0.0

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_nifty_50_list():
    """Return a curated list of Nifty 50 tickers."""
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
        "BHARTIARTL.NS", "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "LTIM.NS",
        "KOTAKBANK.NS", "AXISBANK.NS", "LT.NS", "BAJFINANCE.NS", "MARUTI.NS",
        "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS", "TATASTEEL.NS", "M&M.NS",
        "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS", "ASIANPAINT.NS", "HCLTECH.NS",
        "BAJAJFINSV.NS", "INDUSINDBK.NS", "NESTLEIND.NS", "JSWSTEEL.NS", "GRASIM.NS",
        "ADANIPORTS.NS", "HINDALCO.NS", "ONGC.NS", "COALINDIA.NS", "SBILIFE.NS",
        "BRITANNIA.NS", "TATACONSUM.NS", "DRREDDY.NS", "WIPRO.NS", "HDFCLIFE.NS",
        "EICHERMOT.NS", "CIPLA.NS", "BAJAJ-AUTO.NS", "APOLLOHOSP.NS", "HEROMOTOCO.NS",
        "DIVISLAB.NS", "BPCL.NS", "TATAMOTORS.NS"
    ]

@st.cache_data(ttl=900)
def get_market_data(tickers):
    """Fetch basic market data for a list of tickers."""
    market_data = []
    for ticker in tickers[:15]: # Limit to top 15 for performance
        try:
            t = yf.Ticker(ticker)
            info = t.history(period="2d")
            if len(info) >= 2:
                curr = info['Close'].iloc[-1]
                prev = info['Close'].iloc[-2]
                change = curr - prev
                change_pct = (change / prev) * 100
                market_data.append({
                    "Ticker": ticker,
                    "Price": curr,
                    "Change %": change_pct
                })
        except:
            continue
    return market_data

def show_investments():
    st.title("📈 Investment Portfolio")
    
    # 1. Add Investment Form
    with st.expander("➕ Add New Investment", expanded=True):
        col_t, col_p = st.columns([3, 1])
        with col_t:
            ticker_input = st.text_input("Enter Ticker Symbol (e.g. AAPL, RELIANCE.NS)", key="new_ticker_input")
        with col_p:
            fetch_btn = st.button("🔍 Get Price", use_container_width=True)
            
        # Handle price fetching
        current_market_price = 0.0
        if ticker_input or fetch_btn:
            with st.spinner("Syncing price..."):
                current_market_price = get_current_price(ticker_input.upper().strip())
                if current_market_price > 0:
                    st.toast(f"Current price for {ticker_input.upper()}: ₹{current_market_price:.2f}")

        with st.form("add_investment_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                quantity = st.number_input("Quantity", min_value=1.0, value=10.0, step=1.0)
            with col2:
                # Default to the fetched price or 0.0
                purchase_price = st.number_input("Purchase Price (₹)", min_value=0.0, value=current_market_price, step=0.01)
                purchase_date = st.date_input("Purchase Date", value=datetime.now())
                
            if st.form_submit_button("Confirm & Add to Portfolio"):
                if ticker_input and quantity >= 1:
                    final_price = purchase_price if purchase_price > 0 else current_market_price
                    Investment.create(
                        ticker=ticker_input.upper().strip(),
                        quantity=quantity,
                        purchase_price=final_price,
                        purchase_date=purchase_date
                    )
                    st.success(f"Added {quantity} shares of {ticker_input.upper()} at ₹{final_price:.2f}!")
                    st.rerun()
                else:
                    st.error("Please enter a valid ticker and quantity (min 1).")

    # 2. Portfolio Table
    investments = Investment.find_all()

    if not investments:
        # ---- DUMMY / PREVIEW MODE ----
        from ui.dummy_data import DUMMY_INVESTMENTS

        st.info(
            "📈 **Sample Preview** — Below is an example portfolio with real-time prices. "
            "Add your own holdings using the form above.",
            icon="🔍",
        )

        dummy_list = []
        with st.spinner("Fetching live prices for sample portfolio..."):
            for inv in DUMMY_INVESTMENTS:
                curr_price = get_current_price(inv["ticker"])
                if curr_price == 0.0:
                    curr_price = inv["purchase_price"] * 1.08  # fallback +8%
                qty = inv["quantity"]
                avg_cost = inv["purchase_price"]
                market_value = qty * curr_price
                cost_basis = qty * avg_cost
                pl = market_value - cost_basis
                pl_pct = (pl / cost_basis * 100) if cost_basis > 0 else 0
                dummy_list.append({
                    "Ticker": inv["ticker"],
                    "Quantity": qty,
                    "Avg Cost": avg_cost,
                    "Curr Price": curr_price,
                    "Market Value": market_value,
                    "P/L": pl,
                    "P/L %": pl_pct,
                })

        dummy_df = pd.DataFrame(dummy_list)
        total_value = dummy_df["Market Value"].sum()
        total_cost = (dummy_df["Quantity"] * dummy_df["Avg Cost"]).sum()
        total_pl = total_value - total_cost
        total_pl_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Portfolio Value (Sample)", f"₹{total_value:,.2f}")
        m2.metric("Total P/L (Sample)", f"₹{total_pl:,.2f}", delta=f"{total_pl_pct:.2f}%")
        m3.metric("Holdings (Sample)", f"{len(dummy_df)} Stocks")

        st.dataframe(
            dummy_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Avg Cost":      st.column_config.NumberColumn("Avg Cost",      format="₹%.2f"),
                "Curr Price":    st.column_config.NumberColumn("Curr Price",    format="₹%.2f"),
                "Market Value":  st.column_config.NumberColumn("Market Value",  format="₹%.2f"),
                "P/L":           st.column_config.NumberColumn("P/L",           format="₹%.2f"),
                "P/L %":         st.column_config.NumberColumn("P/L %",         format="%.2f%%"),
            },
        )
    else:
        # Process investments for display
        portfolio_list = []
        with st.spinner("Fetching real-time market data..."):
            for inv in investments:
                curr_price = get_current_price(inv['ticker'])
                avg_cost = inv['purchase_price']
                qty = inv['quantity']
                
                market_value = qty * curr_price
                cost_basis = qty * avg_cost
                pl = market_value - cost_basis
                pl_pct = (pl / cost_basis * 100) if cost_basis > 0 else 0
                
                portfolio_list.append({
                    "id": str(inv.get('_id', '')),
                    "Ticker": inv['ticker'],
                    "Quantity": qty,
                    "Avg Cost": avg_cost,
                    "Curr Price": curr_price,
                    "Market Value": market_value,
                    "P/L": pl,
                    "P/L %": pl_pct
                })

        df = pd.DataFrame(portfolio_list)
        
        # 3. Summary Metrics
        total_value = df['Market Value'].sum()
        total_cost = (df['Quantity'] * df['Avg Cost']).sum()
        total_pl = total_value - total_cost
        total_pl_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Portfolio Value", f"₹{total_value:,.2f}")
        m2.metric("Total Profit/Loss", f"₹{total_pl:,.2f}", delta=f"{total_pl_pct:.2f}%")
        m3.metric("Holdings", f"{len(df)} Stocks")

        st.markdown("---")
        
        # 4. Interactive Table
        st.subheader("Your Holdings")
        
        def save_changes():
            changes = st.session_state.get("portfolio_editor", {})
            for row_idx in changes.get("deleted_rows", []):
                inv_id = df.iloc[row_idx]['id']
                Investment.delete(inv_id)
                st.toast("Holding removed.", icon="🗑️")
                
        st.data_editor(
            df.drop(columns=['id']),
            column_config={
                "Avg Cost": st.column_config.NumberColumn("Avg Cost", format="₹%.2f"),
                "Curr Price": st.column_config.NumberColumn("Curr Price", format="₹%.2f"),
                "Market Value": st.column_config.NumberColumn("Market Value", format="₹%.2f"),
                "P/L": st.column_config.NumberColumn("P/L", format="₹%.2f"),
                "P/L %": st.column_config.NumberColumn("P/L %", format="%.2f%%"),
            },
            use_container_width=True,
            hide_index=True,
            key="portfolio_editor",
            on_change=save_changes,
            num_rows="dynamic"
        )

        st.markdown("---")

    # 5. AI Advisor Section
    st.subheader("🤖 AI Investment Advisor")
    if st.button("Consult AI Advisor", type="primary"):
        # Format data for AI
        ai_data = []
        for _, row in df.iterrows():
            ai_data.append({
                'ticker': row['Ticker'],
                'quantity': row['Quantity'],
                'avg_cost': row['Avg Cost'],
                'current_price': row['Curr Price'],
                'pl': row['P/L']
            })
            
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("### AI Advisor Report")
            advice_stream = route_ai_task('invest_advice', portfolio_data=ai_data, stream=True)
            st.write_stream(advice_stream)

    st.markdown("---")
    
    # 6. Market Explorer
    st.subheader("🌐 Nifty 50 Market Explorer")
    st.caption("Top companies in the Nifty 50 index. Add them to your portfolio to track them.")
    
    nifty_tickers = get_nifty_50_list()
    market_df = pd.DataFrame(get_market_data(nifty_tickers))
    
    if not market_df.empty:
        cols = st.columns(3)
        for i, (_, row) in enumerate(market_df.iterrows()):
            with cols[i % 3]:
                with st.container(border=True):
                    st.write(f"**{row['Ticker']}**")
                    color = "green" if row['Change %'] >= 0 else "red"
                    st.write(f"₹{row['Price']:.2f} (:{color}[{row['Change %']:.2f}%])")
                    
                    if st.button(f"Add {row['Ticker']}", key=f"add_nifty_{row['Ticker']}"):
                        Investment.create(
                            ticker=row['Ticker'],
                            quantity=1,
                            purchase_price=row['Price'],
                            purchase_date=datetime.now()
                        )
                        st.success(f"Added 1 unit of {row['Ticker']} at ₹{row['Price']:.2f}")
                        st.rerun()
    else:
        st.info("Unable to load market data. Check your internet connection.")