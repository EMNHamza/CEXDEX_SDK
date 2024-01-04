import requests
import logging
import time

from constantes.url import URL_BLOCK_THOR, URL_DEPOSIT_THOR, URL_POOL_THOR, URL_NODE_THOR, URL_MIMIR_THOR, URL_INBOUND_ADD_THOR, URL_BLOCK_THOR_NEW
from typing import Dict, List
from constantes.myAddresses import MY_ADDRESS
from classes.Asset import AssetThorchain
from classes.Opportunity import OpportunityCexDex, OpportunityThorchain, OpportunityDexDex
from utilsThorchain.thorchainUtils import formattedBalancesData


def getThorchainBalances():
    
    try:
        
        URL_BALANCE_THOR = f"{URL_NODE_THOR}:1317/bank/balances/{MY_ADDRESS}"
        responseBalanceThor = requests.get(url=URL_BALANCE_THOR, timeout=1).json()

        newDictBalancesFormatted = formattedBalancesData(balancesData=responseBalanceThor["result"])
        # print(f'getThorchainBalances - newDictBalancesFormatted {newDictBalancesFormatted}')
    except Exception as err:
        logging.warning(f'getThorchainBalance - error getting data from {URL_NODE_THOR} {err}')
        newDictBalancesFormatted = {}
    
    return newDictBalancesFormatted


def depositJS(amount: int, asset: str, memo: str):
    print("depositJS", amount, asset)
    try:
        urlDeposit = f"{URL_DEPOSIT_THOR}amount1={amount}&asset1={asset}&memo1={memo}"
        responseDeposit = requests.get(url=urlDeposit, timeout=2)
    except Exception as err:
        logging.warning(f'depositJS - error getting data from {URL_NODE_THOR} : {err}')
    return responseDeposit


def getThorchainPool() -> Dict:
    try:
        responsePool = requests.get(url=URL_POOL_THOR, timeout=1).json()
    except Exception as err:
        logging.warning(f'getPool - error getting data from {URL_NODE_THOR}')
    return responsePool


def getBlock():
    try:
        block = requests.get(url=URL_BLOCK_THOR_NEW, timeout=1).json()[0]["thorchain"]

    except Exception as err:
        logging.warning(f'getBlock - error getting data from {URL_NODE_THOR}')

    return block


def executeThorchainOpportunity(opportunity):
    if isinstance(opportunity, OpportunityCexDex):
        opp = opportunity.opportunityThorchain
        bybitPrice = opportunity.opportunityBybit.bybitAssetPrice
        gainEstimated = opportunity.gainTotalEstimated
        if opp.pairAsset.assetIn.assetType == 'STABLE':
            limitOrderValue = str(int((opp.amountOutEstimated) - (gainEstimated/bybitPrice)*10**opp.pairAsset.assetOut.decimals))
        else:
            limitOrderValue = str(int((opp.amountOutEstimated) - gainEstimated*10**opp.pairAsset.assetOut.decimals))
        
    if isinstance(opportunity, OpportunityThorchain):
        opp = opportunity
        limitOrderValue = str(int(opportunity.amountIn) * (10**opportunity.pairAsset.assetOut.decimals / 10**opportunity.pairAsset.assetOut.decimals))


    if isinstance(opportunity, OpportunityDexDex):
        opp = opportunity.opportunityThorchain
        limitOrderValue = str(1)

    txHash = depositJS(
        amount=int(opp.amountIn),
        asset=str(opp.pairAsset.assetIn.memoName),
        memo=f"=:{opp.pairAsset.assetOut.memoName}:{MY_ADDRESS}:{limitOrderValue}",
    )

    return txHash


def checkThorchainTxStatus(txHash):
    txHash = txHash.replace('"', '')
    urlTx = f"http://192.248.157.141:1317/thorchain/tx/{txHash}/signers"
    memoOut = ''
    isSuccess = False
    max_retries = 1500  # Set a maximum number of retries
    retries = 0

    t1 = time.perf_counter()
    while retries < max_retries:
        try:
            responseTx = requests.get(urlTx)
            if responseTx.status_code == 200:
                responseTx = responseTx.json()
                
                if 'out_txs' in responseTx and responseTx["out_txs"]:
                    memoOut = responseTx["out_txs"][0]["memo"]
                    if "OUT:" in memoOut or "REFUND:" in memoOut:
                        break
        except Exception as err:
            logging.warning(f'error : {err} for {txHash}')
        finally:
            retries += 1  # Ensure the retries counter is incremented.
            time.sleep(0.5)  # Wait a second before the next try.

    t2 = time.perf_counter()
    logging.info(f'Time to find tx status: {t2 - t1}')

    if "OUT:" in memoOut:
        isSuccess = True

    logging.info(f'txHash {txHash} isSuccess ? {isSuccess}')

    return isSuccess


def swapThorchain(
    address: str, amount: int, assetIn: AssetThorchain, assetOut: AssetThorchain, limitOrderValue: int
):
    # assetOut = changeNameAsset(dict=dictAssetNameToAssetMemoName, asset=assetOut)
    amount = int(amount)
    # if assetIn.memoName == 'THOR.RUNE':
    #     assetIn.memoName = 'THOR/RUNE'
    print("swap", assetIn.memoName, assetOut.memoName, amount)
    txhash = depositJS(
        amount=amount,
        asset=assetIn.memoName,
        memo=f"=:{assetOut.memoName}:{address}:{limitOrderValue}",
    )
    return txhash


def isChainHaltedOnThorchain(chain: str) -> bool:
    responseMimir = requests.get(URL_MIMIR_THOR).json()
    responseInbound = requests.get(URL_INBOUND_ADD_THOR).json()

    chain = chain.upper()
    keyChain = "HALT" + str(chain) + "CHAIN"
    keyTrading = "HALT" + str(chain) + "TRADING"
    keySolvency = "SOLVENCYHALT" + str(chain) + "CHAIN"

    isHalted = False

    if responseMimir["HALTTHORCHAIN"] == 1 or responseMimir["HALTTRADING"] == 1:
        logging.warning(f"THORCHAIN is halted")
        isHalted = True
        return isHalted

    if keyChain in responseMimir and keyTrading in responseMimir:
        if responseMimir[keyChain] == 1 or responseMimir[keyTrading] == 1:
            logging.warning(f"{chain} is halted - responseMimir")
            isHalted = True
            return isHalted
    
    if keySolvency in responseMimir:
        if responseMimir[keySolvency] == 1:
            logging.warning(f"{chain} is halted - responseMimir")
            isHalted = True
            return isHalted          

    for chainInbound in responseInbound:
        if chainInbound["chain"].upper() == chain:
            if (
                chainInbound["global_trading_paused"] == True
                or chainInbound["halted"] == True
                or chainInbound["chain_trading_paused"] == True
            ):
                logging.warning(f"{chain} is halted - response Inbound")
                isHalted = True
                return isHalted

    isHalted = False
    return isHalted


def removeChainHaltedOnThorchain(listAssets: List):
    newAssetList = []
    for asset in listAssets:
        try:
            isHalted = isChainHaltedOnThorchain(asset.chain)
        except Exception as e:
            # Log the exception and skip to the next asset
            logging.error(f"Error checking if {asset.chain} is halted: {e}")
            continue  # Skip this asset and continue with the next

        if not isHalted:
            newAssetList.append(asset)
        else:
            logging.warning(f"{asset.chain} is Halted - {asset.symbol} removed")

    listAssets = newAssetList

    return listAssets




# def estimateSwapThorchain(
#     amountIn: float, assetIn: Asset, assetOut: Asset, responsePool
# ) -> float:
#     poolIn = Pool(
#         asset=assetIn,
#         balanceAssetInPool=1,
#         balanceRuneInPoolAsset=1,
#         synthSupplyRemaining=1,
#         status="",
#     )
#     poolOut = Pool(
#         asset=assetOut,
#         balanceAssetInPool=1,
#         balanceRuneInPoolAsset=1,
#         synthSupplyRemaining=1,
#         status="",
#     )

#     poolIn = poolIn.checkBalancePool(responseGetPool=responsePool)
#     poolOut = poolOut.checkBalancePool(responseGetPool=responsePool)

#     amountOut = formulaDoubleSwapOutput(
#         amountIn=amountIn,
#         poolIn=poolIn,
#         poolOut=poolOut,
#         isSynthSwapIn=True,
#         isSynthSwapOut=True,
#         synthMultiplier=1,
#     )
#     lastFees = getValueOfRuneInAsset(
#         amount=0.02, asset=assetOut, responsePool=responsePool
#     )
#     lastFees = lastFees * 1e8
#     amountOutFinal = amountOut - lastFees
#     print("lastFees", lastFees)
#     print("amountOutFinal", amountOutFinal)

#     return amountOutFinal
