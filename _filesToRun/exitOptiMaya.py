from tools.init import initBalance
from utilsMaya.mayaInteraction import swapMaya
from constantes.constantes import DECIMALS_CACAO, OUTBOUND_FEES_CACAO, NETWORK_FEES_CACAO
from constantes.myAddresses import MY_ADDRESS_MAYA

from utilsThorchain.thorchainInteraction import getBlock, getThorchainPool, swapThorchain
from utilsThorchain.thorchainUtils import updateThorchainAssetPoolData

from utilsMaya.mayaUtils import updateMayaAssetPoolData
from utilsMaya.mayaInteraction import getMayaBlock, getMayaPool
from utilsMaya.mayaCalcul import formulaGetDoubleSwapFee, getValueOfAssetInCacao
import time 

balances = initBalance()
currentBlock = getMayaBlock()
poolData = getMayaPool()

updateMayaAssetPoolData(
    balances=balances,
    poolData=poolData,
    currentBlock=currentBlock,
)

for asset in balances.balancesMaya.listAssets:
    if asset.poolName == 'ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7': #ETH.ETH ETH.DAI-0X6B175474E89094C44DA98B954EEDEAC495271D0F THOR.RUNE ETH.WBTC-0X2260FAC5E5542A773AA44FBCFEDF7C193BC2C599 BTC.BTC BNB.BTCB-1DE BNB.BUSD-BD1 BNB.ETH-1C9 ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7 ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48 ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7
        assetIn=asset
        assetIn.pool.balanceAssetInPool = asset.pool.balanceAssetInPool * 1e2
    if asset.poolName == 'THOR.RUNE':
        assetOut=asset        
        assetOut.pool.balanceAssetInPool = asset.pool.balanceAssetInPool * 1e2


# Variables
total_amount = assetIn.balance * 1e2 # Total ETH to be swapped
max_num_swaps = 50  # Minimum swap amount to start with
optimal_fees = float('inf')
optimal_swap_amount = 0
optimal_num_swaps = 0

# Loop over different swap amounts
for num_swaps in range(1, max_num_swaps + 1):
    swap_amount = total_amount / num_swaps
    slipFees = formulaGetDoubleSwapFee(swap_amount, assetIn.pool, assetOut.pool, True, False) * num_swaps
    slipFeesInCacao = getValueOfAssetInCacao(amount=slipFees, pool=assetOut.pool)
    outboundFees = OUTBOUND_FEES_CACAO * 10**DECIMALS_CACAO * num_swaps
    networkFees = NETWORK_FEES_CACAO * 10**DECIMALS_CACAO * num_swaps

    totalFees = slipFeesInCacao + outboundFees + networkFees
    
    print(f'swap_amount {swap_amount/1e10} num_swaps {num_swaps} totalFees {totalFees/1e10} slipFeesInCacao {slipFeesInCacao/1e10} outboundFees {outboundFees/1e10} networkFees {networkFees/1e10}')
    # Compare to find the optimal scenario
    if totalFees < optimal_fees:
        optimal_fees = totalFees
        optimal_swap_amount = swap_amount
        optimal_num_swaps = num_swaps

# Print the optimal scenario
print(f'Optimal swap amount: {optimal_swap_amount/1e10} {assetIn.symbol}, Number of swaps: {optimal_num_swaps}, Total fees: {optimal_fees/1e10}')


for num_swaps in range(1, optimal_num_swaps + 1):
    txHash = swapMaya(address=MY_ADDRESS_MAYA,amount=optimal_swap_amount/1e2,assetIn=assetIn,assetOut=assetOut, limitOrderValue=1)
    print(f'txHash : {txHash.text}')
    time.sleep(3)