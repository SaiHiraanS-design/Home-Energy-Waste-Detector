# Home Energy Waste Detector
**Live app:** https://home-energy-waste-detector-mtbkrjnjfd8g5uyxhddkig.streamlit.app
Finds "leaks" in a house's electricity use from real smart-meter data and puts a rupee cost on them.

**Data:** UCI Individual Household Electric Power Consumption (about 2 million one-minute readings, one house, Dec 2006 to Nov 2010, with kitchen, laundry and water heater/AC sub-meters).

## What it detects
| Leak | Method | Result (at Rs 6/kWh) |
|---|---|---|
| Standby load | 5th percentile of 1-5 AM power per day, median across days | 222 W, about Rs 11,668/yr |
| Heater/AC while away | Heater/AC energy on weekdays 10:00-15:59 | 24% of its use, about Rs 4,756/yr |
| Spike days | Days above rolling 30-day median + 3 MAD | 22 days, about Rs 462/yr |

## How to run
    pip install -r requirements.txt
    python3 -m streamlit run app.py

To rebuild the data files from the raw download, put `household_power_consumption.txt` in `data/`, then run `clean.py` and `summarize.py`.

## Limitations
- One French house from 2006-2010, so absolute figures are not Indian household figures. The method works on any smart-meter data.
- Every figure is an upper bound. The standby load includes the fridge and router, which can't be switched off. A spike day driven by the heater is also counted in the heater leak, so the leaks overlap.
- "Away hours" is an assumption (weekdays 10:00-15:59), adjustable in the app.
