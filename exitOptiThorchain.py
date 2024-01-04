from utilsThorchain.thorchainCalcul import getValueOfAssetInRune, formulaGetSwapFee
from tools.init import initBalance
from utilsMaya.mayaInteraction import swapMaya
from constantes.myAddresses import MY_ADDRESS_MAYA, MY_ADDRESS
from constantes.constantes import DECIMALS_RUNE, OUTBOUND_FEES_RUNE, NETWORK_FEES_RUNE
from classes.Asset import AssetThorchain
from classes.Pool import Pool
from utilsThorchain.thorchainInteraction import getBlock, getThorchainPool, swapThorchain
from utilsThorchain.thorchainUtils import updateThorchainAssetPoolData
import time

balances = initBalance()

currentBlock = getBlock
poolData = getThorchainPool()

updateThorchainAssetPoolData(
    balances=balances,
    poolData=poolData,
    currentBlock=currentBlock,
)

for asset in balances.balancesThorchain.listAssets:
    if asset.poolName == 'THOR.RUNE': #ETH.ETH ETH.DAI-0X6B175474E89094C44DA98B954EEDEAC495271D0F THOR.RUNE ETH.WBTC-0X2260FAC5E5542A773AA44FBCFEDF7C193BC2C599 BTC.BTC BNB.BTCB-1DE BNB.BUSD-BD1 BNB.ETH-1C9 ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7
        assetIn=asset
    if asset.poolName == 'ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7':
        assetOut=asset


def formulaGainSwapToRuneOutput(
    amountIn: float, toRune: bool, asset: AssetThorchain, isSynthSwap: bool, synthMultiplier=1
) -> float:
    X = asset.pool.balanceAssetInPool if toRune == True else asset.pool.balanceRuneInPoolAsset
    Y = asset.pool.balanceRuneInPoolAsset if toRune == True else asset.pool.balanceAssetInPool
    x = float(amountIn)
    num = x * X * Y
    denum = (x + X) ** 2

    # if isSynthSwap == True:
    #     X = X * synthMultiplier
    #     Y = Y * synthMultiplier
    # logging.info(f" x, X, Y {x,X,Y}")
    amountOut = num / denum
    
    outboundFees = OUTBOUND_FEES_RUNE*10**DECIMALS_RUNE
    networkFees = NETWORK_FEES_RUNE*10**DECIMALS_RUNE
    
    amountInInRune = getValueOfAssetInRune(amount=amountIn,asset=asset)

    gain = amountOut-outboundFees-networkFees-amountInInRune
    
    print(f'gain {gain} amountOut {amountOut} amountInInRune {amountInInRune}')
    return gain


# def dichotomie(
#     f,
#     low,
#     high,
#     e,
#     toRune,
#     asset,
#     isSynthSwapIn,
#     isSynthSwapOut,
# ):
#     while high - low > e:
#         mid = low + (high - low)/2
        
#         f_mid = f(mid, toRune, asset, isSynthSwapIn, isSynthSwapOut)
#         f_high = f(high, toRune, asset, isSynthSwapIn, isSynthSwapOut)

#         if f_mid < f_high:
#             low = mid
#         else:
#             high = mid

#     mid = (low + high) / 2
#     final_value = f(mid, toRune, asset, isSynthSwapIn, isSynthSwapOut)
#     return mid, final_value


# (amountInOpti, gain) = dichotomie(
#     f=formulaGainSwapToRuneOutput,
#     low=1000,
#     high=int(assetIn.balance),
#     e=1000,
#     toRune=True,
#     asset=assetIn,
#     isSynthSwapIn=True,
#     isSynthSwapOut=True,
# )

# print(f'amountInOpti {amountInOpti} gain {gain}')



# slipFees = formulaGetSwapFee(toRune=True,pool=assetIn.pool,amountIn=assetIn.balance,isSynthSwap=True)
# outboundFees = OUTBOUND_FEES_RUNE * 10**DECIMALS_RUNE
# networkFees = NETWORK_FEES_RUNE * 10**DECIMALS_RUNE

# totalFees = slipFees + outboundFees + networkFees

# print(f'amountIn = {assetIn.balance} {assetIn.symbol}, totalFees = {totalFees} slipFees = {slipFees}, outboundFees {outboundFees} networkFees {networkFees}')


# Variables
total_balance = 500*1e8 # Total ETH to be swapped
max_num_swaps = 50  # Minimum swap amount to start with
optimal_fees = float('inf')
optimal_swap_amount = 0
optimal_num_swaps = 0

# Loop over different swap amounts
for num_swaps in range(1, max_num_swaps + 1):
    swap_amount = total_balance / num_swaps
    # slipFees = formulaGetSwapFee(True, assetIn.pool, swap_amount, True) * num_swaps
    slipFees = formulaGetSwapFee(False, assetOut.pool, swap_amount, True) * num_swaps
    slipFees = getValueOfAssetInRune(amount=slipFees,asset=assetOut)
    # assetIn.pool.balanceAssetInPool -= swap_amount
    # print(f' swap_amount {swap_amount} assetIn.pool.balanceAssetInPool {assetIn.pool.balanceAssetInPool}')
    outboundFees = OUTBOUND_FEES_RUNE * 10**DECIMALS_RUNE * num_swaps
    networkFees = NETWORK_FEES_RUNE * 10**DECIMALS_RUNE * num_swaps

    totalFees = slipFees + outboundFees + networkFees
    
    print(f'swap_amount {swap_amount/1e8} num_swaps {num_swaps} totalFees {totalFees/1e8} slipFees {slipFees/1e8} outboundFees {outboundFees/1e8} networkFees {networkFees/1e8}')
    # Compare to find the optimal scenario
    if totalFees < optimal_fees:
        optimal_fees = totalFees
        optimal_swap_amount = swap_amount
        optimal_num_swaps = num_swaps

# Print the optimal scenario
print(f'Optimal swap amount: {optimal_swap_amount/1e8} assetIn, Number of swaps: {optimal_num_swaps}, Total fees: {optimal_fees/1e8}')


for num_swaps in range(1, optimal_num_swaps + 1):
    txHash = swapThorchain(address=MY_ADDRESS,amount=optimal_swap_amount,assetIn=assetIn,assetOut=assetOut, limitOrderValue=1)
    print(f'txHash : {txHash.text}')
    time.sleep(1)