from datetime import datetime
import time
from tools.utilsCsv import writeInCSV
import os
from updateBalances import getBalancesTelegram
# priceBTC = 36600

# dictAllAssets = initAllAssets()
# dictMyAssets = initMyAssets(dictAssets=dictAllAssets)
# balanceTotalBTCThorchain, balanceTotalInStableThorchain, dataBalancesCSV = initBalanceThorchainTest(dictAssets=dictMyAssets)

# bybitBalances = get_bybit_balances()
# balanceBTCBybit = float(bybitBalances['BTC'])
# balanceSTABLEBybit = float(bybitBalances['USDC'])

# balanceTotalBTCThorchain5 = balanceTotalBTCThorchain
# balanceTotalBTCThorchain30 = balanceTotalBTCThorchain
# balanceTotalInStableThorchain5 = balanceTotalInStableThorchain
# balanceTotalInStableThorchain30 = balanceTotalInStableThorchain

# balanceBTCBybit30 = float(bybitBalances['BTC'])
# balanceSTABLEBybit30 = float(bybitBalances['USDC'])

# last_update_time_1mn = datetime.min
# last_update_time_5mn = datetime.min
# last_update_time_30mn = datetime.min


# for listAsset in dictMyAssets.values():
#     for asset in listAsset:
#         if asset.balanceName.upper() == "BTC/BTC":
#             balanceBTC = asset.myBalanceThorchain
#             assetBTC = asset

# responsePool = getPool()
# balanceBTCBybitInDollars = balanceBTCBybit30 * priceBTC

# print(f'balanceBTCBybitInDollars {balanceBTCBybitInDollars}')

# dataBalanceBybit = [balanceBTCBybit30, round(balanceSTABLEBybit30,2), round(balanceBTCBybitInDollars+balanceSTABLEBybit30,2), balanceBTCBybit30 + balanceTotalBTCThorchain30/1e8, round(balanceTotalInStableThorchain30/1e8 + balanceSTABLEBybit30,2), round((balanceTotalBTCThorchain30/1e8)*priceBTC+(balanceTotalInStableThorchain30/1e8)+balanceBTCBybitInDollars+balanceSTABLEBybit30,2)]
# combined_data = dataBalancesCSV + dataBalanceBybit
# writeInCSV("csv/balances.csv",combined_data)

# while True:

#     current_time = datetime.now()

#     # print(f'current_time, last_update_time_5mn, last_update_time_30mn {current_time, last_update_time_5mn, last_update_time_30mn}')

#     # if (current_time - last_update_time_5mn).total_seconds() >= 60 * 5:

#     #     newBalanceTotalBTC, newBalanceTotalInStable = initBalance(dictAssets=dictMyAssets)

#     #     print(f'gain BTC 5mn : {newBalanceTotalBTC - balanceTotalBTC5}')
#     #     print(f'gain STABLE 5mn : {newBalanceTotalInStable - balanceTotalInStable5}')

#     #     if newBalanceTotalBTC - balanceTotalBTC5 <  -6150:
#     #         print(f'gain BTC négatif 5mn : {newBalanceTotalBTC - balanceTotalBTC5}')
#     #         os.system("pkill -f main.py")

#     #     if newBalanceTotalInStable - balanceTotalInStable5 < -150000000:
#     #         print(f'gain STABLE négatif 5mn : {newBalanceTotalInStable - balanceTotalInStable5}')
#     #         os.system("pkill -f main.py")

#     #     balanceTotalBTC5 = newBalanceTotalBTC
#     #     balanceTotalInStable5 = newBalanceTotalInStable
#     #     last_update_time_5mn = current_time

#     if (current_time - last_update_time_30mn).total_seconds() >= 60 * 5:
#         print('checking balances...')
#         newBalanceTotalBTCThorchain, newBalanceTotalStableThorchain, newDataBalancesCSV = initBalanceThorchainTest(
#             dictAssets=dictMyAssets)

#         newBybitBalances = get_bybit_balances()
#         newBalanceBTCBybit = float(newBybitBalances['BTC'])
#         newBalanceSTABLEBybit = float(newBybitBalances['USDC'])

#         balanceTotalBTCBOT = balanceBTCBybit30 + balanceTotalBTCThorchain30/1e8
#         newBalanceTotalBTCBOT = newBalanceBTCBybit + newBalanceTotalBTCThorchain/1e8

#         balanceTotalStableBOT = round(balanceTotalInStableThorchain30/1e8 + balanceSTABLEBybit30,2)
#         newBalanceTotalStableBOT = round(newBalanceSTABLEBybit + newBalanceTotalStableThorchain/1e8,2)

#         balanceTotalDollarsBOT = round(balanceTotalStableBOT + balanceTotalBTCBOT*priceBTC,2)
#         newBalanceTotalDollarsBOT = round(newBalanceTotalStableBOT + newBalanceTotalBTCBOT*priceBTC,2)

#         print(f'thorchain : newBalanceTotalBTC {newBalanceTotalBTCThorchain/1e8} newBalanceTotalInStable {newBalanceTotalStableThorchain/1e8}')
#         print(f'bybit : newBalanceBTCBybit {newBalanceBTCBybit} newBalanceSTABLEBybit {newBalanceSTABLEBybit}')
#         print(f'total balances : ALL : {newBalanceTotalDollarsBOT} BTC : {newBalanceTotalBTCBOT} STABLE : {newBalanceTotalStableBOT}')

#         print(f'new : {newBalanceTotalDollarsBOT} old : {balanceTotalDollarsBOT} threshold : {0.999 * balanceTotalDollarsBOT}')

#         if newBalanceTotalDollarsBOT < 0.999 * balanceTotalDollarsBOT:
#             print(f'GAIN NEGATIVE : new : {newBalanceTotalDollarsBOT} old : {balanceTotalDollarsBOT} threshold : {0.999 * balanceTotalDollarsBOT}')
#             os.system("pkill -f testCexDex.py")
#             break


#         balanceTotalBTCThorchain30 = newBalanceTotalBTCThorchain
#         balanceTotalInStableThorchain30 = newBalanceTotalStableThorchain
#         balanceBTCBybit30 = newBalanceBTCBybit
#         balanceSTABLEBybit30 = newBalanceSTABLEBybit
#         last_update_time_30mn = current_time

#         newResponsePool = getPool()
#         newBalanceBTCBybitInDollars = newBalanceBTCBybit * priceBTC
#         newDataBalanceBybit = [newBalanceBTCBybit, round(newBalanceSTABLEBybit,2), round(newBalanceBTCBybitInDollars+newBalanceSTABLEBybit,2), newBalanceTotalBTCBOT, newBalanceTotalStableBOT, newBalanceTotalDollarsBOT]
#         new_combined_data = newDataBalancesCSV + newDataBalanceBybit
#         writeInCSV("csv/balances.csv",new_combined_data)
#         print('checking balances ending')
#     time.sleep(30)


import pandas as pd
from datetime import datetime, timedelta
import time


def read_gains_from_csv(csv_file):
    dict_gain = {}
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file, index_col=False)
    # Parse the 'Date' and 'Heure' columns into a single datetime column
    df["datetime"] = pd.to_datetime(df["DATE"] + " " + df["HEURE"])

    # Calculate the current timestamp and time intervals for 30m, 15m, 5m, and 1m
    current_timestamp = datetime.now()
    last_30m = current_timestamp - timedelta(minutes=30)
    last_15m = current_timestamp - timedelta(minutes=15)
    last_5m = current_timestamp - timedelta(minutes=5)
    last_1m = current_timestamp - timedelta(minutes=1)

    # Filter the DataFrame based on the time intervals and calculate the net gains
    gain_all_time = df["GAIN_TOTAL_REAL"].sum()
    gain_30m = df.loc[df["datetime"] >= last_30m, "GAIN_TOTAL_REAL"].sum()
    gain_15m = df.loc[df["datetime"] >= last_15m, "GAIN_TOTAL_REAL"].sum()
    gain_5m = df.loc[df["datetime"] >= last_5m, "GAIN_TOTAL_REAL"].sum()
    gain_1m = df.loc[df["datetime"] >= last_1m, "GAIN_TOTAL_REAL"].sum()

    dict_gain["gain_all_time"] = gain_all_time
    dict_gain["last_30m"] = gain_30m
    dict_gain["last_15m"] = gain_15m
    dict_gain["last_5m"] = gain_5m
    dict_gain["last_1m"] = gain_1m
    return dict_gain


# Usage


csv_file = "csv/dataOpp.csv"  # Replace with the actual path to your CSV file
counter = 0
last_update_time_1mn = datetime.min

while True:
    current_time = datetime.now()
    
    if (current_time - last_update_time_1mn).total_seconds() >= 60 * 1:
        print("checking gains...")

        # totalBalances = getBalancesTelegram()

        print(f"counter {counter}")

        gains_summary = read_gains_from_csv(csv_file)
        print("gain_all_time:", round(gains_summary["gain_all_time"], 3), "$")
        print("Last 30 minutes gain:", round(gains_summary["last_30m"], 3), "$")
        print("Last 15 minutes gain:", round(gains_summary["last_15m"], 3), "$")
        print("Last 5 minutes gain:", round(gains_summary["last_5m"], 3), "$")
        print("Last 1 minute gain:", round(gains_summary["last_1m"], 3), "$")

        if float(gains_summary["last_1m"]) < -2.0:
            counter += 1

            if counter >= 3:
                print(f'GAIN NEGATIVE last_1m :{gains_summary["last_1m"]}')
                os.system("pkill -f main.py")
                counter = 0

        if float(gains_summary["last_1m"]) < -10.0:
            print(f'GAIN ULTRA NEGATIVE last_1m :{gains_summary["last_1m"]}')
            os.system("pkill -f main.py")

        last_update_time_1mn = current_time

    time.sleep(59)
