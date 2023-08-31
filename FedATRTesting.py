import datetime
import pandas as pd
import yfinance as yf
import vectorbt as vbt
import pytz
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates

# df.resample('4h').last

# Define the Fed event release dates
fed_dates = [
    #"2021-06-16", "2021-07-28", "2021-09-22",
    "2021-11-03", "2021-12-15", "2022-01-27", "2022-03-17", "2022-05-04",
    "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    "2023-02-01", "2023-03-22", "2023-05-03"
]

# Define the time intervals and their corresponding durations
time_intervals = {
    # '30m': {'duration': pd.DateOffset(minutes=30)},
    '1h': {'duration': pd.DateOffset(hours=1)},
    # '4h': {'duration': pd.DateOffset(hours=4)},
    '1d': {'duration': pd.DateOffset(days=1)}
}

n = 14

prior_atr_values = []
event_tr_values = []
after_atr_values = []

# Iterate over the fed_dates and calculate volatility measures
for fed_date in fed_dates:
    event_date = pd.to_datetime(fed_date).date()
    print(f"Event Date: {event_date}")

    for interval, interval_info in time_intervals.items():
        print(f"Time Interval: {interval}")

        # Set the duration for the current time interval
        duration = interval_info['duration']

        # Calculate the start and end times for the prior ATR calculation
        # if interval == '30m':
        #     start_time_prior = event_date + pd.DateOffset(hours=7, minutes=30)
        #     end_time_prior = event_date + pd.DateOffset(hours=14, minutes=30)
        if interval == '1h':
            start_time_prior = datetime.datetime.combine(
                event_date, datetime.time(0, 0))
            end_time_prior = event_date + pd.DateOffset(hours=14)
        # elif interval == '4h':
        #     start_time_prior = event_date - pd.DateOffset(hours=44)
        #     end_time_prior = event_date + pd.DateOffset(hours=12)
        elif interval == '1d':
            start_time_prior = event_date - pd.DateOffset(days=14)
            end_time_prior = event_date - pd.DateOffset(days=0)

        # Calculate the start and end times for the true range during the event
        # if interval == '30m':
        #     start_time_event = datetime.datetime.combine(
        #         event_date, datetime.time(14, 30))
        #     end_time_event = datetime.datetime.combine(
        #         event_date, datetime.time(15, 0))
        if interval == '1h':
            start_time_event = datetime.datetime.combine(
                event_date, datetime.time(14, 0))
            end_time_event = datetime.datetime.combine(
                event_date, datetime.time(15, 0))
        # elif interval == '4h':
        #     start_time_event = datetime.datetime.combine(
        #         event_date, datetime.time(12, 0))
        #     end_time_event = datetime.datetime.combine(
        #         event_date, datetime.time(16, 0))
        elif interval == '1d':
            start_time_event = datetime.datetime.combine(
                event_date, datetime.time(0, 0))
            end_time_event = datetime.datetime.combine(
                event_date, datetime.time(23, 59))

        # Calculate the start and end times for the ATR after the event
        # if interval == '30m':
        #     start_time_after = datetime.datetime.combine(
        #         event_date, datetime.time(15, 0))
        #     end_time_after = datetime.datetime.combine(
        #         event_date, datetime.time(22, 0))
        if interval == '1h':
            start_time_after = datetime.datetime.combine(
                event_date, datetime.time(15, 0))
            end_time_after = event_date + \
                pd.DateOffset(days=1) + datetime.timedelta(hours=5)
        # elif interval == '4h':
        #     start_time_after = datetime.datetime.combine(
        #         event_date, datetime.time(16, 0))
        #     end_time_after = event_date + \
        #         pd.DateOffset(days=2)
        elif interval == '1d':
            start_time_after = datetime.datetime.combine(
                event_date + pd.DateOffset(days=1), datetime.time(0, 0))
            end_time_after = event_date + \
                pd.DateOffset(days=15) - datetime.timedelta(minutes=1)

        start_time_prior = pd.Timestamp(start_time_prior).tz_localize('UTC')
        end_time_prior = pd.Timestamp(end_time_prior).tz_localize('UTC')
        start_time_event = pd.Timestamp(start_time_event).tz_localize('UTC')
        end_time_event = pd.Timestamp(end_time_event).tz_localize('UTC')
        start_time_after = pd.Timestamp(start_time_after).tz_localize('UTC')
        end_time_after = pd.Timestamp(end_time_after).tz_localize('UTC')

        # Fetch BTC price data from Yahoo Finance API
        ticker = yf.Ticker("BTC-USD")

        # if interval == '30m':
        #     # Fetch price data for the prior period
        #     prior_price_data = ticker.history(
        #         start=start_time_prior, end=end_time_prior, interval='30m')

        #     # Fetch price data for the during period
        #     event_price_data = ticker.history(
        #         start=start_time_event, end=end_time_event, interval='30m')

        #     # Fetch price data for the after period
        #     after_price_data = ticker.history(
        #         start=start_time_after, end=end_time_after, interval='30m')
        # elif interval != '30m':
        # interval = interval
        # Fetch price data for the prior period
        prior_price_data = ticker.history(
            start=start_time_prior, end=end_time_prior, interval=interval)

        # Fetch price data for the during period
        event_price_data = ticker.history(
            start=start_time_event, end=end_time_event, interval=interval)

        # Fetch price data for the after period
        after_price_data = ticker.history(
            start=start_time_after, end=end_time_after, interval=interval)

        # Filter price data based on the calculated start and end times
        prior_data = prior_price_data[(prior_price_data.index >= start_time_prior) & (
            prior_price_data.index <= end_time_prior)]
        event_data = event_price_data[(event_price_data.index >= start_time_event) & (
            event_price_data.index <= end_time_event)]
        after_data = after_price_data[(after_price_data.index >= start_time_after) & (
            after_price_data.index <= end_time_after)]

        # Calculate the True Range
        prior_true_range = prior_data['High'] - prior_data['Low']
        event_true_range = event_data['High'] - event_data['Low']
        after_true_range = after_data['High'] - after_data['Low']

        # Check if enough prior data is available
        if len(prior_true_range) >= n:
            # Calculate the Average True Range (ATR)
            prior_atr = (((prior_true_range.rolling(
                n).mean().iloc[-1]) * (n-1)) + prior_true_range.iloc[-1]) / n
            after_atr = (((after_true_range.rolling(
                n).mean().iloc[-1]) * (n-1)) + after_true_range.iloc[-1]) / n
            
            prior_atr = prior_atr / prior_data['Close'].iloc[-1] * 100
            event_true_range = event_true_range / event_data['Close'].iloc[-1] * 100
            after_atr = after_atr / after_data['Close'].iloc[-1] * 100

            print(f"Prior ATR: {prior_atr:.2f}")
            print(f"Event TR: {event_true_range.iloc[0]:.2f}")
            print(f"After ATR: {after_atr:.2f}")

            prior_atr_values.append(prior_atr)
            event_tr_values.append(event_true_range.iloc[0])
            after_atr_values.append(after_atr)

        else:
            print("Not enough prior data available to calculate ATR.")

# Create two separate lists for 1-hour and 1-day data
hourly_prior_values = [prior_atr_values[i]
                            for i in range(len(prior_atr_values)) if i % 2 == 0]
daily_prior_values = [prior_atr_values[i]
                           for i in range(len(prior_atr_values)) if i % 2 != 0]
hourly_during_values = [event_tr_values[i]
                            for i in range(len(event_tr_values)) if i % 2 == 0]
daily_during_values = [event_tr_values[i]
                           for i in range(len(event_tr_values)) if i % 2 != 0]
hourly_after_values = [after_atr_values[i]
                            for i in range(len(after_atr_values)) if i % 2 == 0]
daily_after_values = [after_atr_values[i]
                           for i in range(len(after_atr_values)) if i % 2 != 0]

# Calculate the bar positions and widths for each graph
bar_width = 10
x_numeric = mdates.date2num(fed_dates)
bar1_position = x_numeric - bar_width
bar2_position = x_numeric
bar3_position = x_numeric + bar_width

fig, ax = plt.subplots()
ax.bar(bar1_position, hourly_prior_values, width=bar_width, label='Prior ATR Values')
ax.bar(bar2_position, hourly_during_values, width=bar_width, label='During TR Values')
ax.bar(bar3_position, hourly_after_values, width=bar_width, label='After ATR Values')

ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.xaxis.set_major_locator(mdates.DayLocator())

ax.set_xticks(x_numeric)

plt.xticks(rotation=55)
plt.xlabel("Fed Event Dates")
plt.ylabel("BTC Volatility")
plt.title("Effects of Fed Dates on BTC Volatility (1h)")
plt.legend()
plt.tight_layout()
plt.show()

bar_width = 10
x_numeric = mdates.date2num(fed_dates)
bar1_position = x_numeric - bar_width
bar2_position = x_numeric
bar3_position = x_numeric + bar_width

fig, ax = plt.subplots()
ax.bar(bar1_position, daily_prior_values, width=bar_width, label='Prior ATR Values')
ax.bar(bar2_position, daily_during_values, width=bar_width, label='During TR Values')
ax.bar(bar3_position, daily_after_values, width=bar_width, label='After ATR Values')

ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.xaxis.set_major_locator(mdates.DayLocator())

ax.set_xticks(x_numeric)

plt.xticks(rotation=55)
plt.xlabel("Fed Event Dates")
plt.ylabel("BTC Volatility")
plt.title("Effects of Fed Dates on BTC Volatility (1d)")
plt.legend()
plt.tight_layout()
plt.show()




