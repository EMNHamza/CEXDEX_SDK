
from tools.init import initBalance
from constantes.myAddresses import MY_ADDRESS_MAYA, MY_ADDRESS
from constantes.url import URL_TRANSFER_TO_THOR, URL_DEPOSIT_MAYA
import requests 

from classes.Asset import AssetMaya

def transferMayaJS(amount: int, asset: str, memo: str):
    print("depositMayaJS", asset, memo)
    try:
        urlDeposit = f"{URL_DEPOSIT_MAYA}amount1={amount}&asset1={asset}&memo1={memo}"
        responseDeposit = requests.get(url=urlDeposit, timeout=2)
    except Exception as err:
        print(f'depositMayaJS - error getting data from {URL_DEPOSIT_MAYA} : {err}')
    return responseDeposit


def swapMaya(
    address: str, amount: int, assetIn: AssetMaya, assetOut: AssetMaya, limitOrderValue: int
):
    amount = int(amount)
    memo = f"=:THOR.RUNE:{address}"
    # print("swap", assetIn.memoName, assetOut.memoName, amount)
    
    txhash = transferMayaJS(
        amount=amount,
        asset=assetIn.memoName,
        memo=memo,
    )
    return txhash


balances = initBalance()

for asset in balances.balancesMaya.listAssets:
    if asset.poolName == 'ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48':
        assetUSDC=asset
    if asset.poolName == 'MAYA.CACAO':
        assetCACAO=asset
    if asset.poolName == 'BTC.BTC':
        assetBTC = asset
    if asset.poolName == 'ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7':
        assetUSDT=asset
    if asset.poolName == 'THOR.RUNE':
        assetRUNE=asset
    if asset.poolName == 'ETH.ETH':
        assetETH=asset

txHash = swapMaya(address=MY_ADDRESS,amount=750*1e8,assetIn=assetRUNE,assetOut=assetRUNE, limitOrderValue=1)

print(f'txHash : {txHash.text}')