
from tools.init import initBalance
from utilsThorchain.thorchainInteraction import swapThorchain
from constantes.myAddresses import MY_ADDRESS

balances = initBalance()

for asset in balances.balancesThorchain.listAssets:
    if asset.poolName == 'ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48': #ETH.ETH ETH.DAI-0X6B175474E89094C44DA98B954EEDEAC495271D0F THOR.RUNE ETH.WBTC-0X2260FAC5E5542A773AA44FBCFEDF7C193BC2C599 BTC.BTC BNB.BTCB-1DE BNB.BUSD-BD1 ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7
        assetIn=asset
    if asset.poolName == 'THOR.RUNE':
        assetOut=asset
    # if asset.poolName == '':
    #     assetIn=asset

# txHash = swapThorchain(address=MY_ADDRESS,amount=5.44084371*1e8,assetIn=assetIn,assetOut=assetOut, limitOrderValue=1)

# print(f'txHash : {txHash.text}')