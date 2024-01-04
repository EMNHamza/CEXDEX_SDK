from tools.init import initBalance
from classes.Balances import Balances
from tools.myUtils import createPairsForBalanceType
from utilsThorchain.thorchainCalcul import testCreateThorchainSynthOnBlockOpportunity
from constantes.constantes import THRESHOLD_GAIN_NET
from utilsThorchain.thorchainInteraction import getThorchainPool, getBlock
from utilsThorchain.thorchainUtils import updateThorchainAssetPoolData
from constantes.myAddresses import MY_ADDRESS 
import traceback
import requests 

def processCreateOpportunityThorchainOnBlock(BalancesShared:Balances, block):
    try:

        pairsThorchain = createPairsForBalanceType(listAssets=BalancesShared.balancesThorchain.listAssets, orderbook='')

        for pairThorchain in pairsThorchain:
            if pairThorchain.assetIn.assetType == pairThorchain.assetOut.assetType:
                for amountInStep in range(500 * int(1e8), 10000 * int(1e8) + 1, 500 * int(1e8)):
                    if pairThorchain.assetIn.assetType != 'STABLE':
                        amountInStep = amountInStep / 35000

                        opportunityThorchain = testCreateThorchainSynthOnBlockOpportunity(
                            pairThorchain=pairThorchain,
                            amountIn=int(amountInStep),
                            typeOpp="onBlockSynth",
                            balancesThorchain=BalancesShared.balancesThorchain
                        )            
                        
                        opportunityThorchain.detectedBlock = pairThorchain.assetIn.pool.block
                        # if opportunityThorchain.amountIn/1e8 > 100:
                        print('')
                        print(f'opportunityThorchain - assetIn {opportunityThorchain.pairAsset.assetIn.symbol} assetOut {opportunityThorchain.pairAsset.assetOut.symbol}')
                        print(f'opportunityThorchain - amountIn {opportunityThorchain.amountIn/1e8} amountOutEstimated {opportunityThorchain.amountOutEstimated/1e8} outboundFees {opportunityThorchain.outboundFees/1e8} slipFees {opportunityThorchain.slipFees/1e8}')
                        url = f'http://192.248.157.141:1317/thorchain/quote/swap?height={block}&from_asset={opportunityThorchain.pairAsset.assetIn.memoName}&to_asset={opportunityThorchain.pairAsset.assetOut.memoName}&amount={opportunityThorchain.amountIn}&destination={MY_ADDRESS}'
                        print(f'url {url}')
                        quoteSwap = requests.get(url=url).json()
                        expected_amount_out = int(quoteSwap['expected_amount_out']) / 1e8
                        outbound_fee = int(quoteSwap['fees']['outbound']) / 1e8
                        print(f'Expected Amount Out: {expected_amount_out}')
                        print(f'Outbound Fee: {outbound_fee}')
                        print('')

    except Exception as err:
        print(f"processCreateOpportunityThorchainOnBlock error {err}")
        traceback.print_exc()


balances = initBalance()
block = getBlock()
poolData = getThorchainPool()
print(f'BLOCK : {block}')
# print(poolData)
updateThorchainAssetPoolData(balances=balances, poolData=poolData, currentBlock=1)

processCreateOpportunityThorchainOnBlock(balances, block)