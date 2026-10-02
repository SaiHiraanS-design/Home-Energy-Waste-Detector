import pandas as pd
import streamlit as st

st.set_page_config(page_title="Home Energy Waste Detector", layout="wide")
st.title("Home Energy Waste Detector")
st.caption("One house, Dec 2006 to Nov 2010. Every figure is a ceiling on avoidable waste, not a guarantee.")

# ---------- Load data (cached so it only runs once) ----------
@st.cache_data
def load_standby_kw():
    return pd.read_parquet("data/baseline.parquet")["baseline_kw"].median()
@st.cache_data
def load_hourly():
    return pd.read_parquet("data/hourly.parquet")

@st.cache_data
def load_daily():
    d = pd.read_parquet("data/daily.parquet").iloc[1:-1]
    return d[d["total_kwh"] > 1]

standby_kw = load_standby_kw()
hourly = load_hourly()
daily = load_daily()

# ---------- Sidebar controls ----------
st.sidebar.header("Settings")
tariff = st.sidebar.slider("Tariff (Rs per kWh)", 2.0, 12.0, 6.0, 0.5)
away_start, away_end = st.sidebar.slider("Away hours (Mon-Fri)", 0, 23, (10, 15))
k = st.sidebar.slider("Spike sensitivity (higher = stricter)", 2.0, 5.0, 3.0, 0.5)

# ---------- Leak 1: standby ----------
standby_kwh_year = standby_kw * 24 * 365
standby_cost = standby_kwh_year * tariff

# ---------- Leak 2: heater/AC while away ----------
h = hourly.copy()
h["hour"] = h.index.hour
h["weekday"] = h.index.dayofweek < 5
away = h[h["weekday"] & h["hour"].between(away_start, away_end)]
years = len(h) / 24 / 365.25
away_kwh_year = away["heater_ac"].sum() / years
away_cost = away_kwh_year * tariff

# ---------- Leak 3: spike days ----------
d = daily["total_kwh"]
med = d.rolling(30, center=True, min_periods=10).median()
mad = (d - med).abs().rolling(30, center=True, min_periods=10).median()
spike = d > (med + k * 1.4826 * mad)
excess = (d - med).where(spike, 0)
spike_kwh_year = excess.sum() / (len(d) / 365.25)
spike_cost = spike_kwh_year * tariff

# ---------- Cards ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Standby load", f"Rs {standby_cost:,.0f} / yr", f"{standby_kw*1000:.0f} W always on", delta_color="off")
c2.metric("Heater/AC while away", f"Rs {away_cost:,.0f} / yr", f"{away_kwh_year:,.0f} kWh", delta_color="off")
c3.metric("Spike days", f"Rs {spike_cost:,.0f} / yr", f"{int(spike.sum())} days flagged", delta_color="off")
c4.metric("Total (upper bound)", f"Rs {standby_cost + away_cost + spike_cost:,.0f} / yr")

# ---------- Charts ----------
import plotly.express as px
import plotly.graph_objects as go

st.divider()

# Chart 1: heatmap of average use by hour and month
st.subheader("When does the house use power?")
hm = hourly.copy()
hm["hour"] = hm.index.hour
hm["month"] = hm.index.month
pivot = hm.pivot_table(index="hour", columns="month", values="total_kwh", aggfunc="mean")
fig1 = px.imshow(
    pivot, aspect="auto", color_continuous_scale="YlOrRd",
    labels=dict(x="Month", y="Hour of day", color="Avg kWh"),
)
st.plotly_chart(fig1, width="stretch")

# Chart 2: daily use with spike days marked
st.subheader("Daily use, with spike days in red")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=d.index, y=d.values, mode="lines", name="Daily kWh"))
fig2.add_trace(go.Scatter(
    x=d.index[spike.values], y=d[spike].values, mode="markers",
    name="Spike day", marker=dict(color="red", size=8),
))
fig2.update_layout(yaxis_title="kWh per day")
st.plotly_chart(fig2, width="stretch")

# Chart 3: where the metered energy goes, by month
st.subheader("Energy by sub-meter, per month")
monthly = daily[["kitchen", "laundry", "heater_ac", "other_kwh"]].resample("MS").sum()
fig3 = px.bar(monthly, x=monthly.index, y=monthly.columns,
                            labels=dict(dt="Month", value="kWh", variable="Meter"))
st.plotly_chart(fig3, width="stretch")