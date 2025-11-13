import streamlit as st
import re
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# Mapping central banks to currency codes
bank_to_currency = {
    "Federal Reserve": "USD",
    "European Central Bank": "EUR", 
    "Bank of England": "GBP",
    "Reserve Bank of Australia": "AUD",
    "Reserve Bank of New Zealand": "NZD",
    "Bank of Japan": "JPY",
    "Bank of Canada": "CAD",
    "Swiss National Bank": "CHF"
}

# Define valid forex pairs
VALID_PAIRS = [
    'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD', 'NZD/USD',
    'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/AUD', 'EUR/CAD', 'EUR/NZD',
    'GBP/JPY', 'GBP/CHF', 'GBP/AUD', 'GBP/CAD', 'GBP/NZD',
    'AUD/JPY', 'CAD/JPY', 'CHF/JPY', 'NZD/JPY',
    'AUD/CAD', 'AUD/CHF', 'AUD/NZD',
    'CAD/CHF', 'NZD/CAD', 'NZD/CHF'
]

# Market data functions
def get_vix_data():
    """Get current VIX value"""
    try:
        vix = yf.Ticker("^VIX")
        vix_history = vix.history(period="5d")
        current_vix = vix_history['Close'].iloc[-1]
        return round(current_vix, 2)
    except:
        return None

def get_sp500_trend():
    """Get SP500 trend information"""
    try:
        spx = yf.Ticker("^GSPC")
        spx_history = spx.history(period="30d")
        current_price = spx_history['Close'].iloc[-1]
        ma_200 = spx_history['Close'].mean()  # Simplified 200MA
        trend = "Bullish" if current_price > ma_200 else "Bearish"
        return {
            'current': round(current_price, 2),
            'trend': trend,
            'above_200ma': current_price > ma_200
        }
    except:
        return None

def get_currency_price_data(pair, period="1mo"):
    """Get recent price data for a currency pair"""
    try:
        # Convert forex pair to yfinance format (remove slash)
        yf_symbol = pair.replace('/', '') + '=X'
        data = yf.download(yf_symbol, period=period, progress=False)
        if not data.empty:
            return {
                'current': round(data['Close'].iloc[-1], 5),
                'trend': 'Bullish' if data['Close'].iloc[-1] > data['Close'].iloc[0] else 'Bearish',
                'data': data
            }
        return None
    except:
        return None

def assess_market_regime(vix_value, sp500_trend):
    """Determine current market regime"""
    if vix_value is None or sp500_trend is None:
        return "Unknown"
    
    if vix_value < 20 and sp500_trend['above_200ma']:
        return "RISK-ON"
    elif vix_value > 25:
        return "RISK-OFF"
    else:
        return "NEUTRAL"

# Strategic analysis functions
def create_strategic_watchlist(rates_dict, market_regime):
    """
    Create categorized watchlist based on rates and market regime
    """
    watchlist = {
        "Primary Carry Trades": [],
        "Counter-Trend Opportunities": [],
        "Range Trading Candidates": [],
        "Avoid - High Risk": []
    }
    
    for pair in VALID_PAIRS:
        base, quote = pair.split('/')
        if base in rates_dict and quote in rates_dict:
            diff = rates_dict[base] - rates_dict[quote]
            abs_diff = abs(diff)
            
            # Get price trend
            price_data = get_currency_price_data(pair, "1mo")
            price_trend = price_data['trend'] if price_data else "Unknown"
            
            if market_regime == "RISK-ON":
                if diff > 1.0 and price_trend == "Bullish":
                    watchlist["Primary Carry Trades"].append({
                        "pair": pair,
                        "diff": diff,
                        "price_trend": price_trend,
                        "direction": "LONG",
                        "rationale": "Strong carry + bullish trend alignment",
                        "confidence": "High"
                    })
                elif diff < -1.0 and price_trend == "Bearish":
                    watchlist["Counter-Trend Opportunities"].append({
                        "pair": pair,
                        "diff": diff,
                        "price_trend": price_trend,
                        "direction": "SHORT",
                        "rationale": "Negative carry + bearish trend",
                        "confidence": "Medium"
                    })
                    
            elif market_regime == "RISK-OFF":
                if diff < -1.0 and price_trend == "Bullish":
                    watchlist["Counter-Trend Opportunities"].append({
                        "pair": pair,
                        "diff": diff,
                        "price_trend": price_trend,
                        "direction": "LONG",
                        "rationale": "Safe haven + bullish reversal potential",
                        "confidence": "Medium"
                    })
                elif diff > 2.0:
                    watchlist["Avoid - High Risk"].append({
                        "pair": pair,
                        "diff": diff,
                        "price_trend": price_trend,
                        "direction": "AVOID",
                        "rationale": "High carry trade unwinding risk",
                        "confidence": "Low"
                    })
            
            # Range trading candidates (small differentials)
            if abs_diff < 0.5:
                watchlist["Range Trading Candidates"].append({
                    "pair": pair,
                    "diff": diff,
                    "price_trend": price_trend,
                    "direction": "RANGE",
                    "rationale": "Low carry influence, technical trading",
                    "confidence": "Medium"
                })
    
    # Sort by confidence and differential
    for category in watchlist:
        watchlist[category].sort(key=lambda x: (x['confidence'] == 'High', abs(x['diff'])), reverse=True)
    
    return watchlist

def generate_trading_signals(watchlist, market_regime):
    """Generate specific trading signals based on analysis"""
    signals = []
    
    for category, pairs in watchlist.items():
        for pair_info in pairs[:3]:  # Top 3 from each category
            if pair_info['direction'] != 'AVOID':
                signal = {
                    "Pair": pair_info['pair'],
                    "Signal": pair_info['direction'],
                    "Category": category,
                    "Rate Diff": f"{pair_info['diff']:.2f}%",
                    "Price Trend": pair_info['price_trend'],
                    "Confidence": pair_info['confidence'],
                    "Rationale": pair_info['rationale']
                }
                
                # Add specific entry recommendations
                if category == "Primary Carry Trades":
                    signal["Entry"] = "Buy pullback to 20-day EMA"
                    signal["Stop"] = "Below recent swing low"
                    signal["Target"] = "Previous resistance + 2R"
                elif category == "Counter-Trend Opportunities":
                    signal["Entry"] = "Break of key level with volume"
                    signal["Stop"] = "Beyond consolidation range"
                    signal["Target"] = "Measured move + 1.5R"
                else:
                    signal["Entry"] = "Range boundaries with reversal confirmation"
                    signal["Stop"] = "Beyond range extremes"
                    signal["Target"] = "Opposite range boundary"
                
                signals.append(signal)
    
    return signals

# Streamlit App
st.set_page_config(page_title="Forex Systematic Trader", page_icon="🎯", layout="wide")

st.title("🎯 Forex Systematic Trading Strategy")
st.markdown("""
Advanced forex trading system combining interest rate differentials, market regime analysis, 
and price action for systematic trade identification.
""")

# Sidebar for market data input
st.sidebar.header("📊 Market Data Input")

# Auto-fetch or manual VIX input
vix_auto = get_vix_data()
if vix_auto:
    vix_value = st.sidebar.number_input("Current VIX Value", 
                                      min_value=0.0, 
                                      max_value=100.0, 
                                      value=float(vix_auto),
                                      step=0.1,
                                      help="Current VIX fear index value")
else:
    vix_value = st.sidebar.number_input("Current VIX Value", 
                                      min_value=0.0, 
                                      max_value=100.0, 
                                      value=15.5,
                                      step=0.1)

# Market regime assessment
sp500_data = get_sp500_trend()
market_regime = assess_market_regime(vix_value, sp500_data)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Current Market Regime")
st.sidebar.markdown(f"**Regime:** {market_regime}")
if vix_value < 20:
    st.sidebar.success("Low Fear - Risk-On Environment")
elif vix_value > 25:
    st.sidebar.error("High Fear - Risk-Off Environment")
else:
    st.sidebar.warning("Neutral - Mixed Signals")

if sp500_data:
    st.sidebar.markdown(f"**SP500 Trend:** {sp500_data['trend']}")

# Main input area
st.subheader("💹 Interest Rate Data Input")

with st.expander("📋 Sample Input Format (Click to expand)"):
    st.code("""Federal Reserve 5.50%
European Central Bank 4.50%
Bank of England 5.25%
Reserve Bank of Australia 4.35%
Reserve Bank of New Zealand 5.50%
Bank of Japan 0.10%
Bank of Canada 5.00%
Swiss National Bank 1.75%""")

raw_input = st.text_area("Paste Interest Rate Table Here", height=150, placeholder="Paste the interest rate table here...")

# Strategy options
st.subheader("⚙️ Trading Strategy Options")

col1, col2, col3 = st.columns(3)
with col1:
    min_confidence = st.selectbox("Minimum Confidence", ["High", "Medium", "Low"], index=1)
with col2:
    max_signals = st.slider("Max Signals to Show", 5, 20, 10)
with col3:
    include_technical = st.checkbox("Include Technical Analysis", value=True)

if st.button("🎯 Generate Trading Signals", type="primary"):
    if not raw_input.strip():
        st.error("Please paste the interest rate table.")
    else:
        # Process interest rate data
        lines = raw_input.splitlines()
        rate_data = []
        
        for line in lines:
            match = re.match(r"(.+?)\s+([\d.]+)\s*%?", line)
            if match:
                bank, rate = match.groups()
                currency = bank_to_currency.get(bank.strip())
                if currency:
                    rate_data.append((currency, float(rate)))
        
        if not rate_data:
            st.error("No valid interest rate data found.")
        else:
            rates_dict = dict(rate_data)
            
            # Create strategic analysis
            watchlist = create_strategic_watchlist(rates_dict, market_regime)
            trading_signals = generate_trading_signals(watchlist, market_regime)
            
            st.success(f"✅ Analysis Complete - {market_regime} Environment")
            
            # Display market overview
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Market Regime", market_regime)
            with col2:
                st.metric("VIX Level", f"{vix_value}")
            with col3:
                st.metric("Total Signals", len(trading_signals))
            with col4:
                high_conf_signals = len([s for s in trading_signals if s['Confidence'] == 'High'])
                st.metric("High Confidence", high_conf_signals)
            
            # Display trading signals
            st.subheader("📈 Generated Trading Signals")
            
            if trading_signals:
                # Filter by confidence
                confidence_map = {"High": 3, "Medium": 2, "Low": 1}
                min_conf_level = confidence_map[min_confidence]
                filtered_signals = [s for s in trading_signals 
                                  if confidence_map[s['Confidence']] >= min_conf_level]
                filtered_signals = filtered_signals[:max_signals]
                
                # Create display dataframe
                display_data = []
                for signal in filtered_signals:
                    display_data.append({
                        "Pair": signal["Pair"],
                        "Signal": signal["Signal"],
                        "Confidence": signal["Confidence"],
                        "Rate Diff": signal["Rate Diff"],
                        "Price Trend": signal["Price Trend"],
                        "Entry": signal["Entry"],
                        "Stop": signal["Stop"],
                        "Target": signal["Target"],
                        "Rationale": signal["Rationale"]
                    })
                
                df_signals = pd.DataFrame(display_data)
                
                # Color coding for confidence
                def color_confidence(val):
                    if val == 'High': return 'background-color: #90EE90'
                    elif val == 'Medium': return 'background-color: #FFE4B5'
                    else: return 'background-color: #FFB6C1'
                
                styled_df = df_signals.style.applymap(color_confidence, subset=['Confidence'])
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # Detailed analysis for top signals
                st.subheader("🔍 Detailed Analysis - Top Opportunities")
                
                top_signals = [s for s in filtered_signals if s['Confidence'] == 'High'][:3]
                
                for i, signal in enumerate(top_signals):
                    with st.expander(f"📊 {signal['Pair']} - {signal['Signal']} Signal (High Confidence)", expanded=i==0):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Trade Details**")
                            st.write(f"**Signal:** {signal['Signal']}")
                            st.write(f"**Rate Differential:** {signal['Rate Diff']}")
                            st.write(f"**Price Trend:** {signal['Price Trend']}")
                            st.write(f"**Market Regime:** {market_regime}")
                            
                            st.markdown("**Execution Plan**")
                            st.write(f"**Entry:** {signal['Entry']}")
                            st.write(f"**Stop Loss:** {signal['Stop']}")
                            st.write(f"**Profit Target:** {signal['Target']}")
                        
                        with col2:
                            st.markdown("**Risk Management**")
                            st.write("**Position Size:** 1-2% account risk")
                            st.write("**Risk-Reward:** Minimum 1.5:1")
                            st.write("**Timeframe:** Daily bias + 4HR entries")
                            
                            # Get and display price chart
                            price_data = get_currency_price_data(signal['Pair'], "3mo")
                            if price_data and include_technical:
                                st.markdown("**Recent Price Action**")
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=price_data['data'].index,
                                    y=price_data['data']['Close'],
                                    mode='lines',
                                    name=signal['Pair'],
                                    line=dict(color='blue')
                                ))
                                fig.update_layout(
                                    height=200,
                                    margin=dict(l=0, r=0, t=0, b=0),
                                    showlegend=False,
                                    xaxis_title="Date",
                                    yaxis_title="Price"
                                )
                                st.plotly_chart(fig, use_container_width=True)
            
            # Strategic watchlist overview
            st.subheader("📋 Strategic Watchlist Overview")
            
            for category, pairs in watchlist.items():
                if pairs:
                    with st.expander(f"{category} ({len(pairs)} pairs)"):
                        for pair_info in pairs[:5]:  # Show top 5
                            col1, col2, col3 = st.columns([2, 2, 3])
                            with col1:
                                st.write(f"**{pair_info['pair']}**")
                                st.write(f"Diff: {pair_info['diff']:.2f}%")
                            with col2:
                                st.write(f"Trend: {pair_info['price_trend']}")
                                st.write(f"Conf: {pair_info['confidence']}")
                            with col3:
                                st.write(pair_info['rationale'])
            
            # Download signals
            if trading_signals:
                csv_data = pd.DataFrame(trading_signals)
                csv = csv_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download Trading Signals",
                    data=csv,
                    file_name="forex_trading_signals.csv",
                    mime="text/csv"
                )

# Educational section
st.markdown("---")
st.subheader("🎓 Systematic Trading Framework")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **📈 Risk-On Environment (VIX < 20)**
    - Focus on carry trades with bullish trends
    - Buy pullbacks in high differential pairs
    - Use tight risk management
    - Monitor for regime changes
    
    **Preferred Pairs:**
    - AUD/JPY, NZD/JPY, USD/JPY
    - EUR/AUD, GBP/AUD
    - Any pair with rate diff > 1% + bullish trend
    """)

with col2:
    st.markdown("""
    **📉 Risk-Off Environment (VIX > 25)**
    - Reduce carry trade exposure
    - Focus on safe havens and reversals
    - Use wider stops for volatility
    - Prepare for fast moves
    
    **Preferred Pairs:**
    - USD/CHF, USD/JPY (as safe havens)
    - Counter-trend opportunities
    - Range-bound low-differential pairs
    """)

st.markdown("""
**💡 Key Principles:**
1. **Market Regime First** - Always trade with the environment
2. **Rate Differentials** - Use as directional bias, not sole factor  
3. **Price Action Alignment** - Only trade when technicals confirm fundamentals
4. **Risk Management** - 1-2% risk per trade, proper position sizing
5. **Flexibility** - Adapt quickly to changing market conditions
""")
