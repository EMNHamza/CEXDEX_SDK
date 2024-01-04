from datetime import datetime, timedelta
import pandas as pd
import os


def read_gains_from_csv(csv_file):
    dict_gain = {}
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file, index_col=False)
    # Parse the 'Date' and 'Heure' columns into a single datetime column
    df['datetime'] = pd.to_datetime(
        df['DATE'] + ' ' + df['HEURE'])

    # Calculate the current timestamp and time intervals for 24h, 6h, 3h, and 1h
    current_timestamp = datetime.now()
    last_24h = current_timestamp - timedelta(hours=24)
    last_18h = current_timestamp - timedelta(hours=18)
    last_12h = current_timestamp - timedelta(hours=12)
    last_6h = current_timestamp - timedelta(hours=6)
    last_3h = current_timestamp - timedelta(hours=3)
    last_1h = current_timestamp - timedelta(hours=1)

    # Filter the DataFrame based on the time intervals and calculate the net gains
    gain_all_time = df['GAIN_TOTAL_REAL'].sum()
    gain_24h = df.loc[df['datetime'] >= last_24h, 'GAIN_TOTAL_REAL'].sum()
    gain_18h = df.loc[df['datetime'] >= last_18h, 'GAIN_TOTAL_REAL'].sum()
    gain_12h = df.loc[df['datetime'] >= last_12h, 'GAIN_TOTAL_REAL'].sum()
    gain_6h = df.loc[df['datetime'] >= last_6h, 'GAIN_TOTAL_REAL'].sum()
    gain_3h = df.loc[df['datetime'] >= last_3h, 'GAIN_TOTAL_REAL'].sum()
    gain_1h = df.loc[df['datetime'] >= last_1h, 'GAIN_TOTAL_REAL'].sum()

    dict_gain["gain_all_time"] = gain_all_time
    dict_gain['last_24h'] = gain_24h
    dict_gain['last_18h'] = gain_18h
    dict_gain['last_12h'] = gain_12h
    dict_gain['last_6h'] = gain_6h
    dict_gain['last_3h'] = gain_3h
    dict_gain['last_1h'] = gain_1h
    return dict_gain


csv_file = "csv/dataOpp.csv"  # Replace with the actual path to your CSV file
gains_summary = read_gains_from_csv(csv_file)

print("All time gain :", round(gains_summary['gain_all_time'], 2),"$")
print("Last 24 hours gain:", round(gains_summary['last_24h'], 2),"$")
print("Last 18 hours gain:", round(gains_summary['last_18h'], 2),"$")
print("Last 12 hours gain:", round(gains_summary['last_12h'], 2),"$")
print("Last 6 hours gain:", round(gains_summary['last_6h'], 2),"$")
print("Last 3 hours gain:", round(gains_summary['last_3h'], 2),"$")
print("Last 1 hour gain:", round(gains_summary['last_1h'], 2),"$")
