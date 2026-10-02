import pandas as pd

# 1. Load the clean minute-level data
df = pd.read_parquet("data/minute.parquet")

# 2. Keep only the quiet night hours (1 AM to 5 AM)
night = df.between_time("01:00", "05:00")["kw"]

# 3. For each day, find the low point of the night.
#    The 5th percentile ignores one-off dips.
baseline = night.groupby(night.index.date).quantile(0.05)

print("Daily night baseline (kW):")
print(baseline.describe().round(3))

# 4. The typical always-on load across all days
standby_kw = baseline.median()
print("Typical standby load (kW):", round(standby_kw, 3))
print("Typical standby load (watts):", round(standby_kw * 1000))

# 5. Turn it into yearly energy and rupees
tariff = 6.0   # rupees per kWh, a placeholder we can change later
standby_kwh_year = standby_kw * 24 * 365
standby_cost_year = standby_kwh_year * tariff

print("Standby energy per year (kWh):", round(standby_kwh_year))
print("Standby cost per year (Rs):", round(standby_cost_year))

# ---------- Leak 2: heater/AC while away ----------
hourly = pd.read_parquet("data/hourly.parquet")
hourly["hour"] = hourly.index.hour
hourly["weekday"] = hourly.index.dayofweek < 5   # Mon-Fri

# Weekdays, 10:00 to 15:59 = "probably nobody home"
away = hourly[hourly["weekday"] & hourly["hour"].between(10, 15)]

years = len(hourly) / 24 / 365.25
away_kwh_year = away["heater_ac"].sum() / years
total_heater_year = hourly["heater_ac"].sum() / years

print("Heater/AC total per year (kWh):", round(total_heater_year))
print("Heater/AC while away per year (kWh):", round(away_kwh_year))
print("Share of heater/AC use while away:", round(away_kwh_year / total_heater_year * 100), "%")
print("Cost of away-hours use per year (Rs):", round(away_kwh_year * tariff))

# ---------- Leak 3: spike days ----------
daily = pd.read_parquet("data/daily.parquet")

# Drop the partial first and last days, and days with no data
daily = daily.iloc[1:-1]
daily = daily[daily["total_kwh"] > 1]

d = daily["total_kwh"]

# "Normal" = rolling 30-day median. Spread = median absolute deviation.
med = d.rolling(30, center=True, min_periods=10).median()
mad = (d - med).abs().rolling(30, center=True, min_periods=10).median()

# A spike is a day more than 3 "spreads" above normal
spike = d > (med + 3 * 1.4826 * mad)
excess = (d - med).where(spike, 0)

years_d = len(d) / 365.25
print("Spike days found:", int(spike.sum()), "of", len(d))
print("Excess energy on spike days per year (kWh):", round(excess.sum() / years_d))
print("Cost of spike days per year (Rs):", round(excess.sum() / years_d * tariff))

print("Top 5 spike days:")
print(excess.sort_values(ascending=False).head(5).round(1))

# ---------- Check the biggest spike day ----------
day = "2007-02-03"
one_day = hourly.loc[day, ["total_kwh", "kitchen", "laundry", "heater_ac", "other_kwh"]]
print("Hourly breakdown for", day)
print(one_day.round(2))