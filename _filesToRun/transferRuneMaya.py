
from tools.init import initBalance
from constantes.myAddresses import MY_ADDRESS_MAYA, MY_ADDRESS
from constantes.url import URL_TRANSFER_TO_MAYA
import requests 

from classes.Asset import AssetMaya

def transferMayaJS(amount: int, asset: str, memo: str):
    print("depositMayaJS", amount, asset)
    try:
        urlDeposit = f"{URL_TRANSFER_TO_MAYA}amount1={amount}&asset1={asset}&memo1={memo}"
        responseDeposit = requests.get(url=urlDeposit, timeout=2)
    except Exception as err:
        print(f'depositMayaJS - error getting data from {URL_TRANSFER_TO_MAYA} : {err}')
    return responseDeposit


def swapMaya(
    address: str, amount: int, assetIn: AssetMaya, assetOut: AssetMaya, limitOrderValue: int
):
    amount = int(amount)
    memo = f"=:{assetOut.memoName}:{address}"
    print("memo", assetIn.memoName, memo)
    
    txhash = transferMayaJS(
        amount=amount,
        asset='THOR.RUNE',
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

txHash = swapMaya(address=MY_ADDRESS_MAYA,amount=250*1e8,assetIn=assetRUNE,assetOut=assetBTC, limitOrderValue=1)

print(f'txHash : {txHash.text}')