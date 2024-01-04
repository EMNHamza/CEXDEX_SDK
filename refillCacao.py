
from tools.init import initBalance
from utilsMaya.mayaInteraction import swapMaya
from constantes.myAddresses import MY_ADDRESS_MAYA, MY_ADDRESS
from classes.Asset import AssetMaya
from utilsMaya.mayaInteraction import depositMayaJS

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

txHash = swapMaya(address=MY_ADDRESS_MAYA,amount=82*1e8,assetIn=assetUSDC,assetOut=assetCACAO, limitOrderValue=1)


def swapMaya(
    address: str, amount: int, assetIn: AssetMaya, assetOut: AssetMaya, limitOrderValue: int
):
    amount = int(amount)
    memo = f"=:{assetOut.memoName}:{address}:{limitOrderValue}"
    print("swap", assetIn.memoName, assetOut.memoName, amount)
    
    txhash = depositMayaJS(
        amount=amount,
        asset=assetIn.memoName,
        memo=memo,
    )
    return txhash


print(f'txHash : {txHash.text}')