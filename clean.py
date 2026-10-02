import pandas as pd

# 1. Load
df = pd.read_csv(
    "data/household_power_consumption.txt",
    sep=";", na_values="?", low_memory=False,
)

# 2. Combine Date + Time into one timestamp
df["dt"] = pd.to_datetime(df["Date"] + " " + df["Time"], dayfirst=True)
df = df.drop(columns=["Date", "Time"])
df = df.set_index("dt").sort_index()

# 3. Make everything numeric
df = df.astype(float)

# 4. Rename columns to friendly names
df = df.rename(columns={
    "Global_active_power": "kw",
    "Sub_metering_1": "kitchen",
    "Sub_metering_2": "laundry",
    "Sub_metering_3": "heater_ac",
})

# 5. See how much data is missing
print("Missing share per column:")
print(df.isna().mean().round(4))

# 6. Fill only short gaps (up to 10 minutes)
df = df.interpolate(limit=10)

print("Rows:", len(df))
print("From", df.index.min(), "to", df.index.max())

# 7. Convert to kWh per minute
df["total_kwh"] = df["kw"] / 60
for c in ["kitchen", "laundry", "heater_ac"]:
    df[c] = df[c] / 1000

# 8. The "everything else" (lights, TV, fridge...)
metered = df[["kitchen", "laundry", "heater_ac"]].sum(axis=1)
df["other_kwh"] = (df["total_kwh"] - metered).clip(lower=0)

# 9. Save the clean file
df.to_parquet("data/minute.parquet")
print("Saved data/minute.parquet")