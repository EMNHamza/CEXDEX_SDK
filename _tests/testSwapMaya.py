from tools.init import initBalance
from utilsMaya.mayaCalcul import formulaDoubleSwapOutput
from utilsMaya.mayaInteraction import getMayaPool, getMayaBlock
from utilsMaya.mayaUtils import updateMayaAssetPoolData
import copy
from constantes.constantes import DECIMALS_CACAO
import requests 
from constantes.myAddresses import MY_ADDRESS_MAYA

block = getMayaBlock()
BalancesShared = initBalance()
newPoolData = getMayaPool()
updateMayaAssetPoolData(balances=BalancesShared, poolData=newPoolData, currentBlock=block)


for asset in BalancesShared.balancesMaya.listAssets:
    if asset.poolName == 'BTC.BTC':
        assetBTC = asset
    if asset.poolName == 'ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48':
        assetUSDC = asset
    if asset.poolName == 'ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7':  
        assetUSDT = asset

assetIn = assetBTC
assetOut = assetUSDC

poolIn = assetIn.pool
poolOut = assetOut.pool

poolInToDichotomie = copy.deepcopy(poolIn)
poolOutToDichotomie = copy.deepcopy(poolOut)

poolInToDichotomie.balanceAssetInPool = poolInToDichotomie.balanceAssetInPool * 10**DECIMALS_CACAO / 10**assetIn.decimals
poolInToDichotomie.balanceCacaoInPoolAsset = poolInToDichotomie.balanceCacaoInPoolAsset 

poolOutToDichotomie.balanceAssetInPool = poolOutToDichotomie.balanceAssetInPool * 10**DECIMALS_CACAO / 10**assetIn.decimals
poolOutToDichotomie.balanceCacaoInPoolAsset = poolOutToDichotomie.balanceCacaoInPoolAsset
poolOutToDichotomie.synthSupplyRemaining = poolOutToDichotomie.synthSupplyRemaining * 10**DECIMALS_CACAO / 10**assetIn.decimals


amountIn = 0.012234 * 1e10


amountOut = formulaDoubleSwapOutput(amountIn=amountIn, poolIn=poolInToDichotomie, poolOut=poolOutToDichotomie, isSynthSwapIn=True, isSynthSwapOut=True)

print(f'amountIn : {amountIn/1e10} {assetIn.symbol} amountOut : {amountOut/1e10} {assetOut.symbol} ')


url = f'http://18.217.85.10:1317/mayachain/quote/swap?height={int(block)}&from_asset={assetIn.memoName}&to_asset={assetOut.memoName}&amount={int(amountIn/1e2)}&destination={MY_ADDRESS_MAYA}&from_address={MY_ADDRESS_MAYA}'
print(f'url {url}')

quoteSwap = requests.get(url=url).json()
expected_amount_out = int(quoteSwap['expected_amount_out']) 
outbound_fee = int(quoteSwap['fees']['outbound']) 
# liquidity = int(quoteSwap['fees']['liquidity']) / 1e8
print(f'Expected Amount Out: {expected_amount_out/ 1e8}')
print(f'Outbound Fee: {outbound_fee/ 1e8}')