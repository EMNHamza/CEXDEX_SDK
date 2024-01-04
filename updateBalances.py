from tools.init import initBalance
from utilsBybit.bybit_utils import getBybitBalances
from utilsThorchain.thorchainInteraction import getThorchainBalances
from utilsMaya.mayaInteraction import getMayaBalances
from tools.utilsCsv import writeInCSV
from datetime import datetime

priceBTC = 43182
priceETH = 2276
priceRUNE = 5.65
priceCACAO = 0.71

def calculate_total_value_in_dollars(asset_dict):
    total_value = 0
    for key, value in asset_dict.items():
        if key == 'BTC':
            total_value += value * priceBTC
        elif key == 'RUNE':
            total_value += value * priceRUNE
        elif key == 'ETH':
            total_value += value * priceETH
        elif key == 'CACAO':
            total_value += value * priceCACAO
        elif key == 'STABLE':
            total_value += value  # Assuming STABLE is already in dollars
    return total_value


def getBalancesTelegram():
    balancesTotal = initBalance()

    balanceInThorchain = {}
    for asset in balancesTotal.balancesThorchain.listAssets:
        if asset.assetType in balanceInThorchain:
            balanceInThorchain[asset.assetType] += asset.balance/10**asset.decimals
        else:
            balanceInThorchain[asset.assetType] = asset.balance/10**asset.decimals



    balanceInBybit = {}
    for asset in balancesTotal.balancesBybit.listAssets:
        if asset.assetType in balanceInBybit:
            balanceInBybit[asset.assetType] += asset.balance
        else:
            balanceInBybit[asset.assetType] = asset.balance



    balanceInMaya= {}
    for asset in balancesTotal.balancesMaya.listAssets:
        if asset.assetType in balanceInMaya:
            balanceInMaya[asset.assetType] += asset.balance/10**asset.decimals
        else:
            balanceInMaya[asset.assetType] = asset.balance/10**asset.decimals



    for d in [balanceInThorchain, balanceInBybit, balanceInMaya]:
        d['DOLLARS'] = calculate_total_value_in_dollars(d)

    combinedDict = {}
    for d in [balanceInThorchain, balanceInBybit, balanceInMaya]:
        for key, value in d.items():
            if key in combinedDict:
                combinedDict[key] += value
            else:
                combinedDict[key] = value
    
    balancesTotal = {'thorchain' : balanceInThorchain, 'bybit' : balanceInBybit, 'maya' : balanceInMaya, 'total' : combinedDict}
    print(balanceInThorchain)
    print(balanceInBybit)
    print(balanceInMaya)
    print(combinedDict)

    return balancesTotal


balancesTotal = initBalance()

balanceInThorchain = {}
for asset in balancesTotal.balancesThorchain.listAssets:
    if asset.assetType in balanceInThorchain:
        balanceInThorchain[asset.assetType] += asset.balance/10**asset.decimals
    else:
        balanceInThorchain[asset.assetType] = asset.balance/10**asset.decimals

balanceInBybit = {}
for asset in balancesTotal.balancesBybit.listAssets:
    if asset.assetType in balanceInBybit:
        balanceInBybit[asset.assetType] += asset.balance
    else:
        balanceInBybit[asset.assetType] = asset.balance



balanceInMaya= {}
for asset in balancesTotal.balancesMaya.listAssets:
    if asset.assetType in balanceInMaya:
        balanceInMaya[asset.assetType] += asset.balance/10**asset.decimals
    else:
        balanceInMaya[asset.assetType] = asset.balance/10**asset.decimals



for d in [balanceInThorchain, balanceInBybit, balanceInMaya]:
    d['DOLLARS'] = calculate_total_value_in_dollars(d)

combinedDict = {}
for d in [balanceInThorchain, balanceInBybit, balanceInMaya]:
    for key, value in d.items():
        if key in combinedDict:
            combinedDict[key] += value
        else:
            combinedDict[key] = value

print(balanceInThorchain)
print(balanceInBybit)
print(balanceInMaya)
print(combinedDict)




current_datetime = datetime.now()
formatted_date = current_datetime.date().strftime("%Y-%m-%d")
formatted_time = current_datetime.time().strftime("%H:%M:%S")

#DATE,HEURE,BALANCE_RUNE_THORCHAIN,BALANCE_BTC_THORCHAIN,BALANCE_STABLE_THORCHAIN,BALANCE_ETH_THORCHAIN,BALANCE_TOTAL_THORCHAIN_DOLLARS,BALANCE_BTC_BYBIT,BALANCE_STABLE_BYBIT,BALANCE_ETH_BYBIT,BALANCE_TOTAL_DOLLARS_BYBIT,BALANCE_CACAO_MAYA,BALANCE_RUNE_MAYA, BALANCE_BTC_MAYA, BALANCE_STABLE_MAYA, BALANCE_ETH_MAYA, BALANCE_TOTAL_MAYA_DOLLARS,BALANCE_TOTAL_BTC,BALANCE_TOTAL_STABLE,BALANCE_TOTAL_RUNE,BALANCE_TOTAL_ETH,BALANCE_TOTAL_DOLLARS_BOT

#DATE,HEURE,BALANCE_BTC_THORCHAIN,BALANCE_BTC_BYBIT,BALANCE_BTC_MAYA,BALANCE_BTC_TOTAL,BALANCE_STABLE_THORCHAIN,BALANCE_STABLE_BYBIT,BALANCE_STABLE_MAYA,BALANCE_STABLE_TOTAL,BALANCE_ETH_THORCHAIN,BALANCE_ETH_BYBIT,BALANCE_ETH_MAYA,BALANCE_ETH_TOTAL,BALANCE_RUNE_THORCHAIN,BALANCE_RUNE_BYBIT,BALANCE_RUNE_MAYA,BALANCE_RUNE_TOTAL,BALANCE_CACAO_MAYA,BALANCE_CACAO_TOTAL,BALANCE_DOLLARS_THORCHAIN,BALANCE_DOLLARS_BYBIT,BALANCE_DOLLARS_MAYA,BALANCE_DOLLARS_TOTAL

row_to_add = [formatted_date,formatted_time,balanceInThorchain['BTC'],balanceInBybit['BTC'],balanceInMaya['BTC'],combinedDict['BTC'],
              balanceInThorchain['STABLE'],balanceInBybit['STABLE'],balanceInMaya['STABLE'],combinedDict['STABLE'],
              balanceInThorchain['ETH'],balanceInBybit['ETH'],0,combinedDict['ETH'],
              balanceInThorchain['RUNE'],0,0,combinedDict['RUNE'],
              balanceInMaya['CACAO'],combinedDict['CACAO'],
              round(balanceInThorchain['DOLLARS'], 3),round(balanceInBybit['DOLLARS'], 3),round(balanceInMaya['DOLLARS'], 3),round(combinedDict['DOLLARS'], 3)]

writeInCSV(fileName='csv/balances.csv',rowToAdd=row_to_add)

