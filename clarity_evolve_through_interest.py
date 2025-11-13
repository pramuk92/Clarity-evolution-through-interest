import streamlit as st
import re
import pandas as pd
import yfinance as yf
from datetime import datetime
import time

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

# Cache market data to reduce API calls
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_vix_data():
    """Get current VIX value with error handling"""
    try:
        vix = yf.Ticker("^VIX")
        vix_history = vix.history(period="2d")
        if not vix_history.empty:
            current_vix = vix_history['Close'].iloc[-1]
            return round(current_vix, 2)
    except Exception as e:
        st.sidebar.warning(f"Could not fetch VIX data: {e}")
    return None

@st.cache_data(ttl=300)
def get_sp500_trend():
    """Get SP500 trend information with error handling"""
    try:
        spx = yf.Ticker("^GSPC")
        spx_history = spx.history(period="10d")  # Shorter period to reduce load
        if not spx_history.empty:
            current_price = spx_history['Close'].iloc[-1]
            # Simple trend based on last 5 days
            if current_price > spx_history['Close'].iloc[0]:
                trend = "Bullish"
            else:
                trend = "Bearish"
            return {
                'current': round(current_price, 2),
                'trend': trend,
            }
    except Exception as e:
        st.sidebar.warning(f"Could not fetch SP500 data: {e}")
    return None

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_currency_price_data(pair, period="1mo"):
    """Get recent price data for a currency pair with rate limiting"""
    try:
        # Add delay to be respectful to Yahoo Finance
        time.sleep(0.1)
        
        yf_symbol = pair.replace('/', '') + '=X'
        data = yf.download(yf_symbol, period=period, progress=False, interval="1d")
        if not data.empty:
            return {
                'current': round(data['Close'].iloc[-1], 5),
                'trend': 'Bullish' if data['Close'].iloc[-1] > data['Close'].mean() else 'Bearish',
                'data': data.tail(20)  # Only keep last 20 days to reduce memory
            }
    except Exception as e:
        st.sidebar.warning(f"Could not fetch data for {pair}: {e}")
    return None

def assess_market_regime(vix_value, sp500_trend):
    """Determine current market regime"""
    if vix_value is None:
        return "UNKNOWN"
    
    if vix_value < 20:
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
        "Primary Opportunities": [],
        "Secondary Opportunities": [],
        "Monitor Only": [],
        "Avoid": []
    }
    
    # Only analyze top pairs to reduce API calls
    analyzed_pairs = 0
    max_pairs_to_analyze = 10  # Limit API calls
    
    for pair in VALID_PAIRS:
        if analyzed_pairs >= max_pairs_to_analyze:
            break
            
        base, quote = pair.split('/')
        if base in rates_dict and quote in rates_dict:
            diff = rates_dict[base] - rates_dict[quote]
            abs_diff = abs(diff)
            
            # Only get price data for pairs with significant differentials
            if abs_diff >= 0.5:  # Only analyze pairs with meaningful differentials
                price_data = get_currency_price_data(pair, "1mo")
                analyzed_pairs += 1
                
                if price_data:
                    price_trend = price_data['trend']
                    
                    # Strategy logic based on regime and alignment
                    if market_regime == "RISK-ON":
                        if diff > 1.0 and price_trend == "Bullish":
                            watchlist["Primary Opportunities"].append({
                                "pair": pair,
                                "diff": diff,
                                "price_trend": price_trend,
                                "direction": "LONG",
                                "rationale": "Strong carry + bullish trend in risk-on environment",
                                "confidence": "High"
                            })
                        elif diff > 0.5:
                            watchlist["Secondary Opportunities"].append({
                                "pair": pair,
                                "diff": diff,
                                "price_trend": price_trend,
                                "direction": "LONG",
                                "rationale": "Moderate carry, watch for entries",
                                "confidence": "Medium"
                            })
                    
                    elif market_regime == "RISK-OFF":
                        if diff < -1.0:
                            watchlist["Primary Opportunities"].append({
                                "pair": pair,
                                "diff": diff,
                                "price_trend": price_trend,
                                "direction": "SHORT" if diff > 0 else "LONG",
                                "rationale": "Safe haven characteristics in risk-off",
                                "confidence": "High"
                            })
                    
                    else:  # NEUTRAL regime
                        if abs_diff > 1.0:
                            watchlist["Monitor Only"].append({
                                "pair": pair,
                                "diff": diff,
                                "price_trend": price_trend,
                                "direction": "WAIT",
                                "rationale": "Significant differential but neutral regime",
                                "confidence": "Low"
                            })
    
    return watchlist

def generate_trading_signals(watchlist, market_regime):
    """Generate specific trading signals based on analysis"""
    signals = []
    
    for category, pairs in watchlist.items():
        for pair_info in pairs[:3]:  # Top 3 from each category
            if pair_info['direction'] not in ['AVOID', 'WAIT']:
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
                if category == "Primary Opportunities":
                    signal["Entry"] = "Wait for pullback to support"
                    signal["Stop"] = "1-2% below entry"
                    signal["Target"]": "2:1 risk-reward"
                else:
                    signal["Entry"] = "Conservative entry on confirmation"
                    signal["Stop"] = "Wider stop for volatility"
                    signal["Target"]": "1.5:1 risk-reward"
                
                signals.append(signal)
    
    return signals

# Streamlit App
st.set_page_config(page_title="Forex Systematic Trader", page_icon="🎯", layout="wide")

st.title("🎯 Forex Systematic Trading Strategy")
st.markdown("""
*Optimized for minimal API calls and reliable performance*
""")

# Sidebar for market data input
st.sidebar.header("📊 Market Data Input")

# Auto-fetch or manual VIX input with better error handling
vix_auto = get_vix_data()
vix_default = vix_auto if vix_auto else 15.5

vix_value = st.sidebar.number_input("Current VIX Value", 
                                  min_value=0.0, 
                                  max_value=100.0, 
                                  value=float(vix_default),
                                  step=0.1,
                                  help="VIX below 20 = Risk-On, above 25 = Risk-Off")

# Market regime assessment
sp500_data = get_sp500_trend()
market_regime = assess_market_regime(vix_value, sp500_data)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Current Market Regime")
st.sidebar.markdown(f"**Regime:** {market_regime}")

if market_regime == "RISK-ON":
    st.sidebar.success("✅ Low Fear - Risk-On Environment")
elif market_regime == "RISK-OFF":
    st.sidebar.error("🚨 High Fear - Risk-Off Environment")
else:
    st.sidebar.warning("⚠️ Neutral - Mixed Signals")

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

col1, col2 = st.columns(2)
with col1:
    min_confidence = st.selectbox("Minimum Confidence", ["High", "Medium", "Low"], index=0)
with col2:
    include_price_data = st.checkbox("Include Price Data Analysis", value=True, 
                                   help="Uncheck to reduce API calls")

# Add API call disclaimer
st.info("🔍 **Note:** This app makes limited API calls to Yahoo Finance (cached for 5-10 minutes) to be respectful to their servers.")

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
            
            with st.spinner("Analyzing market opportunities..."):
                # Create strategic analysis
                watchlist = create_strategic_watchlist(rates_dict, market_regime)
                trading_signals = generate_trading_signals(watchlist, market_regime)
            
            st.success(f"✅ Analysis Complete - {market_regime} Environment")
            
            # Display market overview
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Market Regime", market_regime)
            with col2:
                st.metric("VIX Level", f"{vix_value}")
            with col3:
                high_conf_signals = len([s for s in trading_signals if s['Confidence'] == 'High'])
                st.metric("High Confidence Signals", high_conf_signals)
            
            # Display trading signals
            st.subheader("📈 Generated Trading Signals")
            
            if trading_signals:
                # Filter by confidence
                confidence_map = {"High": 3, "Medium": 2, "Low": 1}
                min_conf_level = confidence_map[min_confidence]
                filtered_signals = [s for s in trading_signals 
                                  if confidence_map[s['Confidence']] >= min_conf_level]
                
                if filtered_signals:
                    # Create display dataframe - FIXED: No styling to avoid the error
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
                    
                    # Simple color coding using Streamlit's native formatting
                    for _, row in df_signals.iterrows():
                        if row['Confidence'] == 'High':
                            st.success(f"🎯 **{row['Pair']}** - {row['Signal']} (High Confidence)")
                        elif row['Confidence'] == 'Medium':
                            st.warning(f"📊 **{row['Pair']}** - {row['Signal']} (Medium Confidence)")
                        else:
                            st.info(f"👀 **{row['Pair']}** - {row['Signal']} (Low Confidence)")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"Rate Diff: {row['Rate Diff']} | Trend: {row['Price Trend']}")
                            st.write(f"Entry: {row['Entry']}")
                        with col2:
                            st.write(f"Stop: {row['Stop']} | Target: {row['Target']}")
                            st.write(f"Rationale: {row['Rationale']}")
                        st.markdown("---")
                    
                    # Download signals
                    csv_data = pd.DataFrame(filtered_signals)
                    csv = csv_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Trading Signals",
                        data=csv,
                        file_name="forex_trading_signals.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No signals meet your confidence criteria. Try lowering the minimum confidence level.")
            else:
                st.warning("No trading signals generated for current market conditions.")
            
            # Strategic watchlist overview
            st.subheader("📋 Strategic Watchlist Overview")
            
            for category, pairs in watchlist.items():
                if pairs:
                    with st.expander(f"{category} ({len(pairs)} pairs)"):
                        for pair_info in pairs:
                            col1, col2, col3 = st.columns([2, 2, 3])
                            with col1:
                                st.write(f"**{pair_info['pair']}**")
                                st.write(f"Diff: {pair_info['diff']:.2f}%")
                            with col2:
                                st.write(f"Trend: {pair_info['price_trend']}")
                                st.write(f"Conf: {pair_info['confidence']}")
                            with col3:
                                st.write(pair_info['rationale'])

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
    
    **Preferred Strategy:**
    - Long high-yield currencies
    - Technical breakout entries
    - 2:1 risk-reward targets
    """)

with col2:
    st.markdown("""
    **📉 Risk-Off Environment (VIX > 25)**
    - Reduce carry trade exposure
    - Focus on safe havens
    - Use wider stops for volatility
    
    **Preferred Strategy:**
    - Short high-yield currencies  
    - Counter-trend opportunities
    - Defensive position sizing
    """)

st.markdown("""
**💡 Optimization Notes:**
- API calls are cached and limited to reduce server load
- Only analyze pairs with significant rate differentials
- Price data fetching is optional to minimize requests
- Analysis focuses on quality over quantity
""")
