import logging
import traceback
import requests
import time
import math
from concurrent.futures import ThreadPoolExecutor
from utilsBybit.bybit_utils import api_key, secret_key
from BOT_THORCHAIN_BYBIT_REFONTE.tools.utilsCsv import writeInCSV
from utilsBybit.bybit_utils import getSymbolList, getBybitBalances
from BOT_THORCHAIN_BYBIT_REFONTE.tools.utilsOpportunity import executeThorchainOpportunity, createOpportunity
from utilsBybit.bybit_price_calculation import orderbook_average_price
from pybit.unified_trading import WebSocket
from logging.handlers import RotatingFileHandler
from tools.myUtils import removeChainHalted, getAllPath
from thorchainUtils.thorchainCalcul import formulaGetSwapFee, formulaSwapOutput, getValueOfRuneInAsset, simulePool, getValueInDollars
from thorchainUtils.thorchainInteraction import getPool
from constantes.url import URL_BLOCK_THOR
from tools.init import initBalance
from datetime import datetime
from utilsBybit.bybit_utils import getSymbol, isSell, place_order
from classes.OpportunityCexDex import OpportunityCexDex
from classes.Opportunity import OpportunityBybit
from classes.OpportunityThorchain import OpportunityThorchain
from classes.Pool import Pool
from classes.Pair import PairAsset, PairCexDex
from multiprocessing import Process, Queue, Manager
from typing import Dict, List
from collections import deque
from _logs.log_config import setup_logging



# def createPairs(balances):
#     all_assets = {}
#     for balance_type in [balances.balancesThorchain, balances.balancesBybit, balances.balancesMaya]:
#         for asset_type, assets in balance_type.assets.items():
#             all_assets.setdefault(asset_type, []).extend(assets)

#     pairs = []
#     for asset_type, assets in all_assets.items():
#         for assetIn in assets:
#             for assetOut in assets:
#                 if assetIn.poolName.upper() != assetOut.poolName.upper():
#                     pair = PairAsset(assetIn=assetIn, assetOut=assetOut)
#                     pairs.append(pair)
 

def createPairsForBalanceType(listAssets):
    pairs = []
    for assetIn in listAssets:
        for assetOut in listAssets:
            if assetIn.symbol != assetOut.symbol:
                pairAsset = PairAsset(assetIn=assetIn, assetOut=assetOut)
                pairs.append(pairAsset)
    return pairs

                

def createPairsCexDex(pairsCex, pairsDex):
    pairsCexDex = []
    for pairCex in pairsCex:
        for pairDex in pairsDex:
            if pairCex.assetIn.assetType == pairDex.assetOut.assetType and pairCex.assetOut.assetType == pairDex.assetIn.assetType:
                pairCexDex = PairCexDex(pairAssetCex=pairCex, pairAssetDex=pairDex)
                pairsCexDex.append(pairCexDex)
    return pairsCexDex
 

def formulaDoubleSwapOutputNet(
    amountIn: int,
    poolIn: Pool,
    poolOut: Pool,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    synthMultiplier=1,
) -> float:

    fee_swap1 = formulaGetSwapFee(True, poolIn, amountIn, isSynthSwapOut)

    amountAssetInToRune = formulaSwapOutput(
        True, poolIn, amountIn, isSynthSwapIn, synthMultiplier
    ) - fee_swap1

    fee_swap2 = formulaGetSwapFee(False, poolOut, amountAssetInToRune, isSynthSwapOut)

    amountOut = formulaSwapOutput(
        False, poolOut, amountAssetInToRune, isSynthSwapOut, synthMultiplier
    ) - fee_swap2

    return amountOut


def formulaGainInStable(amountIn: int, poolIn: Pool, poolOut: Pool, isSynthSwapIn: bool, isSynthSwapOut: bool, orderbookData: Dict, synthMultiplier=1):
    amountOutNet = formulaDoubleSwapOutputNet(amountIn=amountIn, poolIn=poolIn, poolOut=poolOut, isSynthSwapIn=isSynthSwapIn, isSynthSwapOut=isSynthSwapOut)
    # amountOutNet = amountOutNet / 1e8
    # amountIn = amountIn / 1e8

    if "BTC" in poolIn.asset:

        priceBTC = orderbook_average_price(orderbook_data=orderbookData, amount=amountIn/1e8, is_btc_sell=True)

        amountInInStable = amountIn * priceBTC
        gainInStable = amountOutNet - amountInInStable
        # logging.info(f'priceBTC poolIn {priceBTC} amount to convert : {amountIn/1e8} BTC - amountInStable : {amountInInStable/1e8} - Gain in Stable {gainInStable/1e8}')

    if "BTC" in poolOut.asset:
        priceBTC = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutNet, is_btc_sell=False)
        amountOutInStable = amountOutNet * priceBTC
        gainInStable = amountOutInStable - amountIn
        # logging.info(f'priceBTC poolOut {priceBTC} amount to convert : {amountIn/1e8} STABLE - amountOutInStable : {amountOutInStable/1e8} - Gain in Stable {gainInStable/1e8}')

    return gainInStable


def scoutOpportunityCexDex(listOpportunities: List):
    listSuccessOpportunities = []
    opportunity: OpportunityCexDex
    for opportunity in listOpportunities:
        if opportunity.gainNetEstimated > 0:
            listSuccessOpportunities.append(opportunity)

    return listSuccessOpportunities


def checkTxStatus(txHash):
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


def calculateGainOpportunityCexDex(opportunityCexDex, isEstimated):

    priceBTC = opportunityCexDex.opportunityBybit.bybitAssetPrice

    if isEstimated == True:
        amountInBybit = opportunityCexDex.opportunityBybit.amountInEstimated
        amountOutBybit = opportunityCexDex.opportunityBybit.amountOutEstimated
        amountInThorchain = opportunityCexDex.opportunityThorchain.amountIn/1e8
        amountOutThorchain = opportunityCexDex.opportunityThorchain.amountOutEstimated/1e8
    else:
        amountInBybit = opportunityCexDex.opportunityBybit.amountInReal
        amountOutBybit = opportunityCexDex.opportunityBybit.amountOutReal
        amountInThorchain = opportunityCexDex.opportunityThorchain.amountIn/1e8
        amountOutThorchain = opportunityCexDex.opportunityThorchain.amountOutReal/1e8

    if opportunityCexDex.opportunityThorchain.assetIn.type == 'BTC':

        gainBTC = amountOutBybit - amountInThorchain
        gainStable = amountOutThorchain - amountInBybit

        gainBTCInSTABLE = gainBTC * priceBTC

        gainTotalNetInStable = gainBTCInSTABLE + gainStable

    else:

        gainStable = amountOutBybit - amountInThorchain
        gainBTC = amountOutThorchain - amountInBybit

        gainBTCInSTABLE = gainBTC * priceBTC

        gainTotalNetInStable = gainStable + gainBTCInSTABLE

    # gainNetStableEstimated, gainNetStableReal, gainNetAssetEstimated, gainNetAssetReal, gainTotalEstimated, gainTotalReal

    if isEstimated == True:
        opportunityCexDex.gainNetStableEstimated = gainStable
        opportunityCexDex.gainNetAssetEstimated = gainBTC
        opportunityCexDex.gainTotalEstimated = gainTotalNetInStable
    else:
        opportunityCexDex.gainNetStableReal = gainStable
        opportunityCexDex.gainNetAssetReal = gainBTC
        opportunityCexDex.gainTotalReal = gainTotalNetInStable

    return opportunityCexDex


# def update_orderbook_data(data):
#     orderbookDataShared.update(data)
#     # logging.info(f'processOrderbookBybit - orderbookDataShared {orderbookDataShared}')


# def handle_orderbook(message):
#     # I will be called every time there is new orderbook data!
#     data = message["data"]
#     update_orderbook_data(data)


def dichotomie(
    f,
    low,
    high,
    e,
    poolIn: Pool,
    poolOut: Pool,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    orderbookData: Dict
) -> int:
    mid = 0
    while high - low > e:
        mid = int((high + low) / 2)
        p1 = int(low + (high - low) / 4)
        p2 = int(low + 3 * (high - low) / 4)
        if f(p1, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, orderbookData) > f(
            mid, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, orderbookData
        ):
            high = mid
        elif f(mid, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, orderbookData) < f(
            p2, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, orderbookData
        ):
            low = mid
        else:
            low = p1
            high = p2

    return (mid, f(mid, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, orderbookData))


def createThorchainOpportunity(
    poolData: Dict, assetIn: float, assetOut: float, amountInMax: float, typeOpp: str, orderbookData: Dict
):

    poolIn = Pool(
        asset=assetIn.poolName,
        balanceAssetInPool=1,
        balanceRuneInPoolAsset=1,
        synthSupplyRemaining=1,
        status="",
    )
    poolOut = Pool(
        asset=assetOut.poolName,
        balanceAssetInPool=1,
        balanceRuneInPoolAsset=1,
        synthSupplyRemaining=1,
        status="",
    )

    poolIn = poolIn.checkBalancePool(responseGetPool=poolData)
    poolOut = poolOut.checkBalancePool(responseGetPool=poolData)

    if poolOut.status == "Available":
        (amountInOpti, gainNetInStable) = dichotomie(
            f=formulaGainInStable,
            low=0,
            high=int(amountInMax),
            e=1,
            poolIn=poolIn,
            poolOut=poolOut,
            isSynthSwapIn=True,
            isSynthSwapOut=True,
            orderbookData=orderbookData
        )

        amountOutNet = formulaDoubleSwapOutputNet(amountIn=amountInOpti, poolIn=poolIn, poolOut=poolOut, isSynthSwapIn=True, isSynthSwapOut=True)

        if amountOutNet < poolOut.synthSupplyRemaining:
            totalOutboundFees = getValueOfRuneInAsset(
                amount=0.02 * 1e8, asset=assetOut, responsePool=poolData
            )

            amountInInDollars = getValueInDollars(amount=amountInOpti, asset=assetIn, responsePool=poolData)
            # logging.info(f'Opp : amountInOpti {amountInOpti} gainNetInAssetOut {gainNetInAssetOut}')
            # logging.info(f'Opp : gainNetInDollars {gainNetInDollars/1e8}, gainNetInAsset {gainNetInAssetOut/1e8}, assetIn {assetIn.name}, assetOut {assetOut.name}, amountIn {amountIn}, amountOut {amountOut}, ')

            newOpp = OpportunityThorchain(
                assetIn=assetIn,
                assetOut=assetOut,
                amountIn=amountInOpti,
                amountInInDollars=amountInInDollars,
                amountOutEstimated=amountOutNet,
                amountOutReal=0,
                typeOpp=typeOpp,
                outboundFees=totalOutboundFees,
                txHash=''
            )

        else:
            logging.warning(
                f"synthSupplyRemaining too low for {poolOut.asset}, amountOpti {amountInOpti} and SynthSupplyRemaining {poolOut.synthSupplyRemaining}"
            )
    else:
        logging.warning(
            f"amountIn NULL or pool disable, amountIN {amountInOpti} poolStatus {poolOut.status}"
        )

    return newOpp


def createBybitOpportunity(opportunityThorchain: OpportunityThorchain, orderbookData: Dict, dictMyAssets: Dict):
    # assetIn, assetOut, amountIn, amountOutEstimated, amountOutReal, gainNetInStableEstimated, gainNetInStableReal, typeOpp

    amountIn = opportunityThorchain.amountOutEstimated / 1e8
    amountInRounded = math.floor(amountIn*10**5)/10**5

    for listAsset in dictMyAssets.values():
        for asset in listAsset:
            if asset.poolName == "BTC.BTC":
                assetBTC = asset
            if asset.poolName == "ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48":
                assetUSDC = asset

    if opportunityThorchain.assetIn.type == 'STABLE':
        assetIn = assetBTC
        assetOut = assetUSDC
        priceBTC = orderbook_average_price(orderbook_data=orderbookData, amount=amountIn, is_btc_sell=True)
        amountOutEstimated = amountIn * priceBTC

    if opportunityThorchain.assetIn.type == 'BTC':
        assetIn = assetUSDC
        assetOut = assetBTC
        priceBTC = orderbook_average_price(orderbook_data=orderbookData, amount=amountIn, is_btc_sell=False)
        amountOutEstimated = amountIn / priceBTC

    opportunityBybit = OpportunityBybit(assetIn=assetIn, assetOut=assetOut, amountInEstimated=amountInRounded, bybitAssetPrice=priceBTC, amountInReal=0, amountOutEstimated=amountOutEstimated, amountOutReal=0, typeOpp="Bybit", orderId='')

    return opportunityBybit


def createOpportunityCexDex(opportunityThorchain: OpportunityThorchain, opportunityBybit: OpportunityBybit):

    opportunityCexDex = OpportunityCexDex(opportunityThorchain=opportunityThorchain, opportunityBybit=opportunityBybit, gainNetStableEstimated=0, gainNetStableReal=0, gainNetAssetEstimated=0, gainNetAssetReal=0, gainTotalEstimated=0, gainTotalReal=0)

    opportunityCexDex = calculateGainOpportunityCexDex(opportunityCexDex=opportunityCexDex, isEstimated=True)

    return opportunityCexDex


def getAmountOutRealFromTxThorchain(txHash: str):
    txHash = txHash.replace('"', '')
    urlTx = f"http://192.248.157.141:1317/thorchain/tx/{txHash}/signers"
    try:
        responseTx = requests.get(urlTx)
        if responseTx.status_code == 200:
            responseTx = responseTx.json()
            # if 'out_txs' in responseTx:
            amountOutReal = int(responseTx["out_txs"][0]["coins"][0]["amount"])
        else:
            logging.warning(f"Failed to fetch data: Status code {responseTx.status_code} {responseTx.text}")
    except Exception as err:
        logging.warning(f'error : {err} for {txHash}')

    return amountOutReal


def executeBybitOpportunity(opportunity, symbol_list):
    try:
        asset_in_symbol = opportunity.opportunityBybit.assetIn.bybitAssetSymbol
        asset_out_symbol = opportunity.opportunityBybit.assetOut.bybitAssetSymbol
        amount = float(opportunity.opportunityBybit.amountInEstimated)
        pair_symbol = getSymbol(asset_in_symbol, asset_out_symbol, symbol_list)
        is_buy = isSell(asset_in_symbol, asset_out_symbol, pair_symbol)
        amount_in, amount_out, order_id = place_order(pair_symbol, is_buy, amount, httpClient)
        opportunity.opportunityBybit.amountInReal = float(amount_in)
        opportunity.opportunityBybit.amountOutReal = float(amount_out)
        opportunity.opportunityBybit.orderId = order_id

    except Exception as e:
        logging.warning(f"Erreur lors de l'execution de la transaction Bybit' : {e}")


def writeDataOppCexDex(opportunityCexDex: OpportunityCexDex, isTxThorchainSuccess: bool):

    current_datetime = datetime.now()
    formatted_date = current_datetime.date().strftime("%Y-%m-%d")
    formatted_time = current_datetime.time().strftime("%H:%M:%S")

    opportunityCexDex.opportunityThorchain.amountOutReal = getAmountOutRealFromTxThorchain(opportunityCexDex.opportunityThorchain.txHash)
    opportunityCexDex.gainNetReal = calculateGainOpportunityCexDex(opportunityCexDex=opportunityCexDex, isEstimated=False)

    txStatus = ""
    if isTxThorchainSuccess == True:
        txStatus = 'OK'
    else:
        txStatus = 'REVERTED'
        opportunityCexDex.gainNetStableReal = 0
        opportunityCexDex.gainNetAssetReal = 0

        if opportunityCexDex.opportunityThorchain.assetIn.type == 'STABLE':
            feesRune = (opportunityCexDex.opportunityThorchain.outboundFees * opportunityCexDex.opportunityBybit.bybitAssetPrice)
            opportunityCexDex.gainTotalReal = (opportunityCexDex.opportunityThorchain.amountOutReal - opportunityCexDex.opportunityThorchain.amountIn - feesRune)/1e8
        else:
            gainTotalReal = opportunityCexDex.opportunityThorchain.amountOutReal - opportunityCexDex.opportunityThorchain.amountIn
            opportunityCexDex.gainTotalReal = (gainTotalReal * opportunityCexDex.opportunityBybit.bybitAssetPrice)/1e8 - opportunityCexDex.opportunityThorchain.outboundFees / 1e8

    rowToAdd = [formatted_date, formatted_time, txStatus, opportunityCexDex.opportunityThorchain.txHash, opportunityCexDex.opportunityThorchain.detectedBlock, opportunityCexDex.opportunityThorchain.assetIn.symbol, opportunityCexDex.opportunityThorchain.assetOut.symbol, (opportunityCexDex.opportunityThorchain.amountIn/1e8), opportunityCexDex.opportunityThorchain.amountOutEstimated/1e8,
                opportunityCexDex.opportunityThorchain.amountOutReal/1e8, opportunityCexDex.opportunityBybit.orderId, opportunityCexDex.opportunityBybit.assetIn.bybitAssetSymbol, opportunityCexDex.opportunityBybit.assetOut.bybitAssetSymbol, opportunityCexDex.opportunityBybit.amountInEstimated, opportunityCexDex.opportunityBybit.amountInReal, opportunityCexDex.opportunityBybit.amountOutEstimated, opportunityCexDex.opportunityBybit.amountOutReal, opportunityCexDex.gainNetStableEstimated, opportunityCexDex.gainNetStableReal, opportunityCexDex.gainNetAssetEstimated, opportunityCexDex.gainNetAssetReal, opportunityCexDex.gainTotalEstimated, opportunityCexDex.gainTotalReal]

    writeInCSV(fileName='csv/dataOppCexDex.csv', rowToAdd=rowToAdd)


def updateAssetBybitBalance(dictAsset, bybitBalances):
    # dictNewAsset = {}
    # dictNewAsset = dictAsset

    for listAssets in dictAsset.values():
        for asset in listAssets:
            if asset.type == 'BTC':
                asset.myBalanceBybit = float(bybitBalances['BTC'])

            if asset.type == 'STABLE':
                asset.myBalanceBybit = float(bybitBalances['USDC'])

    return dictAsset


def getGain1000(opportunityCexDex: OpportunityCexDex):
    gainEstimated = opportunityCexDex.gainTotalEstimated
    assetPrice = opportunityCexDex.opportunityBybit.bybitAssetPrice
    amountInDollarsValue = getAmountInValue(opportunityCexDex)
    if amountInDollarsValue < 3:
        gainEstimated1000 = 0
    else:
        gainEstimated1000 = (gainEstimated / amountInDollarsValue) * 1000
    return gainEstimated1000


def getAmountInValue(opportunityCexDex: OpportunityCexDex):
    assetPrice = opportunityCexDex.opportunityBybit.bybitAssetPrice
    if opportunityCexDex.opportunityThorchain.assetIn.type == 'STABLE':
        amountInDollarsValue = opportunityCexDex.opportunityThorchain.amountIn/1e8
    else:
        amountInDollarsValue = opportunityCexDex.opportunityThorchain.amountIn * assetPrice / 1e8
    return amountInDollarsValue


def getAmountInMax(firstPair, secondPair, orderbookDataShared):
    priceAssetOutInAssetIn = orderbook_average_price(orderbook_data=orderbookDataShared, amount=secondPair.assetIn.balance/10**secondPair.assetIn.decimals, is_btc_sell=True)
    balanceAssetInSecondPairConvertToAssetInFirstPair = priceAssetOutInAssetIn * (secondPair.assetIn.balance /10**secondPair.assetIn.decimals)
    amountInMax = min(balanceAssetInSecondPairConvertToAssetInFirstPair, (firstPair.assetIn.balance/10**firstPair.assetIn.decimals)) * 0.99
    return amountInMax


# def selectOpportunities(listOpportunities: List, poolData: Dict, orderbook,balance):
#     sorted_opportunities = sortOpportunities(listOpportunities)
#     updated_orderbook=orderbook
#     updated_pool_data=poolData
#     updated_balance=balance
#     selected_opportunities=[]
#     for opportunity in sorted_opportunities:
#         # Simuler l'exécution de l'opportunité
#         simulation = simulate_execution(opportunity, updated_pool_data, updated_orderbook, updated_balance)

#         if simulation:
#             # Mettre à jour les données de pool et orderbook
#             updated_pool_data=update_pool_data(opportunity, poolData)
#             updated_orderbook=update_orderbook(opportunity,orderbook)
#             updated_balance=update_balance(opportunity, balance)
#             selected_opportunities.append(opportunity)

#     return selected_opportunities


def simulate_execution(opportunity, poolData, updated_orderbook):

    return


def sortOpportunities(listOpportunities):
    def get_sort_key(opportunity):
        if isinstance(opportunity, OpportunityThorchain):
            return opportunity.amountIn
        elif isinstance(opportunity, OpportunityCexDex):
            return opportunity.opportunityThorchain.amountIn
        else:
            raise TypeError("Objet inconnu dans la liste des opportunités")

    sorted_opportunities = sorted(listOpportunities, key=get_sort_key)
    return sorted_opportunities


def threadExecuteOpportunity(opportunity: OpportunityCexDex, symbol_list: List):

    try:
        logging.info(f'threadExecuteOpportunity starting')
        txHash = executeThorchainOpportunity(opportunityCexDex=opportunity)
        opportunity.opportunityThorchain.txHash = txHash.text
        logging.info(f'checking txStatus loading... {opportunity.opportunityThorchain.txHash}')
        isTxThorchainSuccess = checkTxStatus(txHash=opportunity.opportunityThorchain.txHash)
        if isTxThorchainSuccess == True:
            executeBybitOpportunity(opportunity=opportunity, symbol_list=symbol_list)
        logging.info(f'threadExecuteOpportunity completed for : txHash : {opportunity.opportunityThorchain.txHash} orderID : {opportunity.opportunityBybit.orderId}')

        writeDataOppCexDex(opportunityCexDex=opportunity, isTxThorchainSuccess=isTxThorchainSuccess)

    except Exception as err:
        logging.warning(f"processCreateOpportunityCexDex error {err}")
        # traceback.print_exc()



# def processGetBalances(dictMyAssetsShared: Dict, dictMyAssets: Dict):
#     while True:
#         try:

#             bybitBalances = getBybitBalances()
#             initBalanceThorchain(dictMyAssets)
#             dictMyAssets = updateAssetBybitBalance(dictAsset=dictMyAssets, bybitBalances=bybitBalances)
#             dictMyAssets = removeChainHalted(dictMyAssets=dictMyAssets)
#             dictMyAssetsShared.update(dictMyAssets)

#             # for listAssets in dictMyAssetsShared.values():
#             #     for asset in listAssets:
#             #         logging.info(f'processGetBalances - dictMyAssetsShared - asset.symbol {asset.symbol} asset.bybitAssetSymbol {asset.bybitAssetSymbol} asset.myBalanceThorhchain {asset.myBalanceThorchain} asset.myBalanceBybit {asset.myBalanceBybit}')

#             time.sleep(0.5)
#         except Exception as err:
#             logging.warning(f"processGetBalances error {err}")
#             # traceback.print_exc()


# def processOrderbookBybit():
#     ws_private = WebSocket(
#         testnet=False,
#         channel_type="spot",
#         api_key=api_key,
#         api_secret=secret_key,
#         ping_interval=20,
#         ping_timeout=10,
#         retries=20,
#         restart_on_error=True,
#         trace_logging=False,
#     )

#     ws_private.orderbook_stream(50, "BTCUSDC", handle_orderbook)

#     while True:
#         time.sleep(1)


def processGetBlock(slidingListBlock, queueBlock: Queue, poolDataShared: Dict) -> List[int]:
    while True:
        try:
            block = requests.get(url=URL_BLOCK_THOR, timeout=1).json()[
                "result"]["sync_info"]["latest_block_height"]
            slidingListBlock.append(int(block))

            lastBlock = int(slidingListBlock[-2])
            currentBlock = int(slidingListBlock[-1])

            responseInfoNode = requests.get(
                url=URL_BLOCK_THOR, timeout=1).json()

            catchingUpNode = responseInfoNode["result"]["sync_info"]["catching_up"]

            if catchingUpNode == True:
                logging.warning("processGetBlock - catching up true")
                continue

            if currentBlock > lastBlock and catchingUpNode == False:
                responsePool = getPool()
                poolDataShared[:] = responsePool
                queueBlock.put(currentBlock)
        except Exception as err:
            logging.warning(f"processGetBlock error {err}")
            # traceback.print_exc()


# def processCreateOpportunityCexDex(queueBlock: Queue, queueOpportunities: Queue, poolDataShared: Dict, dictMyAssetsShared: Dict, orderbookDataShared: Dict):
#     while True:
#         try:
#             currentBlock = queueBlock.get()

#             logging.info(f'processCreateOpportunityCexDex - currentBlock {currentBlock}')

#             listSuccessCexDexOpportunities = []

#             pairsThorchain = createPairsForBalanceType(listAssets=balances.balancesThorchain.listAssets)
#             pairsBybit = createPairsForBalanceType(listAssets=balances.balancesBybit.listAssets)
#             pairsCexDex = createPairsCexDex(pairsDex=pairsThorchain, pairsCex=pairsBybit)

#             for pairCexDex in pairsCexDex:

#                 amountInMax = getAmountInMax(pairCexDex.pairThorchain, pairCexDex.pairBybit)

#                 if pairCexDex.pairDex.assetIn.balance > 100:

#                     opportunity = createThorchainOpportunity(
#                         poolData=poolDataShared,
#                         assetIn=pairCexDex.pairDex.assetIn,
#                         assetOut=pairCexDex.pairDex.assetOut,
#                         amountInMax=int(amountInMax*10**pairCexDex.pairDex.assetIn.decimals),
#                         typeOpp="CexDex",
#                         orderbookData=orderbookDataShared
#                     )

#                 opportunity.detectedBlock = currentBlock
#                 opportunityBybit = createBybitOpportunity(opportunityThorchain=opportunity, orderbookData=orderbookDataShared, dictMyAssets=dictMyAssetsShared)
#                 opportunityCexDex = createOpportunityCexDex(opportunityThorchain=opportunity, opportunityBybit=opportunityBybit)
                
#                 conditionOpp = opportunityCexDex.gainTotalEstimated > 0.15 and getGain1000(opportunityCexDex) > 0.4
                
#                 if conditionOpp:
#                     logging.info(f'opportunityCexDex :  gainTotalEstimated {opportunityCexDex.gainTotalEstimated}, gain1000 {getGain1000(opportunityCexDex)}, amout in value in dollars {getAmountInValue(opportunityCexDex)}')
#                     print("y'a une opp fréro")
#                     logging.info(f'')
#                     logging.info(
#                         f'opportunityThorchain : assetIn : {opportunity.assetIn.symbol} assetOut : {opportunity.assetOut.symbol} amountIn : {opportunity.amountIn/1e8} amountOutEstimated {opportunity.amountOutEstimated/1e8} block : {opportunity.detectedBlock}')
#                     logging.info(
#                         f'opportunityBybit : assetIn : {opportunityBybit.assetIn.bybitAssetSymbol} assetOut : {opportunityBybit.assetOut.bybitAssetSymbol} amountInEstimated : {opportunityBybit.amountInEstimated} amountOutEstimated {opportunityBybit.amountOutEstimated} bybitAssetPrice {opportunityBybit.bybitAssetPrice}')
#                     logging.info(f'opportunityCexDex :  gainTotalEstimated {opportunityCexDex.gainTotalEstimated}, gainNetStableEstimated {opportunityCexDex.gainNetStableEstimated}, gainNetAssetEstimated {opportunityCexDex.gainNetAssetEstimated}')
#                     logging.info(f'')
#                     listSuccessCexDexOpportunities.append(opportunityCexDex)

#             if listSuccessCexDexOpportunities:
#                 best_opportunity = max(listSuccessCexDexOpportunities, key=lambda x: x.gainTotalEstimated)
#                 listSuccessCexDexOpportunities = [best_opportunity]

#                 queueOpportunities.put(best_opportunity)

#         except Exception as err:
#             logging.warning(f"processCreateOpportunityCexDex error {err}")


def processOpportunityConsumer(queueOpportunities: Queue, symbol_list: List):
    with ThreadPoolExecutor(max_workers=100) as executor:
        while True:
            try:

                opportunity = queueOpportunities.get()

                logging.info(f'processOpportunityConsumer starting for assetIn : {opportunity.opportunityThorchain.assetIn.balanceName} montant in : {opportunity.opportunityThorchain.amountIn}')
                executor.submit(threadExecuteOpportunity, opportunity, symbol_list)
                logging.info(f'processOpportunityConsumer ending for assetIn : {opportunity.opportunityThorchain.assetIn.balanceName} montant in : {opportunity.opportunityThorchain.amountIn}')
            except Exception as err:
                logging.warning(f"processOpportunityConsumer error {err}")
                # traceback.print_exc()


def processOnBlock(queueBlock:Queue, dictMyAssetsShared:Dict, poolDataShared:Dict,queueOpportunities:Queue):
    while True:
        try:
            currentBlock = queueBlock.get()
            
            listOpportunities = []
            allPath = getAllPath(dict=dictMyAssetsShared)
            for path in allPath:
                assetInPath = path.assetIn
                assetOutPath = path.assetOut
                if assetInPath.myBalance > 100:
                    opportunity = createOpportunity(
                        responsePool=poolDataShared,
                        assetIn=assetInPath,
                        assetOut=assetOutPath,
                        amountIn=int(assetInPath.myBalance),
                        typeOpp="onBlock",
                    )
                    listOpportunities.append(opportunity)
            
            listSuccessOpportunitiesOnBlock = []
            for opportunity in listOpportunities:
                opportunity.detectedBlock = currentBlock

                if opportunity.assetIn.type == 'STABLE':
                    gainNetInDollars = (opportunity.amountOutEstimated - opportunity.amountIn)/1e8
                else:
                    gainNetInAssetOut = (opportunity.amountOutEstimated - opportunity.amountIn)
                    gainNetInDollars = getValueInDollars(amount=gainNetInAssetOut,asset=opportunity.assetOut,responsePool=poolDataShared)
            
                if gainNetInDollars > 0.2:
                    listSuccessOpportunitiesOnBlock.append(opportunity)
                
            if listSuccessOpportunitiesOnBlock:
                queueOpportunities.put(listSuccessOpportunitiesOnBlock)
        
        except Exception as err:
            logging.warning(f"processOnBlock error {err}")
            # traceback.print_exc()



if __name__ == "__main__":
    httpClient = requests.Session()
    manager = Manager()

    # symbol_list = getSymbolList(httpClient)

    # slidingListBlock = deque(maxlen=3)
    # slidingListBlock.append(0)
    # slidingListBlock.append(0)
    # slidingListBlock.append(0)

    # queueBlockThorchain = Queue()
    # queueBlockMaya = Queue()
    # queueOpportunities = Queue()

    # poolThorchainDataShared = manager.list()
    # poolMayaDataShared = manager.list()
    # orderbookDataShared = manager.dict()
    BalancesShared = manager.Namespace()
    BalancesShared = initBalance()


    for asset in BalancesShared.balancesThorchain.listAssets:
        print(f'balancesThorchain - asset.symbol : {asset.symbol} - asset.balance {asset.balance}')
    
    for asset in BalancesShared.balancesBybit.listAssets:
        print(f'balancesBybit - asset.symbol : {asset.symbol} - asset.balance {asset.balance}')

    



# ----- 

    # processBalances = Process(target=processGetBalances, args=(BalancesShared))
    # processOrderbookProducer = Process(target=processOrderbookBybit, args=(orderbookDataShared))

    # processBlockThorchainProducer = Process(target=processGetBlock, args=(slidingListBlock, queueBlockThorchain, poolThorchainDataShared))
    # processBlockMayaProducer = Process(target=processGetBlock, args=(slidingListBlock, queueBlockMaya, poolMayaDataShared))

    # processOpportunityCexDexProducer = Process(target=processCreateOpportunityCexDex, args=(queueBlockThorchain, queueOpportunities, poolThorchainDataShared, BalancesShared, orderbookDataShared))
    # processOpportunityOnBlockThorchainProducer = Process(target=processOnBlock, args=(queueBlockThorchain, BalancesShared, queueOpportunities, poolThorchainDataShared))
    # processOpportunityOnBlockMayaProducer = Process(target=processOnBlock, args=(queueBlockMaya, BalancesShared, queueOpportunities, poolMayaDataShared))
    
    # processOpportunityConsumer_ = Process(target=processOpportunityConsumer, args=(queueOpportunities, symbol_list))

# ----- 

#     processBalances.start()
#     processOrderbookProducer.start()

#     processBlockThorchainProducer.start()
#     processBlockMayaProducer.start()

#     processOpportunityCexDexProducer.start()
#     processOpportunityOnBlockThorchainProducer.start()
#     processOpportunityOnBlockMayaProducer.start()

#     processOpportunityConsumer_.start()

# # ----- 

#     processBalances.join()
#     processOrderbookProducer.join()

#     processBlockThorchainProducer.join()
#     processBlockMayaProducer.join()

#     processOpportunityCexDexProducer.join()
#     processOpportunityOnBlockThorchainProducer.join()
#     processOpportunityOnBlockMayaProducer.join()

#     processOpportunityConsumer_.join()
