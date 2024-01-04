import requests
import logging
import time 

from constantes.url import URL_NODE_MAYA, URL_BALANCE_MAYA, URL_POOL_MAYA, URL_BLOCK_MAYA_NEW, URL_DEPOSIT_MAYA, URL_TX_DATA_MAYA, URL_MIMIR_MAYA, URL_INBOUND_ADD_MAYA
from constantes.myAddresses import MY_ADDRESS_MAYA
from constantes.constantes import DECIMALS_CACAO

from classes.Asset import AssetMaya
from classes.Opportunity import OpportunityMaya, OpportunityBybit, OpportunityCexDex, OpportunityDexDex
from classes.Balances import Balances, BalancesThorchain, BalancesBybit, BalancesMaya
from typing import Dict
from utilsThorchain.thorchainUtils import formattedBalancesData
from utilsMaya.mayaCalcul import getValueOfAssetInCacao, getValueOfCacaoInAsset

from copy import deepcopy

def getMayaBalances():
    try:
        url = f"{URL_BALANCE_MAYA}/{MY_ADDRESS_MAYA}"
        responseBalanceMaya = requests.get(url=url, timeout=1).json()
        newDictBalancesFormatted = formattedBalancesData(balancesData=responseBalanceMaya["result"])
    except Exception as err:
        logging.warning(f'getThorchainBalance - error getting data from {URL_NODE_MAYA} - {err}')
        newDictBalancesFormatted = {}
    
    return newDictBalancesFormatted


def getMayaPool() -> Dict:
    try:
        responsePool = requests.get(url=URL_POOL_MAYA, timeout=1).json()
    except Exception as err:
        logging.warning(f'getPool - error getting data from {URL_POOL_MAYA}')
    return responsePool


def getMayaBlock():
    try:
        block = int(requests.get(url=URL_BLOCK_MAYA_NEW, timeout=1).json()[0]["mayachain"])
    except Exception as err:
        logging.warning(f'getBlock - error getting data from {URL_BLOCK_MAYA_NEW}')

    return block


def checkMayaTxStatus(txHash):
    txHash = txHash.replace('"', '')
    urlTx = f"{URL_TX_DATA_MAYA}{txHash}/signers"
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
            logging.error(f'error : {err} for {txHash}')
        finally:
            retries += 1  # Ensure the retries counter is incremented.
            time.sleep(0.5)  # Wait a second before the next try.

    t2 = time.perf_counter()
    logging.info(f'Time to find tx maya status: {t2 - t1}')

    if "OUT:" in memoOut:
        isSuccess = True

    logging.info(f'maya txHash {txHash} isSuccess ? {isSuccess}')

    return isSuccess


def depositMayaJS(amount: int, asset: str, memo: str):
    print("depositMayaJS", amount, asset)
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
    memo = f"=:{assetOut.memoName}:{address}:{limitOrderValue}"
    print("swap", assetIn.memoName, assetOut.memoName, amount)
    
    txhash = depositMayaJS(
        amount=amount,
        asset=assetIn.memoName,
        memo=memo,
    )
    return txhash


def executeMayaOpportunity(opportunity):
    if isinstance(opportunity, OpportunityCexDex):
        opp = opportunity.opportunityThorchain
        bybitPrice = opportunity.opportunityBybit.bybitAssetPrice
        gainEstimated = opportunity.gainTotalEstimated
        if opp.pairAsset.assetIn.assetType == 'STABLE':
            limitOrderValue = str(int((opp.amountOutEstimated) - (gainEstimated/bybitPrice)*10**opp.pairAsset.assetOut.decimals))
        else:
            limitOrderValue = str(int((opp.amountOutEstimated) - gainEstimated*10**opp.pairAsset.assetOut.decimals))
        
    if isinstance(opportunity, OpportunityMaya):
        opp = opportunity
        limitOrderValue = str(int((opp.amountIn) * (10**opp.pairAsset.assetOut.decimals / 10**opp.pairAsset.assetOut.decimals)))

    if isinstance(opportunity, OpportunityDexDex):
        opp = opportunity.opportunityMaya

        assetInCopy = deepcopy(opportunity.opportunityMaya.pairAsset.assetIn)
        assetOutCopy = deepcopy(opportunity.opportunityMaya.pairAsset.assetOut)

        poolIn = assetInCopy.pool
        poolOut = assetOutCopy.pool

        poolIn.balanceAssetInPool = poolIn.balanceAssetInPool * 1e2
        poolOut.balanceAssetInPool = poolOut.balanceAssetInPool *1e2

        gainInCacao = getValueOfAssetInCacao(amount=opportunity.gainAssetInDexEstimated*10**DECIMALS_CACAO,pool=poolIn)
        gainInAssetOutMaya = getValueOfCacaoInAsset(amount=gainInCacao,pool=poolOut)

        limitOrderValue = str(int(opportunity.opportunityMaya.amountOutEstimated - gainInAssetOutMaya * 10**opportunity.opportunityMaya.pairAsset.assetOut.decimals / 10**DECIMALS_CACAO))
        logging.info(f'executeMayaOpportunity - OpportunityDexDex - limitOrderValue {limitOrderValue}')
        
    txHash = depositMayaJS(
        amount=int(opp.amountIn),
        asset=str(opp.pairAsset.assetIn.memoName),
        memo=f"=:{opp.pairAsset.assetOut.memoName}:{MY_ADDRESS_MAYA}:{limitOrderValue}",
    )

    return txHash


def isChainHaltedOnMaya(chain: str) -> bool:
    responseMimir = requests.get(URL_MIMIR_MAYA).json()
    responseInbound = requests.get(URL_INBOUND_ADD_MAYA).json()

    chain = chain.upper()
    keyChain = "HALT" + str(chain) + "CHAIN"
    keyTrading = "HALT" + str(chain) + "TRADING"
    keySolvency = "SOLVENCYHALT" + str(chain) + "CHAIN"

    isHalted = False
    
    # if chain == 'THOR':
    #     isHalted = True
    #     return isHalted 
    

    if responseMimir["HALTTHORCHAIN"] == 1 or responseMimir["HALTTRADING"] == 1 or responseMimir["HALTTHORTRADING"] == 1 or responseMimir["HALTSIGNINGTHOR"] == 1:
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


def removeChainHaltedOnMaya(listAssets):


    # listAssetsMaya = createAssetsFromJSON(AssetMaya)
    # balancesMaya = BalancesMaya(listAssets=updateAssetBalances(listAssetsMaya,balancesDataMaya))

    newAssetList = []
    for asset in listAssets:
        try:
            isHalted = isChainHaltedOnMaya(asset.chain)
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


# def isChainHaltedThorchain(chain: str) -> bool:
#     responseMimir = requests.get(URL_MIMIR_THOR).json()
#     responseInbound = requests.get(URL_INBOUND_ADD_THOR).json()

#     chain = chain.upper()
#     keyChain = "HALT" + str(chain) + "CHAIN"
#     keyTrading = "HALT" + str(chain) + "TRADING"
#     keySolvency = "SOLVENCYHALT" + str(chain) + "CHAIN"

#     isHalted = False

#     if responseMimir["HALTTHORCHAIN"] == 1 or responseMimir["HALTTRADING"] == 1:
#         logging.warning(f"THORCHAIN is halted")
#         isHalted = True
#         return isHalted

#     if keyChain in responseMimir and keyTrading in responseMimir:
#         if responseMimir[keyChain] == 1 or responseMimir[keyTrading] == 1:
#             logging.warning(f"{chain} is halted - responseMimir")
#             isHalted = True
#             return isHalted

#     if keySolvency in responseMimir:
#         if responseMimir[keySolvency] == 1:
#             logging.warning(
#                 f"{keySolvency} solvency is halted - responseMimir")
#             isHalted = True
#             return isHalted

#     for chainInbound in responseInbound:
#         if chainInbound["chain"].upper() == chain:
#             if chainInbound["global_trading_paused"] == True or chainInbound["halted"] == True or chainInbound['chain_trading_paused'] == True:
#                 logging.warning(f"{chain} is halted - response Inbound")
#                 isHalted = True
#                 return isHalted

#     isHalted = False
#     return isHalted


# def removeChainHalted(dictMyAssets: Dict):

#     for key, assetList in dictMyAssets.items():
#         newAssetList = []
#         for asset in assetList:
#             try:
#                 isHalted = isChainHaltedThorchain(asset.chain)
#             except Exception as e:
#                 # Log the exception and skip to the next asset
#                 logging.error(f'Error checking if {asset.chain} is halted: {e}')
#                 continue  # Skip this asset and continue with the next

#             # if asset.chain == 'BNB':
#             #     isHalted = True

#             if not isHalted:
#                 newAssetList.append(asset)
#             else:
#                 logging.warning(
#                     f'{asset.chain} is Halted - {asset.name} removed')

#         dictMyAssets[key] = newAssetList

#     return dictMyAssets


# def executeThorchainOpportunity(opportunityCexDex):
#     opp = opportunityCexDex.opportunityThorchain
#     bybitPrice = opportunityCexDex.opportunityBybit.bybitAssetPrice
#     gainEstimated = opportunityCexDex.gainTotalEstimated
#     if opp.assetIn.type == 'STABLE':
#         limitOrderValue = str(int((opp.amountOutEstimated) - (gainEstimated/bybitPrice)*1e8))
#     else:
#         limitOrderValue = str(int((opp.amountOutEstimated) - gainEstimated*1e8))

#     txHash = depositJS(
#         amount=int(opp.amountIn),
#         asset=str(opp.assetIn.memoName),
#         memo=f"=:{opp.assetOut.memoName}:{MY_ADDRESS}:{limitOrderValue}",
#     )

#     return txHash
