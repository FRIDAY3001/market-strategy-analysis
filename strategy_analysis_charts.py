import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

# Load data
df = pd.read_csv("HT_InputFile for Quadratic(Trade_Ref)_Refined.csv")
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Trigger Time'] = pd.to_datetime(df['Trigger Time'], errors='coerce')
df['Buy/Sell'] = df['Buy/Sell'].str.strip().str.capitalize()

# Split Buy/Sell
buy = df[df['Buy/Sell'] == 'Buy'].copy()
sell = df[df['Buy/Sell'] == 'Sell'].copy()

# Rename
buy = buy.rename(columns={
    'Trade Price': 'Trade Price_buy', 'Qty': 'Qty_buy', 'Brokerage': 'Brokerage_buy',
    'Other_Charges': 'Other_charges_buy', 'Trigger Time': 'Trigger Time_buy',
    'Date': 'Date_buy', 'Symbol': 'Symbol_buy'
})
sell = sell.rename(columns={
    'Trade Price': 'Trade Price_sell', 'Qty': 'Qty_sell', 'Brokerage': 'Brokerage_sell',
    'Other_Charges': 'Other_charges_sell', 'Trigger Time': 'Trigger Time_sell',
    'Date': 'Date_sell', 'Symbol': 'Symbol_sell'
})

# Merge
trades = pd.merge(buy, sell, on='Trade_Ref')

# Metrics
trades['Entry_Price'] = trades['Trade Price_buy']
trades['Exit_Price'] = trades['Trade Price_sell']
trades['Quantity'] = trades['Qty_buy']
trades['Symbol'] = trades['Symbol_buy']
trades['Gross_PnL'] = (trades['Exit_Price'] - trades['Entry_Price']) * trades['Quantity']
trades['Total_Brokerage'] = trades['Brokerage_buy'] + trades['Brokerage_sell']
trades['Total_Other_Charges'] = trades['Other_charges_buy'] + trades['Other_charges_sell']
trades['Net_PnL'] = trades['Gross_PnL'] + trades['Total_Brokerage'] + trades['Total_Other_Charges']
trades['Capital_Used'] = trades['Entry_Price'] * trades['Quantity']
trades['Trade_Duration_Minutes'] = (trades['Trigger Time_sell'] - trades['Trigger Time_buy']).dt.total_seconds() / 60
trades['Return_Pct'] = (trades['Net_PnL'] / trades['Capital_Used']) * 100
trades['Date_Only'] = trades['Date_buy'].dt.date
trades['Entry_Hour'] = trades['Trigger Time_buy'].dt.hour
trades['Base_Symbol'] = trades['Symbol'].str.extract(r'^([A-Z]+)')
trades['Day_of_Week'] = trades['Date_buy'].dt.day_name()

# Cumulative PnL and Drawdown
trades = trades.sort_values('Date_buy')
trades['Cumulative_PnL'] = trades['Net_PnL'].cumsum()
trades['Running_Max'] = trades['Cumulative_PnL'].cummax()
trades['Drawdown'] = trades['Cumulative_PnL'] - trades['Running_Max']

# Capital table
capital = trades[['Date_buy', 'Capital_Used', 'Net_PnL']].copy()
capital['Cumulative_Capital'] = capital['Capital_Used'].cumsum()
capital['Capital_Efficiency'] = capital['Net_PnL'] / capital['Capital_Used']

# Hourly table
hourly = trades.groupby('Entry_Hour').agg(
    Total_Trades=('Net_PnL', 'count'),
    Total_PnL=('Net_PnL', 'sum'),
    Avg_PnL_per_Trade=('Net_PnL', 'mean'),
    Capital_Used=('Capital_Used', 'sum'),
    Win_Rate_Pct=('Net_PnL', lambda x: (x > 0).mean() * 100)
).reset_index()

# === PLOTLY CHART EXPORTS ===

# 1. Equity Curve
fig_eq = go.Figure()
fig_eq.add_trace(go.Scatter(
    x=trades['Date_buy'],
    y=trades['Cumulative_PnL'],
    mode='lines+markers',
    name='Equity Curve',
    line=dict(color='green')
))
fig_eq.update_layout(title='Equity Curve (Cumulative PnL)', xaxis_title='Date', yaxis_title='Cumulative PnL')
with open("equity_curve.html", "w", encoding="utf-8") as f:
    f.write(fig_eq.to_html(full_html=True))

# 2. Drawdown Curve
fig_dd = go.Figure()
fig_dd.add_trace(go.Scatter(
    x=trades['Date_buy'],
    y=trades['Drawdown'],
    mode='lines+markers',
    name='Drawdown',
    line=dict(color='red')
))
fig_dd.update_layout(title='Drawdown Over Time', xaxis_title='Date', yaxis_title='Drawdown')
with open("drawdown.html", "w", encoding="utf-8") as f:
    f.write(fig_dd.to_html(full_html=True))

# 3. Hourly PnL
fig_hourly = go.Figure()
fig_hourly.add_trace(go.Bar(
    x=hourly['Entry_Hour'],
    y=hourly['Total_PnL'],
    name='Hourly PnL',
    marker_color='blue'
))
fig_hourly.update_layout(title='Hourly PnL', xaxis_title='Hour', yaxis_title='Total PnL')
with open("hourly_pnl.html", "w", encoding="utf-8") as f:
    f.write(fig_hourly.to_html(full_html=True))

# 4. Capital Used
fig_cap = go.Figure()
fig_cap.add_trace(go.Scatter(
    x=capital['Date_buy'],
    y=capital['Capital_Used'],
    mode='lines+markers',
    name='Capital Used',
    line=dict(color='orange')
))
fig_cap.update_layout(title='Capital Utilisation Over Time', xaxis_title='Date', yaxis_title='Capital Used')
with open("capital_utilisation.html", "w", encoding="utf-8") as f:
    f.write(fig_cap.to_html(full_html=True))

print("✅ Charts saved as HTML files.")
print("➡️ Open these files in your browser manually:")
print("   - equity_curve.html")
print("   - drawdown.html")
print("   - hourly_pnl.html")
print("   - capital_utilisation.html")
