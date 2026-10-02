import pandas as pd

# 1. Load the clean minute-level file
df = pd.read_parquet("data/minute.parquet")

# 2. Pick the columns we want to add up
cols = ["total_kwh", "kitchen", "laundry", "heater_ac", "other_kwh"]

# 3. Hourly totals
hourly = df[cols].resample("h").sum()
print("Hourly rows:", len(hourly))

# 4. Daily totals
daily = hourly.resample("D").sum()
print("Daily rows:", len(daily))

# 5. Save both
hourly.to_parquet("data/hourly.parquet")
daily.to_parquet("data/daily.parquet")

# 6. Quick look
print(daily.head())
print("Average kWh per day:", round(daily["total_kwh"].mean(), 2))

# 7. Save the nightly baseline so the app doesn't need the big file
night = df["kw"].between_time("01:00", "05:00")
baseline = night.groupby(night.index.date).quantile(0.05)
baseline.to_frame("baseline_kw").to_parquet("data/baseline.parquet")
print("Saved data/baseline.parquet")