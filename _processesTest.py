import logging
import traceback
import requests
import time
import math
import datetime 

from _logs.log_config import setup_logging

from utilsBybit.bybit_utils import (
    api_key,
    secret_key,
    createBybitOpportunityForThorchain,
    orderbook_average_price,
    isSell,
    findMatchingBybitAsset,
    getSymbol
)

from constantes.constantes import (
    THRESHOLD_GAIN_NET,
    MINIMUM_BALANCE_TO_SCOUT,
    THRESHOLD_GAIN1000_NET,
    THRESHOLD_ONBLOCK_GAIN_NET,
    THRESHOLD_ONBLOCK_GAIN1000_NET,
    DECIMALS_CACAO,
    THRESHOLD_GAIN1000_NET_MAYA,
    THRESHOLD_GAIN_NET_MAYA
)

from tools.myUtils import (
    updateBalances,
    createPairsForBalanceType,
    getAmountInMax,
    getAmountInMaxSynthOnBlock,
    getAmountInMaxCexDex,
    getGain1000CexDex,
    getGain1000OnBlock,
    getGain1000DexDex,
    getAmountInValue,
    updateAllBalances,
    getOrderedOpportunities,
    getFilteredOpportunities,
    getFilteredOpportunitiesPerAsset,
    updateBalancesObjectWithBalanceDict,
    fetchPoolData,
    updateAssetPoolData,
    updateBalanceDictWithSingleOpp,
    updateBalanceDictWithDoubleOpp,
    get_balance_value
)
from tools.utilsCEXDEX import createPairsCexDex, createOpportunityCexDex
from tools.utilsBalanceTampon import updateBalanceTampon, updateBalancesObject, newUpdateBalanceTampon, isOppPossible, adjustBalanceWithBuffer
from constantes.url import URL_BLOCK_THOR, URL_BLOCK_MAYA

from utilsThorchain.thorchainCalcul import (
    getValueInDollarsThorchain,
    createThorchainSynthOnBlockOpportunity,
    createThorchainOpportunityForBybit,
    getThorchainWalletValue,
    createThorchainOpportunityForBybitScout,
    getValueOfDollarsInAssetThorchain,
    dichotomieCexDexLog,
    formulaGainStableCexDex,
    createThorchainOpportunityForMaya
)
from utilsThorchain.thorchainInteraction import (
    getThorchainPool,
    executeThorchainOpportunity,
    checkThorchainTxStatus,
    removeChainHaltedOnThorchain
)
from utilsThorchain.thorchainUtils import (
    updateThorchainAssetPoolData,
    updateDexAssetPoolData,
)

from utilsMaya.mayaInteraction import getMayaPool, getMayaBlock, removeChainHaltedOnMaya
from utilsMaya.mayaCalcul import createMayaSynthOnBlockOpportunity, createMayaOpportunityForBybit, createMayaOpportunityForThorchain
from utilsMaya.mayaUtils import updateMayaAssetPoolData

from classes.Opportunity import (
    OpportunityThorchain,
    OpportunityCexDex,
    OpportunityBybit,
    OpportunityMaya,
    OpportunityDexDex
)
from classes.Pair import PairCexDex
from classes.Balances import Balances

from multiprocessing import Process, Queue, Manager, Event, Lock
from typing import Dict, List
from copy import deepcopy

from opportunityExecution import (
    executeCexDexOpportunity,
    executeThorchainOnBlockOpportunity,
    executeMayaCexDexOpportunity,
    executeMayaOnBlockOpportunity,
    executeMayaThorOpportunity
)

from tools.utilsMAYATHOR import createPairsDexDex, createOpportunityDexDex, getAmountInMaxDexDex
from tools.init import initBalanceNull, initBalanceDict
 


def processUpdateDict(balanceDict:Dict,lock:Lock,sharedCounter):
    while True:
        
        time.sleep(20*60)
        logging.info(f'processUpdateDict running')
        
        start_time = None  # Initialize start_time

        while True:
            if sharedCounter.value == 0:
                if start_time is None:
                    logging.info(f'processUpdateDict - start_time is None {sharedCounter.value}')
                    start_time = time.time()  # Start timing when counter hits 0
                elif time.time() - start_time >= 60:  # Check if 1 minute has passed
                    logging.info(f'processUpdateDict - time.time() - start_time {time.time() - start_time} s')
                    break  # Exit loop if counter has been 0 for 1 minute
            else:
                logging.warning(f'processUpdateDict - sharedCounter = {sharedCounter.value}')
                start_time = None  # Reset timer if counter is not 0

            time.sleep(10)  
        

        newBalanceDict = initBalanceDict()

        with lock:
            balanceDictCopy = deepcopy(balanceDict)
            for platform, assets in newBalanceDict.items():
                for balanceName, newValue in assets.items():
                    oldValue = balanceDictCopy[platform].get(balanceName)
                    if oldValue != newValue:
                        balanceDictCopy[platform][balanceName] = newValue
                        if oldValue is not None:
                            logging.info(f"processUpdateDict - Updating '{platform}' -> '{balanceName}' from {oldValue} to {newValue}")
                        else:
                            logging.info(f"processUpdateDict - Adding new pool '{balanceName}' to '{platform}' with value {newValue}")
            balanceDict.update(balanceDictCopy)
            
        if balanceDict['THORCHAIN']['rune'] /1e8 < 1:
            logging.warning(f"processUpdateDict - RUNE GAS FEE TOO LOW : {balanceDict['THORCHAIN']['rune']}")
        if balanceDict['MAYA']['cacao'] /1e8 < 5:
            logging.warning(f"processUpdateDict - CACAO GAS FEE TOO LOW : {balanceDict['MAYA']['cacao']}")




def processGetThorchainBlock(
    tenderminBlock,
    poolData,
    BalancesShared: Balances,
    orderbookDataShared: Dict,
    queueOpportunitiesThorchain: Queue,
    queueOpportunitiesToExecute: Queue,
    balanceDictShared:Dict, 
    poolDictShared:Dict
):
    try:
        BalancesShared = initBalanceNull()

        responseInfoNode = requests.get(url=URL_BLOCK_THOR, timeout=1).json()
        catchingUpNode = responseInfoNode["result"]["sync_info"]["catching_up"]


        if catchingUpNode == True:
            logging.warning("new TC - processGetThorchainBlock - catching up true")


        if catchingUpNode == False:

            BalancesShared.balancesThorchain.listAssets = removeChainHaltedOnThorchain(
                listAssets=BalancesShared.balancesThorchain.listAssets
            )
            
            logging.info(f'new TC - balanceDictShared before SCOUT : {balanceDictShared}')

            updateBalancesObjectWithBalanceDict(balances=BalancesShared, balanceDict=balanceDictShared)
                        
            fetchPoolData(poolDataShared=poolDictShared,block=tenderminBlock,pool=poolData,listAssets=BalancesShared.balancesThorchain.listAssets)
            
            updateAssetPoolData(balances=BalancesShared,poolData=poolDictShared, type='THORCHAIN')


            for asset in BalancesShared.balancesThorchain.listAssets:
                if asset.assetType != "RUNE":
                    logging.info(
                        f"new TC - processGetThorchainBlock - balancesThorchain currentBlock {tenderminBlock} - asset.symbol : {asset.symbol} - asset.balance {asset.balance} asset.pool.balanceAssetInPool {asset.pool.balanceAssetInPool} asset.pool.balanceRuneInPoolAsset {asset.pool.balanceRuneInPoolAsset}"
                    )


            launchThorchainProcesses(
                BalancesShared,
                orderbookDataShared,
                queueOpportunitiesThorchain,
                queueOpportunitiesToExecute
            )

    except Exception as err:
        logging.warning(f"processGetThorBlock error: {type(err).__name__}, {str(err)}")
        traceback.print_exc()


# def processGetMayaBlock(slidingListBlock, BalancesShared:Balances, orderbookDataShared:Dict, queueOpportunitiesMaya:Queue, queueOpportunitiesToExecute:Queue, balanceDictShared:Dict, poolDictShared:Dict):
#     while True:
#         try:
#             BalancesShared = initBalanceNull()
#             block = getMayaBlock()
#             slidingListBlock.append(int(block))

#             lastBlock = int(slidingListBlock[-2])
#             currentBlock = int(slidingListBlock[-1])

#             responseInfoNode = requests.get(
#                 url=URL_BLOCK_MAYA, timeout=1).json()

#             catchingUpNode = responseInfoNode["result"]["sync_info"]["catching_up"]

#             if catchingUpNode == True:
#                 logging.warning("processGetMayaBlock - catching up true")
#                 time.sleep(10)
#                 continue

#             if currentBlock > lastBlock and catchingUpNode == False:
#                 poolData = getMayaPool()

#                 BalancesShared.balancesMaya.listAssets = removeChainHaltedOnMaya(
#                     listAssets=BalancesShared.balancesMaya.listAssets
#                 )
                    
#                 logging.info(f'balanceDictShared before SCOUT : {balanceDictShared}')

#                 updateBalancesObjectWithBalanceDict(balances=BalancesShared, balanceDict=balanceDictShared)

#                 fetchPoolData(poolDataShared=poolDictShared,block=currentBlock,pool=poolData,listAssets=BalancesShared.balancesMaya.listAssets)
                
#                 updateAssetPoolData(balances=BalancesShared,poolData=poolDictShared, type="MAYA")
                
#                 for asset in BalancesShared.balancesMaya.listAssets:
#                     if asset.assetType != "CACAO":
#                         logging.info(
#                             f"processGetMayaBlock - balancesMaya currentBlock {currentBlock} - asset.symbol : {asset.symbol} - asset.balance {asset.balance} asset.pool.balanceAssetInPool {asset.pool.balanceAssetInPool} asset.pool.balanceCacaoInPoolAsset {asset.pool.balanceCacaoInPoolAsset}"
#                         )

#                 launchMayaProcesses(BalancesShared, orderbookDataShared, queueOpportunitiesMaya, queueOpportunitiesToExecute, poolDictShared)
                
            
#             time.sleep(0.1)

#         except Exception as err:
#             logging.warning(f'processGetMayaBlock error : {err}')
#             traceback.print_exc()


def processGetMayaBlock(tendermintBlock,poolData, BalancesShared:Balances, orderbookDataShared:Dict, queueOpportunitiesMaya:Queue, queueOpportunitiesToExecute:Queue, balanceDictShared:Dict, poolDictShared:Dict):
    try:
        
        BalancesShared = initBalanceNull()

        responseInfoNode = requests.get(
            url=URL_BLOCK_MAYA, timeout=1).json()

        catchingUpNode = responseInfoNode["result"]["sync_info"]["catching_up"]

        if catchingUpNode == True:
            logging.warning("processGetMayaBlock - catching up true")


        if catchingUpNode == False:

            BalancesShared.balancesMaya.listAssets = removeChainHaltedOnMaya(
                listAssets=BalancesShared.balancesMaya.listAssets
            )
                
            logging.info(f'new MayaBlock - balanceDictShared before SCOUT : {balanceDictShared}')

            updateBalancesObjectWithBalanceDict(balances=BalancesShared, balanceDict=balanceDictShared)

            fetchPoolData(poolDataShared=poolDictShared,block=tendermintBlock,pool=poolData,listAssets=BalancesShared.balancesMaya.listAssets)
            
            updateAssetPoolData(balances=BalancesShared,poolData=poolDictShared, type="MAYA")
            
            for asset in BalancesShared.balancesMaya.listAssets:
                if asset.assetType != "CACAO":
                    logging.info(
                        f"new MayaBlock - processGetMayaBlock - balancesMaya currentBlock {tendermintBlock} - asset.symbol : {asset.symbol} - asset.balance {asset.balance} asset.pool.balanceAssetInPool {asset.pool.balanceAssetInPool} asset.pool.balanceCacaoInPoolAsset {asset.pool.balanceCacaoInPoolAsset}"
                    )

            launchMayaProcesses(BalancesShared, orderbookDataShared, queueOpportunitiesMaya, queueOpportunitiesToExecute, poolDictShared)
            
        

    except Exception as err:
        logging.warning(f"processGetMayaBlock error: {type(err).__name__}, {str(err)}")
        traceback.print_exc()




def launchThorchainProcesses(
    BalancesShared: Balances,
    orderbookDataShared: Dict,
    queueOpportunitiesThorchain: Queue,
    queueOpportunitiesToExecute: Queue):
    
    eventScoutCexDexThorchain = Event()
    eventScoutOnblockThorchain = Event()

    processOpportunityThorchainVSBybitProducer = Process(
        target=processCreateOpportunityThorchainVSBybit,
        args=(
            BalancesShared,
            orderbookDataShared,
            queueOpportunitiesThorchain,
            eventScoutCexDexThorchain,
        ),
    )
    processOpportunityThorchainSynthOnBlockProducer = Process(
        target=processCreateOpportunityThorchainOnBlock,
        args=(
            BalancesShared,
            orderbookDataShared,
            queueOpportunitiesThorchain,
            eventScoutOnblockThorchain,
        ),
    )
    processSelectOpportunitiesThorchain_ = Process(
        target=processSelectOpportunitiesThorchain,
        args=(
            queueOpportunitiesThorchain,
            queueOpportunitiesToExecute,
            BalancesShared,
            orderbookDataShared,
            eventScoutCexDexThorchain,
            eventScoutOnblockThorchain,
        ),
    )

    processOpportunityThorchainVSBybitScout = Process(
        target=processScoutOpportunityThorchain,
        args=(
            BalancesShared,
            orderbookDataShared,
        ),
    )

    # Démarrage des processus
    processOpportunityThorchainVSBybitProducer.start()
    processOpportunityThorchainSynthOnBlockProducer.start()
    processSelectOpportunitiesThorchain_.start()
    processOpportunityThorchainVSBybitScout.start()


def launchMayaProcesses(BalancesShared: Balances, orderbookDataShared:Dict, queueOpportunitiesMaya:Queue, queueOpportunitiesToExecute:Queue, poolDictShared:Dict):
    eventScoutCexDexMaya = Event()
    eventScoutOnblockMaya = Event()
    eventScoutDexDex = Event()
    
    processOpportunityMayaVSBybitProducer = Process(target=processCreateOpportunityMayaVSBybit , args=(BalancesShared, orderbookDataShared,queueOpportunitiesMaya,eventScoutCexDexMaya))
    processOpportunityMayaSynthOnBlockProducer = Process(target=processCreateOpportunityMayaOnBlock, args=(BalancesShared,queueOpportunitiesMaya,eventScoutOnblockMaya))
    processSelectOpportunitiesMaya_ = Process(target=processSelectOpportunitiesMaya, args=(queueOpportunitiesMaya,queueOpportunitiesToExecute, BalancesShared, orderbookDataShared, eventScoutCexDexMaya, eventScoutOnblockMaya, eventScoutDexDex))
    processOpportunityMayaVSThorProducer = Process(target=processCreateOpportunityMayaVSThor, args=(BalancesShared,queueOpportunitiesMaya,eventScoutDexDex, poolDictShared))

    # Démarrage des processus
    processOpportunityMayaVSBybitProducer.start()
    processOpportunityMayaSynthOnBlockProducer.start()
    processSelectOpportunitiesMaya_.start()
    processOpportunityMayaVSThorProducer.start()




def processCreateOpportunityThorchainOnBlock(
    BalancesShared: Balances,
    orderbookDataShared: Dict,
    queueOpportunitiesThorchain: Queue,
    eventScoutOnblockThorchain: Event,
):
    try:
        pairsThorchain = createPairsForBalanceType(
            listAssets=BalancesShared.balancesThorchain.listAssets,
            orderbook=orderbookDataShared,
        )

        for pairThorchain in pairsThorchain:
            if pairThorchain.assetIn.assetType == pairThorchain.assetOut.assetType:
                if pairThorchain.assetIn.balance > 0:
                    amountInMax = getAmountInMaxSynthOnBlock(
                        pairThorchain, BalancesShared
                    )

                    opportunityThorchain = createThorchainSynthOnBlockOpportunity(
                        pairThorchain=pairThorchain,
                        amountIn=int(
                            amountInMax * 10**pairThorchain.assetIn.decimals
                        ),
                        typeOpp="THORCHAIN",
                        balancesThorchain=BalancesShared.balancesThorchain,
                    )
                    # logging.info(f"")
                    # logging.info(f'ONBLOCK - gainNetInDollars {opportunityThorchain.gainNetInDollars} $')
                    # logging.info(f'ONBLOCK - opp thorchain : amountIn {opportunityThorchain.amountIn/1e8} {opportunityThorchain.pairAsset.assetIn.symbol} amountOut {opportunityThorchain.amountOutEstimated/1e8} {opportunityThorchain.pairAsset.assetOut.symbol}')
                    # logging.info(f'ONBLOCK - opportunityThorchain.gainNetInDollars : {opportunityThorchain.gainTotalEstimated} $ , gain1000 {getGain1000OnBlock(opportunityThorchain)} $ , amountInInDollars : {opportunityThorchain.amountInInDollars} $')
                    # logging.info(f"")
                    if opportunityThorchain.amountInInDollars > 15:
                        # logging.info(f"")
                        # logging.info(f'ONBLOCK - gainNetInDollars {opportunityThorchain.gainNetInDollars} $')
                        # logging.info(f'ONBLOCK - opp thorchain : amountIn {opportunityThorchain.amountIn/1e8} {opportunityThorchain.pairAsset.assetIn.symbol} amountOut {opportunityThorchain.amountOutEstimated/1e8} {opportunityThorchain.pairAsset.assetOut.symbol}')
                        # logging.info(f'ONBLOCK - opportunityThorchain.gainNetInDollars : {opportunityThorchain.gainTotalEstimated} $ , gain1000 {getGain1000OnBlock(opportunityThorchain)} $ , amountInInDollars : {opportunityThorchain.amountInInDollars} $')
                        # logging.info(f"")
                        opportunityThorchain.detectedBlock = (
                            pairThorchain.assetIn.pool.block
                        )

                        if (
                            opportunityThorchain.gainNetInDollars
                            > THRESHOLD_ONBLOCK_GAIN_NET
                            and getGain1000OnBlock(opportunityThorchain)
                            > THRESHOLD_ONBLOCK_GAIN1000_NET
                        ):
                            
                            queueOpportunitiesThorchain.put(opportunityThorchain)
                            print(f"{datetime.datetime.now()} y'a une opp ONBLOCK THOR fréro block = {opportunityThorchain.detectedBlock}")

                            logging.info(f"")
                            logging.info(
                                f"ONBLOCK - processCreateOppOnBlock - opportunityThorchain : block : {opportunityThorchain.detectedBlock} - amountIn : {opportunityThorchain.amountIn/10**opportunityThorchain.pairAsset.assetIn.decimals} {opportunityThorchain.pairAsset.assetIn.symbol} - amountOutEstimated {opportunityThorchain.amountOutEstimated/10**opportunityThorchain.pairAsset.assetOut.decimals} {opportunityThorchain.pairAsset.assetOut.symbol}"
                            )
                            logging.info(
                                f"ONBLOCK - gainNetInDollars : {round(opportunityThorchain.gainTotalEstimated,3)} $, gain1000 {getGain1000OnBlock(opportunityThorchain)} $, amountInInDollars : {opportunityThorchain.amountInInDollars} $"
                            )
                            logging.info(f"")

    except Exception as err:
        logging.warning(f"processCreateOpportunityThorchainOnBlock error {err}")
        traceback.print_exc()

    finally:
        eventScoutOnblockThorchain.set()  
  

def processCreateOpportunityThorchainVSBybit(
    balancesShared: Balances,
    orderbookDataShared: Dict,
    queueOpportunitiesThorchain: Queue,
    eventScoutCexDexThorchain: Event,
):
    try:
        balancesDex = balancesShared.balancesThorchain
        balancesCex = balancesShared.balancesBybit
        pairsDex = createPairsForBalanceType(
            listAssets=balancesDex.listAssets, orderbook=orderbookDataShared
        )
        pairsCex = createPairsForBalanceType(
            listAssets=balancesCex.listAssets, orderbook=orderbookDataShared
        )
        pairsCexDex = createPairsCexDex(pairsDex=pairsDex, pairsCex=pairsCex)

        for pairCexDex in pairsCexDex:
            if pairCexDex.pairAssetDex.assetIn.balance > 0 and pairCexDex.pairAssetCex.assetIn.balance > 0:
                amountInMax = getAmountInMaxCexDex(
                    pairCexDex.pairAssetDex, pairCexDex.pairAssetCex, balancesShared
                    )

                opportunityThorchain = createThorchainOpportunityForBybit(
                    pairThorchain=pairCexDex.pairAssetDex,
                    amountInMax=int(
                        amountInMax * 10**pairCexDex.pairAssetDex.assetIn.decimals
                    ),
                    typeOpp="THORCHAIN",
                    orderbookData=pairCexDex.pairAssetCex.orderbook,
                    balancesThorchain=balancesDex,
                )

                # logging.info(f"")
                # logging.info(f'CEXDEX - opp thorchain : assetIn : {opportunityThorchain.pairAsset.assetIn.symbol} assetOut : {opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opportunityThorchain.amountIn/1e8} amountOut {opportunityThorchain.amountOutEstimated/1e8}')
                # logging.info(f'CEXDEX - opp bybit : assetIn : {opportunityCexDex.opportunityBybit.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityBybit.pairAsset.assetOut.symbol} amountIn : {opportunityCexDex.opportunityBybit.amountInEstimated} amountOut : {opportunityCexDex.opportunityBybit.amountOutEstimated} ')
                # logging.info(f'CEXDEX - gainTotalEstimated {opportunityCexDex.gainTotalEstimated} $, gain1000 {getGain1000CexDex(opportunityCexDex)}, amountInInDollars : {opportunityCexDex.opportunityThorchain.amountInInDollars}')
                # logging.info(f"")
                        
                if opportunityThorchain.amountInInDollars > 15:
                    opportunityThorchain.detectedBlock = (
                        pairCexDex.pairAssetDex.assetIn.pool.block
                    )
                    
                    opportunityBybit = createBybitOpportunityForThorchain(
                        opportunityThorchain=opportunityThorchain,
                        orderbookData=orderbookDataShared,
                        balances=balancesShared,
                    )
                    
                    opportunityCexDex = createOpportunityCexDex(
                        pairCexDex=pairCexDex,
                        opportunityThorchain=opportunityThorchain,
                        opportunityBybit=opportunityBybit,
                    )
                    # logging.info(f"")
                    # logging.info(f'CEXDEX - opp thorchain : assetIn : {opportunityCexDex.opportunityThorchain.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opportunityCexDex.opportunityThorchain.amountIn/1e8} amountOut {opportunityCexDex.opportunityThorchain.amountOutEstimated/1e8}')
                    # logging.info(f'CEXDEX - opp bybit : assetIn : {opportunityCexDex.opportunityBybit.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityBybit.pairAsset.assetOut.symbol} amountIn : {opportunityCexDex.opportunityBybit.amountInEstimated} amountOut : {opportunityCexDex.opportunityBybit.amountOutEstimated} ')
                    # logging.info(f'CEXDEX - gainTotalEstimated {opportunityCexDex.gainTotalEstimated} $, gain1000 {getGain1000CexDex(opportunityCexDex)}, amountInInDollars : {opportunityCexDex.opportunityThorchain.amountInInDollars}')
                    # logging.info(f"")

                    conditionOpp = (
                        opportunityCexDex.gainTotalEstimated > THRESHOLD_GAIN_NET
                        and getGain1000CexDex(opportunityCexDex)
                        > THRESHOLD_GAIN1000_NET
                    )

                    if conditionOpp:
                        print(f"{datetime.datetime.now()} y'a une opp CEXDEX THOR fréro block = {opportunityThorchain.detectedBlock}")
                        logging.info(f"")
                        logging.info(
                            f"CEXDEX - opportunityCexDex :  gainTotalEstimated {opportunityCexDex.gainTotalEstimated}, gain1000 {getGain1000CexDex(opportunityCexDex)}, amount in value in dollars {getAmountInValue(opportunityCexDex)}"
                        )
                        logging.info(
                            f"CEXDEX - processCreateOppTCvsBybit - opportunityThorchain : block : {opportunityThorchain.detectedBlock} - amountIn : {opportunityThorchain.amountIn/10**opportunityThorchain.pairAsset.assetIn.decimals} {opportunityThorchain.pairAsset.assetIn.symbol} - amountOutEstimated {opportunityThorchain.amountOutEstimated/10**opportunityThorchain.pairAsset.assetOut.decimals} {opportunityThorchain.pairAsset.assetOut.symbol}"
                        )
                        logging.info(
                            f"CEXDEX - opportunityBybit : amountInEstimated : {opportunityBybit.amountInEstimated} {opportunityBybit.pairAsset.assetIn.symbol} amountOutEstimated {opportunityBybit.amountOutEstimated} {opportunityBybit.pairAsset.assetOut.symbol} bybitAssetPrice {opportunityBybit.bybitAssetPrice}"
                        )
                        logging.info(
                            f"opportunityCexDex :  gainTotalEstimated {round(opportunityCexDex.gainTotalEstimated,3)}, gainAssetInDexEstimated {opportunityCexDex.gainAssetInDexEstimated}, gainAssetOutDexEstimated {opportunityCexDex.gainAssetOutDexEstimated}"
                        )
                        logging.info(f"")
                        queueOpportunitiesThorchain.put(opportunityCexDex)

    except Exception as err:
        logging.warning(f"processCreateOpportunityThorchainVSBybit error {err}")
        traceback.print_exc()

    finally:
        eventScoutCexDexThorchain.set()


def processCreateOpportunityMayaOnBlock(BalancesShared:Balances, queueOpportunitiesMaya:Queue, eventScoutOnblockMaya:Event):
    try:
        
        pairsMaya = createPairsForBalanceType(listAssets=BalancesShared.balancesMaya.listAssets, orderbook='')
            
        for pairMaya in pairsMaya:
            if pairMaya.assetIn.assetType == pairMaya.assetOut.assetType:
                if pairMaya.assetIn.balance > 0:
                    amountIn = (pairMaya.assetIn.balance * 10**DECIMALS_CACAO / 10**pairMaya.assetIn.decimals)
                    opportunityMaya = createMayaSynthOnBlockOpportunity(
                        pairMaya=pairMaya,
                        amountIn=amountIn,
                        typeOpp="MAYA",
                        balancesMaya=BalancesShared.balancesMaya
                    )            
                    # logging.info(f"")
                    # logging.info(f'ONBLOCK MAYA - opportunityMaya - amountIn {opportunityMaya.amountIn/ 10**pairMaya.assetIn.decimals} {opportunityMaya.pairAsset.assetIn.symbol} amountOutEstimated {opportunityMaya.amountOutEstimated/ 10**pairMaya.assetOut.decimals} {opportunityMaya.pairAsset.assetOut.symbol} outboundFees {opportunityMaya.outboundFees/ 10**pairMaya.assetOut.decimals} slipFees {opportunityMaya.slipFees/ 10**pairMaya.assetOut.decimals} {opportunityMaya.pairAsset.assetOut.symbol}')
                    # logging.info(f'ONBLOCK MAYA : gainTotalEstimated = {round((opportunityMaya.amountOutEstimated-opportunityMaya.amountIn)/10**pairMaya.assetIn.decimals,2)} $')
                    # logging.info(f"")
                                    
                    opportunityMaya.detectedBlock = pairMaya.assetIn.pool.block
                    if opportunityMaya.amountInInDollars > 15:
                        # logging.info(f"")
                        # logging.info(f'ONBLOCK MAYA - opportunityMaya - amountIn {opportunityMaya.amountIn/ 10**pairMaya.assetIn.decimals} {opportunityMaya.pairAsset.assetIn.symbol} amountOutEstimated {opportunityMaya.amountOutEstimated/ 10**pairMaya.assetOut.decimals} {opportunityMaya.pairAsset.assetOut.symbol} outboundFees {opportunityMaya.outboundFees/ 10**pairMaya.assetOut.decimals} slipFees {opportunityMaya.slipFees/ 10**pairMaya.assetOut.decimals} {opportunityMaya.pairAsset.assetOut.symbol}')
                        # logging.info(f'ONBLOCK MAYA : gainTotalEstimated = {round((opportunityMaya.amountOutEstimated-opportunityMaya.amountIn)/10**pairMaya.assetIn.decimals,2)} $')
                        # logging.info(f"")
                        conditionOpp = opportunityMaya.gainNetInDollars > THRESHOLD_GAIN_NET_MAYA and getGain1000OnBlock(opportunityMaya) > THRESHOLD_GAIN1000_NET_MAYA
                    
                        if conditionOpp:
                            print(f"{datetime.datetime.now()} y'a une opp ONBLOCK MAYA fréro block = {opportunityMaya.detectedBlock}")
                            logging.info(f'ONBLOCK - OPP GAGNANTE - gainNetInDollars {round(opportunityMaya.gainNetInDollars,2)} $ - opportunityMaya.detectedBlock {opportunityMaya.detectedBlock} THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA}')    
                            queueOpportunitiesMaya.put(opportunityMaya)

    except Exception as err:
        logging.error(f"processCreateOpportunityMayaOnBlock error {err}")
        traceback.print_exc()

    finally:
        eventScoutOnblockMaya.set()  


def processCreateOpportunityMayaVSBybit(balancesShared : Balances, orderbookDataShared: Dict, queueOpportunitiesMaya:Queue, eventScoutCexDexMaya:Event):
    try:
        
        balancesDex = balancesShared.balancesMaya
        balancesCex = balancesShared.balancesBybit
        pairsDex = createPairsForBalanceType(listAssets=balancesDex.listAssets, orderbook=orderbookDataShared)
        pairsCex = createPairsForBalanceType(listAssets=balancesCex.listAssets, orderbook=orderbookDataShared)
        pairsCexDex = createPairsCexDex(pairsDex=pairsDex, pairsCex=pairsCex)

        for pairCexDex in pairsCexDex:
            amountInMax = getAmountInMax(pairCexDex.pairAssetDex, pairCexDex.pairAssetCex)
            if pairCexDex.pairAssetDex.assetIn.balance > 0:
                    # logging.info(f' CEXDEXMAYA - amountInMax {amountInMax} assetIn {pairCexDex.pairAssetDex.assetIn.symbol} assetOut {pairCexDex.pairAssetDex.assetOut.symbol}')
                    opportunityMaya = createMayaOpportunityForBybit(
                        pairMaya=pairCexDex.pairAssetDex,
                        amountIn=int(amountInMax*10**DECIMALS_CACAO),
                        typeOpp="MAYA",
                        orderbookData=pairCexDex.pairAssetCex.orderbook,
                        balancesMaya=balancesDex
                    )   

                    # logging.info(f'CEXDEXMAYA - opportunityMaya - amountIn {opportunityMaya.amountIn/ 10**pairCexDex.pairAssetDex.assetIn.decimals} {opportunityMaya.pairAsset.assetIn.symbol} amountOutEstimated {opportunityMaya.amountOutEstimated/ 10**pairCexDex.pairAssetDex.assetOut.decimals} {opportunityMaya.pairAsset.assetOut.symbol} outboundFees {opportunityMaya.outboundFees/ 10**pairCexDex.pairAssetDex.assetOut.decimals} slipFees {opportunityMaya.slipFees} {opportunityMaya.pairAsset.assetOut.symbol}')

                    if opportunityMaya.amountInInDollars > 15.0:
                        opportunityMaya.detectedBlock = pairCexDex.pairAssetDex.assetIn.pool.block
                        opportunityBybit = createBybitOpportunityForThorchain(opportunityThorchain=opportunityMaya, orderbookData=orderbookDataShared, balances=balancesShared)
                        opportunityCexDex = createOpportunityCexDex(pairCexDex=pairCexDex, opportunityThorchain=opportunityMaya, opportunityBybit=opportunityBybit)
                        
                        conditionOpp = opportunityCexDex.gainTotalEstimated > THRESHOLD_GAIN_NET_MAYA and getGain1000CexDex(opportunityCexDex) > THRESHOLD_GAIN1000_NET_MAYA
                        if conditionOpp:
                            print(f"{datetime.datetime.now()} y'a une opp CEXDEX MAYA fréro block = {opportunityMaya.detectedBlock}")
                            logging.info(f'OB BYBIT : orderbookDataShared {orderbookDataShared}')
                            logging.info(f'CEXDEXMAYA - opportunityMaya - amountIn {opportunityMaya.amountIn/ 10**pairCexDex.pairAssetDex.assetIn.decimals} {opportunityMaya.pairAsset.assetIn.symbol} amountOutEstimated {opportunityMaya.amountOutEstimated/ 10**pairCexDex.pairAssetDex.assetOut.decimals} {opportunityMaya.pairAsset.assetOut.symbol} outboundFees {opportunityMaya.outboundFees/ 10**pairCexDex.pairAssetDex.assetOut.decimals} slipFees {opportunityMaya.slipFees} {opportunityMaya.pairAsset.assetOut.symbol}')
                            logging.info(f'CEXDEXMAYA - opportunityBybit - amountIn {opportunityBybit.amountInEstimated} {opportunityBybit.pairAsset.assetIn.symbol} amountOutEstimated {opportunityBybit.amountOutEstimated} {opportunityBybit.pairAsset.assetOut.symbol}')
                            logging.info(f'CEXDEXMAYA - OPP GAGNANTE - gainTotalEstimated {round(opportunityCexDex.gainTotalEstimated,2)} $ - opportunityMaya.detectedBlock {opportunityMaya.detectedBlock} THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} $ - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA} $')    
                            queueOpportunitiesMaya.put(opportunityCexDex)
        
    except Exception as err:
        logging.info(f"processCreateOpportunityMayaVSBybit error {err}")
        traceback.print_exc()
    finally:
        eventScoutCexDexMaya.set()


def processScoutOpportunityThorchain(
    balancesShared: Balances,
    orderbookDataShared: Dict,
):
    try:
        balancesDex = balancesShared.balancesThorchain
        balancesCex = balancesShared.balancesBybit
        pairsDex = createPairsForBalanceType(
            listAssets=balancesDex.listAssets, orderbook=orderbookDataShared
        )
        pairsCex = createPairsForBalanceType(
            listAssets=balancesCex.listAssets, orderbook=orderbookDataShared
        )
        pairsCexDex = createPairsCexDex(pairsDex=pairsDex, pairsCex=pairsCex)

        for pairCexDex in pairsCexDex:
            if pairCexDex.pairAssetDex.assetIn.balance > 0 and pairCexDex.pairAssetCex.assetIn.balance > 0:
                for i in range(100): 
                    amountIn = 100*i
                    amountInInAsset = getValueOfDollarsInAssetThorchain(amount=amountIn * 10**pairCexDex.pairAssetDex.assetIn.decimals,asset=pairCexDex.pairAssetDex.assetIn,balancesThorchain=balancesShared.balancesThorchain)

                    # assetIn = findMatchingBybitAsset(balancesShared, pairCexDex.pairAssetDex.assetIn.assetType)
                    # assetOut = findMatchingBybitAsset(balancesShared, pairCexDex.pairAssetDex.assetOut.assetType)
                    # # logging.info(f'TEST PRIX : assetIn {assetIn.symbol} to assetOut {assetOut.symbol}')
                    # isSellOnBybit_ = isSell(
                    #     symbolIn=assetIn.symbol,
                    #     symbolOut=assetOut.symbol,
                    # )
                    # pairSymbol = getSymbol(assetIn.symbol,assetOut.symbol)
                    # priceTest = orderbook_average_price(orderbook_data=orderbookDataShared[pairSymbol], amount=amountInInAsset/1e8,  isSell=isSellOnBybit_)
                    # logging.info(f'TEST PRIX : amountIn = amountInInAsset {amountInInAsset/1e8} {assetIn.symbol} to assetOut {assetOut.symbol} - priceTest {priceTest} for isSell = {isSellOnBybit_}')

                    opportunityThorchain = createThorchainOpportunityForBybitScout(
                        pairThorchain=pairCexDex.pairAssetDex,
                        amountIn=int(amountInInAsset),
                        typeOpp="THORCHAIN",
                        orderbookData=pairCexDex.pairAssetCex.orderbook,
                        balancesThorchain=balancesDex,
                    )

                    if opportunityThorchain.pairAsset.assetIn.balance > amountInInAsset:
                        opportunityThorchain.detectedBlock = (
                            pairCexDex.pairAssetDex.assetIn.pool.block
                        )
                        
                        # logging.info(f'CREATEBYBITOPP SCOUT START')
                        opportunityBybit = createBybitOpportunityForThorchain(
                            opportunityThorchain=opportunityThorchain,
                            orderbookData=orderbookDataShared,
                            balances=balancesShared,
                        )
                        # logging.info(f'CREATEBYBITOPP SCOUT END')
                        opportunityCexDex = createOpportunityCexDex(
                            pairCexDex=pairCexDex,
                            opportunityThorchain=opportunityThorchain,
                            opportunityBybit=opportunityBybit,
                        )


                        # if opportunityCexDex.gainTotalEstimated > 0.05:
                        #     logging.info(f'SCOUT CEXDEX - opp thorchain : assetIn : {opportunityCexDex.opportunityThorchain.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opportunityCexDex.opportunityThorchain.amountIn/1e8} amountOut {opportunityCexDex.opportunityThorchain.amountOutEstimated/1e8}')
                        #     logging.info(f'SCOUT CEXDEX - opp bybit : assetIn : {opportunityCexDex.opportunityBybit.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityBybit.pairAsset.assetOut.symbol} amountIn : {opportunityCexDex.opportunityBybit.amountInEstimated} amountOut : {opportunityCexDex.opportunityBybit.amountOutEstimated} ')
                        #     logging.info(f'SCOUT CEXDEX - gainTotalEstimated {opportunityCexDex.gainTotalEstimated} $, gain1000 {getGain1000CexDex(opportunityCexDex)}, amountInInDollars : {opportunityCexDex.opportunityThorchain.amountInInDollars}')

                        # if(opportunityCexDex.gainTotalEstimated > 0):
                        #     logging.info(f'CEXDEX - opp thorchain : assetIn : {opportunityCexDex.opportunityThorchain.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opportunityCexDex.opportunityThorchain.amountIn} amountOut {opportunityCexDex.opportunityThorchain.amountOutEstimated}')
                        #     logging.info(f'CEXDEX - opp bybit : assetIn : {opportunityCexDex.opportunityBybit.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityBybit.pairAsset.assetOut.symbol} amountIn : {opportunityCexDex.opportunityBybit.amountInEstimated} amountOut : {opportunityCexDex.opportunityBybit.amountOutEstimated} ')
                        #     logging.info(f'CEXDEX - gainTotalEstimated {opportunityCexDex.gainTotalEstimated}, gain1000 {getGain1000CexDex(opportunityCexDex)}, amountInInDollars : {opportunityCexDex.opportunityThorchain.amountInInDollars}')
                        #     logging.info("Opp positive detectée")
                        #     logging.info("Opp positive detectée")
                        amountInMax = getAmountInMaxCexDex(pairCexDex.pairAssetDex, pairCexDex.pairAssetCex, balancesShared)
                        amountInOpp = opportunityCexDex.opportunityThorchain.amountIn/1e8

                        conditionOpp = (
                            opportunityCexDex.gainTotalEstimated > THRESHOLD_GAIN_NET and getGain1000CexDex(opportunityCexDex)> THRESHOLD_GAIN1000_NET and amountInMax>amountInOpp
                            # opportunityCexDex.gainTotalEstimated > 0.05
                        )

                        # # conditionOpp = True
                        # logging.info(f'')
                        # logging.info(f'SCOUT CEXDEX - opp thorchain : assetIn : {opportunityCexDex.opportunityThorchain.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opportunityCexDex.opportunityThorchain.amountIn/1e8} amountOut {opportunityCexDex.opportunityThorchain.amountOutEstimated/1e8}')
                        # logging.info(f'SCOUT CEXDEX - opp bybit : assetIn : {opportunityCexDex.opportunityBybit.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityBybit.pairAsset.assetOut.symbol} amountIn : {opportunityCexDex.opportunityBybit.amountInEstimated} amountOut : {opportunityCexDex.opportunityBybit.amountOutEstimated} assetPrice : {opportunityCexDex.opportunityBybit.bybitAssetPrice}')
                        # logging.info(f"SCOUT CEXDEX - opportunityCexDex :  gainTotalEstimated {opportunityCexDex.gainTotalEstimated}, gain1000 {getGain1000CexDex(opportunityCexDex)}, amount in value in dollars {getAmountInValue(opportunityCexDex)}")
                        # logging.info(f"SCOUT CEXDEX - opportunityCexDex :  amountInMax {amountInMax}")
                        # logging.info(f'')

                        if conditionOpp:
                            print(f"{datetime.datetime.now()} SCOUT - y'a une opp CEXDEX THORCHAIN fréro block = {opportunityThorchain.detectedBlock}")
                            # logging.info(f"")
                            # logging.info(f'SCOUT CEXDEX - opp thorchain : assetIn : {opportunityCexDex.opportunityThorchain.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opportunityCexDex.opportunityThorchain.amountIn/1e8} amountOut {opportunityCexDex.opportunityThorchain.amountOutEstimated/1e8}')
                            # logging.info(f'SCOUT CEXDEX - opp bybit : assetIn : {opportunityCexDex.opportunityBybit.pairAsset.assetIn.symbol} assetOut : {opportunityCexDex.opportunityBybit.pairAsset.assetOut.symbol} amountIn : {opportunityCexDex.opportunityBybit.amountInEstimated} amountOut : {opportunityCexDex.opportunityBybit.amountOutEstimated} assetPrice : {opportunityCexDex.opportunityBybit.bybitAssetPrice}')
                            # logging.info(f"SCOUT CEXDEX - opportunityCexDex :  gainTotalEstimated {opportunityCexDex.gainTotalEstimated}, gain1000 {getGain1000CexDex(opportunityCexDex)}, amount in value in dollars {getAmountInValue(opportunityCexDex)}")
                            # logging.info(f"SCOUT CEXDEX - opportunityCexDex :  amountInMax {amountInMax}")
                            # logging.info(f"")
                            # listSuccessCexDexOpportunities.append(opportunityCexDex)
                            # queueOpportunitiesThorchain.put(opportunityCexDex)

    except Exception as err:
        logging.warning(f"processCreateOpportunityThorchainVSBybit error {err}")
        traceback.print_exc()


def processCreateOpportunityMayaVSThor(balancesShared : Balances, queueOpportunitiesMaya:Queue, eventScoutDexDex:Event, poolDictShared:Dict):
    try:

        updateAssetPoolData(balances=balancesShared,poolData=poolDictShared, type='THORCHAIN')

        balancesMaya = balancesShared.balancesMaya
        balancesThorchain = balancesShared.balancesThorchain 
        
        pairsMaya = createPairsForBalanceType(listAssets=balancesMaya.listAssets, orderbook="")
        pairsThorchain = createPairsForBalanceType(listAssets=balancesThorchain.listAssets, orderbook="")

        pairsDexDex = createPairsDexDex(pairsDex1=pairsMaya, pairsDex2=pairsThorchain)
        
        for pairDexDex in pairsDexDex:

            amountInMax = getAmountInMaxDexDex(firstPairToExecute=pairDexDex.pairAssetDex1, secondPairToExecute=pairDexDex.pairAssetDex2)

            if pairDexDex.pairAssetDex1.assetIn.balance > 10 and pairDexDex.pairAssetDex2.assetOut.symbol != 'DAI-0X6B175474E89094C44DA98B954EEDEAC495271D0F' and pairDexDex.pairAssetDex2.assetOut.symbol != 'BTCB-1DE' and pairDexDex.pairAssetDex2.assetOut.symbol != "WBTC-0X2260FAC5E5542A773AA44FBCFEDF7C193BC2C599":
                opportunityMaya = createMayaOpportunityForThorchain(
                    pairMaya=pairDexDex.pairAssetDex1,
                    amountIn=int(amountInMax*10**DECIMALS_CACAO),
                    typeOpp="MAYA",
                    balances=balancesShared
                )
                if opportunityMaya.amountInInDollars > 0.1:
                    opportunityMaya.detectedBlock = pairDexDex.pairAssetDex1.assetIn.pool.block
                    amountInThorchain = opportunityMaya.amountOutEstimated * 10**pairDexDex.pairAssetDex2.assetIn.decimals / 10**pairDexDex.pairAssetDex1.assetOut.decimals 
                    opportunityThorchain = createThorchainOpportunityForMaya(pairThorchain=pairDexDex.pairAssetDex2, amountIn=amountInThorchain, balancesThorchain=balancesThorchain, typeOpp="THORCHAIN")
                    opportunityDexDex = createOpportunityDexDex(pairDexDex=pairDexDex, opportunityThorchain=opportunityThorchain, opportunityMaya=opportunityMaya, balancesThorchain=balancesThorchain)
                    
                    if pairDexDex.pairAssetDex2.assetIn.assetType != 'RUNE':
                        opportunityThorchain.detectedBlock = pairDexDex.pairAssetDex2.assetIn.pool.block
                    else:
                        opportunityThorchain.detectedBlock = pairDexDex.pairAssetDex2.assetOut.pool.block
                    
                    # logging.info(f"")
                    # logging.info(f'MayaThor - opportunityMaya - amountInInDollars {opportunityMaya.amountInInDollars} $, block : {opportunityMaya.detectedBlock} {opportunityMaya.pairAsset.assetIn.symbol} to {opportunityMaya.pairAsset.assetOut.symbol} amountIn {opportunityMaya.amountIn/ 10**pairDexDex.pairAssetDex1.assetIn.decimals}  amountOutEstimated {opportunityMaya.amountOutEstimated/ 10**pairDexDex.pairAssetDex1.assetOut.decimals}  outboundFees {opportunityMaya.outboundFees/ 10**pairDexDex.pairAssetDex1.assetOut.decimals} slipFees {opportunityMaya.slipFees} $')
                    # logging.info(f'MayaThor - opportunityThorchain - {opportunityThorchain.pairAsset.assetIn.symbol} to {opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opportunityThorchain.amountIn/ 10**pairDexDex.pairAssetDex1.assetOut.decimals}  amountOutEstimated {opportunityThorchain.amountOutEstimated/ 10**pairDexDex.pairAssetDex1.assetIn.decimals}  outboundFees {opportunityThorchain.outboundFees/ 10**pairDexDex.pairAssetDex1.assetIn.decimals} slipFees $')
                    # logging.info(f'MayaThor - gainTotalEstimated {round(opportunityDexDex.gainTotalEstimated,2)} $ - THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA}')    
                    # logging.info(f"")
                    conditionOpp = opportunityDexDex.gainTotalEstimated > THRESHOLD_GAIN_NET_MAYA  and getGain1000DexDex(opportunityDexDex) > THRESHOLD_GAIN1000_NET_MAYA               
                    if conditionOpp:
                        print(f'{datetime.datetime.now()} ya une opp MAYATHOR block : {opportunityMaya.detectedBlock}')
                        logging.info('')
                        logging.info(f'MayaThor - OPP GAGNANTE - gainTotalEstimated {round(opportunityDexDex.gainTotalEstimated,2)} $ - THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA}')    
                        logging.info(f'MayaThor - opportunityMaya - amountInInDollars {opportunityMaya.amountInInDollars} $, block : {opportunityMaya.detectedBlock} {opportunityMaya.pairAsset.assetIn.symbol} to {opportunityMaya.pairAsset.assetOut.symbol} amountIn {opportunityMaya.amountIn/ 10**pairDexDex.pairAssetDex1.assetIn.decimals}  amountOutEstimated {opportunityMaya.amountOutEstimated/ 10**pairDexDex.pairAssetDex1.assetOut.decimals}  outboundFees {opportunityMaya.outboundFees/ 10**pairDexDex.pairAssetDex1.assetOut.decimals} slipFees {opportunityMaya.slipFees} $')
                        logging.info(f'MayaThor - opportunityThorchain - {opportunityThorchain.pairAsset.assetIn.symbol} to {opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opportunityThorchain.amountIn/ 10**pairDexDex.pairAssetDex1.assetOut.decimals}  amountOutEstimated {opportunityThorchain.amountOutEstimated/ 10**pairDexDex.pairAssetDex1.assetIn.decimals}  outboundFees {opportunityThorchain.outboundFees/ 10**pairDexDex.pairAssetDex1.assetIn.decimals} slipFees {opportunityThorchain.slipFees} $')
                        logging.info(f'MayaThor - gainTotalEstimated {round(opportunityDexDex.gainTotalEstimated,2)} $ - THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA}')    
                        
                        queueOpportunitiesMaya.put(opportunityDexDex)
                        logging.info('')

    except Exception as err:
        logging.warning(f"processCreateOpportunityMayaVSThor error {err}")
        traceback.print_exc()
    finally:
        eventScoutDexDex.set()




def processSelectOpportunitiesThorchain(
    queueOpportunitiesThorchain: Queue,
    queueOpportunitiesToExecute: Queue,
    balance: Balances,
    sharedOrderbook: Dict,
    eventScoutCexDexThorchain: Event,
    eventScoutOnblockThorchain: Event,
):
    try:
        # eventScoutCexDexThorchain.wait()  # Attendre la fin du processus de recherche 1
        # eventScoutOnblockThorchain.wait()  # Attendre la fin du processus de recherche 2
        while not (eventScoutCexDexThorchain.is_set() and eventScoutOnblockThorchain.is_set()):
            # logging.info(f'processSelectOpportunitiesThorchain - eventScoutCexDexThorchain.is_set {eventScoutCexDexThorchain.is_set()}, eventScoutOnblockThorchain.is_set {eventScoutOnblockThorchain.is_set()}')
            time.sleep(0.01)

        # logging.info(f'IN processSelectOpportunitiesThorchain')
        # Collecter toutes les opportunités de la queue
        # updatedBalance = balance
        # updatedSharedOrderbook = sharedOrderbook
        opportunities = []
        opportunitiesToExecute = []

        while not queueOpportunitiesThorchain.empty():
            lastElementInQueue = queueOpportunitiesThorchain.get()
            logging.info(f'Opp retirée de la queue avec gain total estimé = {lastElementInQueue.gainTotalEstimated}')
            if isinstance(lastElementInQueue, OpportunityCexDex):
                logging.info(f'Slippage Fees = {lastElementInQueue.opportunityThorchain.slipFees}')
            else :
                logging.info(f'Slippage Fees = {lastElementInQueue.slipFees}')


            opportunities.append(lastElementInQueue)

        orderedOpportunities = getOrderedOpportunities(opportunities)

        filteredOpportunitiesPerAsset = getFilteredOpportunitiesPerAsset(
            orderedOpportunities
        )

        # filteredOpportunities = getFilteredOpportunities(orderedOpportunities)

        for opp in filteredOpportunitiesPerAsset:
            if isinstance(opp, OpportunityCexDex):
                # logging.info(
                #     f"FILTERED OPP CEXDEX - processSelectOpportunitiesThorchain - BLOCK : {opp.opportunityThorchain.pairAsset.assetIn.pool.block} poolIn : asset {opp.opportunityThorchain.pairAsset.assetIn.pool.balanceAssetInPool} rune : {opp.opportunityThorchain.pairAsset.assetIn.pool.balanceRuneInPoolAsset} poolOut : asset {opp.opportunityThorchain.pairAsset.assetOut.pool.balanceAssetInPool} rune {opp.opportunityThorchain.pairAsset.assetOut.pool.balanceRuneInPoolAsset}"
                # )
                # logging.info(
                #     f"FILTERED OPP CEXDEX - processSelectOpportunitiesThorchain - opp thorchain : assetIn : {opp.opportunityThorchain.pairAsset.assetIn.symbol} assetOut : {opp.opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opp.opportunityThorchain.amountIn/1e8} amountOut {opp.opportunityThorchain.amountOutEstimated/1e8}"
                # )
                # logging.info(
                #     f"FILTERED OPP CEXDEX - processSelectOpportunitiesThorchain - opp bybit : assetIn : {opp.opportunityBybit.pairAsset.assetIn.symbol} assetOut : {opp.opportunityBybit.pairAsset.assetOut.symbol} amountIn : {opp.opportunityBybit.amountInEstimated} amountOut : {opp.opportunityBybit.amountOutEstimated} "
                # )
                # logging.info(
                #     f"FILTERED OPP CEXDEX - processSelectOpportunitiesThorchain - gainTotalEstimated {opp.gainTotalEstimated}"
                # )
                opportunitiesToExecute.append(opp)
            if isinstance(opp, OpportunityThorchain):
                # logging.info(
                #     f"TEST FILTERED OPP ONBLOCK - processSelectOpportunitiesThorchain - BLOCK : {opp.pairAsset.assetIn.pool.block} poolIn : asset {opp.pairAsset.assetIn.pool.balanceAssetInPool} rune : {opp.pairAsset.assetIn.pool.balanceRuneInPoolAsset} poolOut : asset {opp.pairAsset.assetOut.pool.balanceAssetInPool} rune {opp.pairAsset.assetOut.pool.balanceRuneInPoolAsset}"
                # )
                # logging.info(
                #     f"TEST FILTERED OPP ONBLOCK - processSelectOpportunitiesThorchain - assetIn : {opp.pairAsset.assetIn.symbol} assetOut : {opp.pairAsset.assetOut.symbol} amountIn {opp.amountIn/1e8} amountOut {opp.amountOutEstimated/1e8} gainNetInDollars {opp.gainTotalEstimated}"
                # )
                opportunitiesToExecute.append(opp)

        queueOpportunitiesToExecute.put(opportunitiesToExecute)

    except Exception as e:
        # Gérer l'exception ici
        logging.warning(
            f"processSelectOpportunitiesThorchain - Une erreur est survenue : {e}"
        )
        # Vous pouvez décider de retourner une liste vide, relancer l'exception, ou effectuer une autre action.
        return []

    finally:
        # Le bloc finally est exécuté indépendamment de la survenue ou non d'une exception.
        eventScoutCexDexThorchain.clear()  # Réinitialiser les événements pour le prochain bloc
        eventScoutOnblockThorchain.clear()

    return filteredOpportunitiesPerAsset


def processSelectOpportunitiesMaya(
    queueOpportunitiesMaya: Queue,
    queueOpportunitiesToExecute: Queue,
    balance: Balances,
    sharedOrderbook: Dict,
    eventScoutCexDexMaya: Event,
    eventScoutOnblockMaya: Event,
    eventScoutDexDex:Event
):
    try:

        while not (eventScoutDexDex.is_set()): #and eventScoutDexDex.is_set()
            time.sleep(0.01)

        # Collecter toutes les opportunités de la queue
        # updatedBalance = balance
        # updatedSharedOrderbook = sharedOrderbook
        opportunities = []
        opportunitiesToExecute = []
        
        while not queueOpportunitiesMaya.empty():
            lastElementInQueue = queueOpportunitiesMaya.get()
            logging.info(f'Maya - Opp retirée de la queue avec gain total estimé = {lastElementInQueue.gainTotalEstimated}')
            if isinstance(lastElementInQueue, OpportunityCexDex):
                logging.info(f'Maya Slippage Fees = {lastElementInQueue.opportunityThorchain.slipFees}')
            elif isinstance(lastElementInQueue, OpportunityDexDex):
                logging.info(f'Maya Slippage Fees = {lastElementInQueue.opportunityMaya.slipFees}')
            else :
                logging.info(f'Maya Slippage Fees = {lastElementInQueue.slipFees}')
            opportunities.append(lastElementInQueue)


        orderedOpportunities = getOrderedOpportunities(opportunities)

        filteredOpportunitiesPerAsset = getFilteredOpportunitiesPerAsset(
            orderedOpportunities
        )

        for opp in filteredOpportunitiesPerAsset:
            if isinstance(opp, OpportunityCexDex):
                # logging.info(
                #     f"MAYA FILTERED OPP CEXDEX - processSelectOpportunitiesMaya - BLOCK : {opp.opportunityThorchain.pairAsset.assetIn.pool.block} poolIn : asset {opp.opportunityThorchain.pairAsset.assetIn.pool.balanceAssetInPool} cacao : {opp.opportunityThorchain.pairAsset.assetIn.pool.balanceCacaoInPoolAsset} poolOut : asset {opp.opportunityThorchain.pairAsset.assetOut.pool.balanceAssetInPool} cacao {opp.opportunityThorchain.pairAsset.assetOut.pool.balanceCacaoInPoolAsset}"
                # )
                # logging.info(
                #     f"MAYA FILTERED OPP CEXDEX - processSelectOpportunitiesMaya - opp thorchain : assetIn : {opp.opportunityThorchain.pairAsset.assetIn.symbol} assetOut : {opp.opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opp.opportunityThorchain.amountIn/1e8} amountOut {opp.opportunityThorchain.amountOutEstimated/1e8}"
                # )
                # logging.info(
                #     f"MAYA FILTERED OPP CEXDEX - processSelectOpportunitiesMaya - opp bybit : assetIn : {opp.opportunityBybit.pairAsset.assetIn.symbol} assetOut : {opp.opportunityBybit.pairAsset.assetOut.symbol} amountIn : {opp.opportunityBybit.amountInEstimated} amountOut : {opp.opportunityBybit.amountOutEstimated} "
                # )
                # logging.info(
                #     f"MAYA FILTERED OPP CEXDEX - processSelectOpportunitiesMaya - gainTotalEstimated {opp.gainTotalEstimated}"
                # )
                opportunitiesToExecute.append(opp)
            if isinstance(opp, OpportunityMaya):
                # logging.info(
                #     f"MAYA FILTERED OPP ONBLOCK - processSelectOpportunitiesMaya - BLOCK : {opp.pairAsset.assetIn.pool.block} poolIn : asset {opp.pairAsset.assetIn.pool.balanceAssetInPool} cacao : {opp.pairAsset.assetIn.pool.balanceCacaoInPoolAsset} poolOut : asset {opp.pairAsset.assetOut.pool.balanceAssetInPool} cacao {opp.pairAsset.assetOut.pool.balanceCacaoInPoolAsset}"
                # )
                # logging.info(
                #     f"MAYA FILTERED OPP ONBLOCK - processSelectOpportunitiesMaya - assetIn : {opp.pairAsset.assetIn.symbol} assetOut : {opp.pairAsset.assetOut.symbol} amountIn {opp.amountIn/1e8} amountOut {opp.amountOutEstimated/1e8} gainNetInDollars {opp.gainTotalEstimated}"
                # )
                opportunitiesToExecute.append(opp)
            if isinstance(opp, OpportunityDexDex):
                opportunitiesToExecute.append(opp)

        queueOpportunitiesToExecute.put(opportunitiesToExecute)

    except Exception as e:
        # Gérer l'exception ici
        logging.warning(
            f"processSelectOpportunitiesMaya - Une erreur est survenue : {e}"
        )
        # Vous pouvez décider de retourner une liste vide, relancer l'exception, ou effectuer une autre action.
        return []

    finally:
        # Le bloc finally est exécuté indépendamment de la survenue ou non d'une exception.
        eventScoutCexDexMaya.clear()  # Réinitialiser les événements pour le prochain bloc
        eventScoutOnblockMaya.clear()
        eventScoutDexDex.clear()

    return filteredOpportunitiesPerAsset




def processOpportunityConsumer(queueOpportunitiesToExecute: Queue, balances: Balances, lock:Lock, balanceDictShared:Dict, poolDictShared:Dict, sharedCounter):
    while True:
        try:
            if 'THORCHAIN' in poolDictShared and 'MAYA' in poolDictShared:
                updateAssetPoolData(balances=balances,poolData=poolDictShared, type='THORCHAIN')
                updateAssetPoolData(balances=balances,poolData=poolDictShared, type='MAYA')
                listOpportunities = []
                if not queueOpportunitiesToExecute.empty():
                    listOpportunities = queueOpportunitiesToExecute.get()

                for opportunity in listOpportunities:
                    isOppPossible_ = isOppPossible(balanceDict=balanceDictShared, opportunity=opportunity)
                    if isOppPossible_:   
                        with lock:
                            sharedCounter.value = sharedCounter.value + 1  
                        logging.info(f'balanceDictShared before Opp {sharedCounter} : {balanceDictShared}')               
                        if isinstance(opportunity, OpportunityCexDex):
                            updateBalanceDictWithDoubleOpp(opportunity1=opportunity.opportunityThorchain, opportunity2=opportunity.opportunityBybit, balanceDict=balanceDictShared, isOppSuccess=True, isEstimated=True, lock=lock)

                            if opportunity.opportunityThorchain.typeOpp=="MAYA":
                                processExecuteOpportunity_ =  Process(target=executeMayaCexDexOpportunity, args=(balances, opportunity, lock, balanceDictShared, sharedCounter))

                            elif opportunity.opportunityThorchain.typeOpp=="THORCHAIN":
                                processExecuteOpportunity_ = Process(target=executeCexDexOpportunity, args=(balances, opportunity, lock, balanceDictShared, sharedCounter))

                            processExecuteOpportunity_.start()
                            
                        if isinstance(opportunity, OpportunityThorchain):
                            updateBalanceDictWithSingleOpp(opportunity=opportunity, balanceDict=balanceDictShared, isOppSuccess=True, isEstimated=True, lock=lock)
                            processExecuteOpportunity_ = Process(target=executeThorchainOnBlockOpportunity,args=(balances, opportunity, lock, balanceDictShared, sharedCounter))
                            processExecuteOpportunity_.start()

                        if isinstance(opportunity, OpportunityMaya):
                            updateBalanceDictWithSingleOpp(opportunity=opportunity, balanceDict=balanceDictShared, isOppSuccess=True, isEstimated=True, lock=lock)
                            processExecuteOpportunity_ =  Process(target=executeMayaOnBlockOpportunity, args=(balances, opportunity, lock, balanceDictShared, sharedCounter))
                            processExecuteOpportunity_.start()    
                        
                        if isinstance(opportunity, OpportunityDexDex):
                            updateBalanceDictWithDoubleOpp(opportunity1=opportunity.opportunityMaya, opportunity2=opportunity.opportunityThorchain, balanceDict=balanceDictShared, isOppSuccess=True, isEstimated=True, lock=lock)
                            processExecuteOpportunity_ =  Process(target=executeMayaThorOpportunity, args=(balances, opportunity, lock, balanceDictShared, sharedCounter))
                            processExecuteOpportunity_.start()  

                    else:
                        logging.warning(f'opp not possible')
            

        except Exception as err:
            logging.warning(f"processOpportunityConsumer error {err}")
            traceback.print_exc()



