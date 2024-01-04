from tools.init import initBalance
from classes.Balances import Balances
from tools.myUtils import createPairsForBalanceType, updateAllBalances
from utilsMaya.mayaCalcul import createMayaSynthOnBlockOpportunity, createMayaOpportunityForBybit, createMayaOpportunityForThorchain
from constantes.myAddresses import MY_ADDRESS_MAYA
from utilsMaya.mayaInteraction import getMayaPool, getMayaBlock, removeChainHaltedOnMaya
from utilsMaya.mayaUtils import updateMayaAssetPoolData
from constantes.constantes import DECIMALS_CACAO, THRESHOLD_GAIN_NET_MAYA, THRESHOLD_GAIN1000_NET_MAYA
from multiprocessing import Process, Queue, Manager, Event
from constantes.constantes import DECIMALS_CACAO
from constantes.url import URL_BLOCK_MAYA, URL_BLOCK_THOR
from typing import Dict, List
from tools.utilsCEXDEX import createPairsCexDex, createOpportunityCexDex
from tools.myUtils import updateBalances, createPairsForBalanceType, getAmountInMax, getGain1000CexDex, getGain1000OnBlock, getAmountInValue, updateAllBalances, getOrderedOpportunities, getFilteredOpportunities, getFilteredOpportunitiesPerAsset
from utilsBybit.bybit_utils import createBybitOpportunityForThorchain
from collections import deque
from utilsBybit.bybit_websocket import startWebsocket
from classes.Opportunity import OpportunityMaya, OpportunityCexDex, OpportunityThorchain
from opportunityExecution import executeMayaCexDexOpportunity,executeMayaOnBlockOpportunity, executeCexDexOpportunity
from tools.utilsMAYATHOR import createPairsDexDex, createOpportunityDexDex, getAmountInMaxDexDex
from utilsThorchain.thorchainCalcul import createThorchainOpportunityForMaya
from utilsThorchain.thorchainInteraction import getThorchainPool, removeChainHaltedOnThorchain, getBlock
from utilsThorchain.thorchainUtils import updateThorchainAssetPoolData

import traceback
import requests 
import time


def processGetMayaBlock(slidingListBlock, BalancesShared:Balances, orderbookDataShared:Dict, queueOpportunitiesMaya:Queue, queueOpportunitiesToExecute:Queue):
    referencePoolData = getMayaPool()
    referencePoolDataThor = getThorchainPool()
    blockThor=getBlock()
    while True:
        try:
            block = getMayaBlock()
            slidingListBlock.append(int(block))

            lastBlock = int(slidingListBlock[-2])
            currentBlock = int(slidingListBlock[-1])

            responseInfoNode = requests.get(
                url=URL_BLOCK_MAYA, timeout=1).json()

            catchingUpNode = responseInfoNode["result"]["sync_info"]["catching_up"]

            if catchingUpNode == True:
                print("processGetMayaBlock - catching up true")
                time.sleep(10)
                continue

            if currentBlock > lastBlock and catchingUpNode == False:
                newPoolData = getMayaPool()
                compteur =0
                # while newPoolData == referencePoolData:
                #     newPoolData = getMayaPool()
                #     compteur = compteur+1
                #     time.sleep(0.1)
                # compteur =0

                referencePoolData=newPoolData
                poolData = newPoolData

                newCurrentBlock = getMayaBlock()

                if int(newCurrentBlock) > currentBlock :
                    print(f'newCurrentBlock {newCurrentBlock} vs oldBlock {currentBlock}')
                    slidingListBlock.append(int(newCurrentBlock))
                    currentBlock=newCurrentBlock

                removeChainHaltedOnMaya(
                    listAssets=BalancesShared.balancesMaya.listAssets
                )

                updateAllBalances(BalancesShared)
                updateMayaAssetPoolData(balances=BalancesShared, poolData=poolData, currentBlock=currentBlock)
                updateThorchainAssetPoolData(balances=BalancesShared,poolData=referencePoolDataThor, currentBlock=blockThor)
                launchMayaProcesses(BalancesShared, orderbookDataShared, queueOpportunitiesMaya, queueOpportunitiesToExecute)

        except Exception as err:
            print(err)
            traceback.print_exc()


def processGetThorchainBlock(
    slidingListBlock,
    BalancesShared: Balances,
):

    referencePoolData = getThorchainPool()

    while True:
        try:
            block = requests.get(url=URL_BLOCK_THOR, timeout=1).json()["result"][
                "sync_info"
            ]["latest_block_height"]
            # block = requests.get(url=URL_BLOCK_THOR_NEW, timeout=1).json()[
            #     0]["thorchain"]
            slidingListBlock.append(int(block))

            lastBlock = int(slidingListBlock[-2])
            currentBlock = int(slidingListBlock[-1])

            responseInfoNode = requests.get(url=URL_BLOCK_THOR, timeout=1).json()

            catchingUpNode = responseInfoNode["result"]["sync_info"]["catching_up"]

            # getThorchainWalletValue(BalancesShared.balancesThorchain)

            if catchingUpNode == True:
                time.sleep(10)
                continue

            if currentBlock > lastBlock and catchingUpNode == False:
                newPoolData = getThorchainPool()
                compteur =0
                # while newPoolData == referencePoolData:
                #     newPoolData = getThorchainPool()
                #     compteur = compteur+1
                #     # logging.info(f'Compteur = {compteur}')
                #     time.sleep(0.1)

                compteur =0
                referencePoolData=newPoolData
                poolData = newPoolData

                newCurrentBlock = requests.get(url=URL_BLOCK_THOR, timeout=1).json()[
                    "result"
                ]["sync_info"]["latest_block_height"]

                if int(newCurrentBlock) > currentBlock:
                    slidingListBlock.append(int(newCurrentBlock))
                    currentBlock = newCurrentBlock

                removeChainHaltedOnThorchain(
                    listAssets=BalancesShared.balancesThorchain.listAssets
                )

                updateAllBalances(BalancesShared)

                updateThorchainAssetPoolData(
                    balances=BalancesShared,
                    poolData=poolData,
                    currentBlock=currentBlock,
                )


            time.sleep(0.1)

        except Exception as err:
            traceback.print_exc()


def launchMayaProcesses(BalancesShared: Balances, orderbookDataShared:Dict, queueOpportunitiesMaya:Queue, queueOpportunitiesToExecute:Queue):
    eventScoutCexDexMaya = Event()
    eventScoutOnblockMaya = Event()
    eventScoutDexDexMaya = Event()

    # processOpportunityMayaVSBybitProducer = Process(target=processCreateOpportunityMayaVSBybit , args=(BalancesShared, orderbookDataShared,queueOpportunitiesMaya,eventScoutCexDexMaya))
    # processOpportunityMayaSynthOnBlockProducer = Process(target=processCreateOpportunityMayaOnBlock, args=(BalancesShared,queueOpportunitiesMaya,eventScoutOnblockMaya))
    processCreateOpportunityMayaVSThorProducer = Process(target=processCreateOpportunityMayaVSThor, args=(BalancesShared,queueOpportunitiesMaya,eventScoutDexDexMaya))
    # processSelectOpportunitiesMaya_ = Process(target=processSelectOpportunitiesMaya, args=(queueOpportunitiesMaya,queueOpportunitiesToExecute, BalancesShared, orderbookDataShared, eventScoutCexDexMaya, eventScoutOnblockMaya))

    # Démarrage des processus
    # processOpportunityMayaVSBybitProducer.start()
    # processOpportunityMayaSynthOnBlockProducer.start()
    # processSelectOpportunitiesMaya_.start()
    processCreateOpportunityMayaVSThorProducer.start()


def processCreateOpportunityMayaVSThor(balancesShared : Balances, queueOpportunitiesMaya:Queue, eventScoutDexDex:Event):
    try:
        balancesMaya = balancesShared.balancesMaya
        balancesThorchain = balancesShared.balancesThorchain
        pairsMaya = createPairsForBalanceType(listAssets=balancesMaya.listAssets, orderbook="")
        pairsThorchain = createPairsForBalanceType(listAssets=balancesThorchain.listAssets, orderbook="")

        pairsDexDex = createPairsDexDex(pairsDex1=pairsMaya, pairsDex2=pairsThorchain)

        for pairDexDex in pairsDexDex:
            # print(f'MAYA : {pairDexDex.pairAssetDex1.assetIn.symbol }  {pairDexDex.pairAssetDex1.assetOut.symbol }')
            # print(f'THOR : {pairDexDex.pairAssetDex2.assetIn.symbol }  {pairDexDex.pairAssetDex2.assetOut.symbol }')
            amountInMax = getAmountInMaxDexDex(firstPairToExecute=pairDexDex.pairAssetDex1, secondPairToExecute=pairDexDex.pairAssetDex2)

            if pairDexDex.pairAssetDex1.assetIn.balance > 10 and amountInMax > 10:
                opportunityMaya = createMayaOpportunityForThorchain(
                    pairMaya=pairDexDex.pairAssetDex1,
                    amountIn=int(amountInMax*10**DECIMALS_CACAO),
                    typeOpp="MAYATHOR",
                    balances=balancesShared
                )
                # if opportunityMaya.amountInInDollars > 15.0:
                opportunityMaya.detectedBlock = pairDexDex.pairAssetDex1.assetIn.pool.block
                amountInThorchain = opportunityMaya.amountOutEstimated * 10**pairDexDex.pairAssetDex2.assetIn.decimals / 10**pairDexDex.pairAssetDex1.assetOut.decimals 
                opportunityThorchain = createThorchainOpportunityForMaya(pairThorchain=pairDexDex.pairAssetDex2, amountIn=amountInThorchain, balancesThorchain=balancesThorchain, typeOpp="MAYATHOR")
                opportunityDexDex = createOpportunityDexDex(pairDexDex=pairDexDex, opportunityThorchain=opportunityThorchain, opportunityMaya=opportunityMaya, balancesThorchain=balancesThorchain)

                conditionOpp = opportunityDexDex.gainTotalEstimated > THRESHOLD_GAIN_NET_MAYA
                
                if conditionOpp:
                    print('')
                    print(f'MayaThor - OPP GAGNANTE - gainTotalEstimated {round(opportunityDexDex.gainTotalEstimated,2)} $ - THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA}')    
                    print(f'MayaThor - opportunityMaya - amountInInDollars {opportunityMaya.amountInInDollars} $, block : {opportunityMaya.detectedBlock} {opportunityMaya.pairAsset.assetIn.symbol} to {opportunityMaya.pairAsset.assetOut.symbol} amountIn {opportunityMaya.amountIn/ 10**pairDexDex.pairAssetDex1.assetIn.decimals}  amountOutEstimated {opportunityMaya.amountOutEstimated/ 10**pairDexDex.pairAssetDex1.assetOut.decimals}  outboundFees {opportunityMaya.outboundFees/ 10**pairDexDex.pairAssetDex1.assetOut.decimals} slipFees {opportunityMaya.slipFees} $')
                    print(f'MayaThor - opportunityThorchain - {opportunityThorchain.pairAsset.assetIn.symbol} to {opportunityThorchain.pairAsset.assetOut.symbol} amountIn {opportunityThorchain.amountIn/ 10**pairDexDex.pairAssetDex1.assetOut.decimals}  amountOutEstimated {opportunityThorchain.amountOutEstimated/ 10**pairDexDex.pairAssetDex1.assetIn.decimals}  outboundFees {opportunityThorchain.outboundFees/ 10**pairDexDex.pairAssetDex1.assetIn.decimals} slipFees {opportunityThorchain.slipFees} {opportunityThorchain.pairAsset.assetOut.symbol}')
                    print(f'MayaThor - gainTotalEstimated {round(opportunityDexDex.gainTotalEstimated,2)} $ - THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA}')    
                    
                    queueOpportunitiesMaya.put(opportunityDexDex)
                    print('')

    except Exception as err:
        print(f"processCreateOpportunityMayaVSThor error {err}")
        traceback.print_exc()
    finally:
        eventScoutDexDex.set()




httpClient = requests.Session()
manager = Manager()

# symbol_list = getSymbolList(httpClient)

slidingListBlock = deque(maxlen=3)
slidingListBlock.append(0)
slidingListBlock.append(0)
slidingListBlock.append(0)

queueOpportunitiesToExecute = Queue()
queueOpportunitiesMaya = Queue()

# eventWebsocketConnected = Event()
    
# orderbookDataShared = manager.dict()
BalancesShared = manager.Namespace()
BalancesShared = initBalance()

# ----- 
# processOrderbookProducer = Process(target=startWebsocket, args=(orderbookDataShared,eventWebsocketConnected))
processBlockMayaProducer = Process(target=processGetMayaBlock, args=(slidingListBlock, BalancesShared, '', queueOpportunitiesMaya, queueOpportunitiesToExecute))
# processOpportunityConsumer_ = Process(target=processOpportunityConsumer, args=(queueOpportunitiesToExecute, BalancesShared))
# processGetThorchainBlockProducer = Process(target=processGetThorchainBlock, args=(slidingListBlock, BalancesShared))
# ----- 
# processOrderbookProducer.start()
# eventWebsocketConnected.wait()
processBlockMayaProducer.start()
# processGetThorchainBlockProducer.start()

# processOpportunityConsumer_.start()
# ----- 
# processOrderbookProducer.join()
processBlockMayaProducer.join()
# processGetThorchainBlockProducer.join()
# processOpportunityConsumer_.join()





# def processCreateOpportunityMayaOnBlock(BalancesShared:Balances, queueOpportunitiesMaya:Queue, eventScoutOnblockMaya:Event):
#     try:
        
#         pairsMaya = createPairsForBalanceType(listAssets=BalancesShared.balancesMaya.listAssets, orderbook='')
            
#         for pairMaya in pairsMaya:
#             if pairMaya.assetIn.assetType == pairMaya.assetOut.assetType:
#                 if pairMaya.assetIn.balance >10:
#                     amountIn = (pairMaya.assetIn.balance * 10**DECIMALS_CACAO / 10**pairMaya.assetIn.decimals)
#                     opportunityMaya = createMayaSynthOnBlockOpportunity(
#                         pairMaya=pairMaya,
#                         amountIn=amountIn,
#                         typeOpp="MayaOnBlockSynth",
#                         balancesMaya=BalancesShared.balancesMaya
#                     )            
                    
#                     opportunityMaya.detectedBlock = pairMaya.assetIn.pool.block
#                     if opportunityMaya.amountInInDollars > 15:
#                         print('')
#                         print(f'ONBLOCK - opportunityMaya - amountIn {opportunityMaya.amountIn/ 10**pairMaya.assetIn.decimals} {opportunityMaya.pairAsset.assetIn.symbol} amountOutEstimated {opportunityMaya.amountOutEstimated/ 10**pairMaya.assetOut.decimals} {opportunityMaya.pairAsset.assetOut.symbol} outboundFees {opportunityMaya.outboundFees/ 10**pairMaya.assetOut.decimals} slipFees {opportunityMaya.slipFees/ 10**pairMaya.assetOut.decimals} {opportunityMaya.pairAsset.assetOut.symbol}')
#                         print(f'ONBLOCK : gainTotalEstimated = {round((opportunityMaya.amountOutEstimated-opportunityMaya.amountIn)/10**pairMaya.assetIn.decimals,2)} $')
#                         # url = f'http://18.217.85.10:1317/mayachain/quote/swap?height={int(opportunityMaya.detectedBlock)}&from_asset={opportunityMaya.pairAsset.assetIn.memoName}&to_asset={opportunityMaya.pairAsset.assetOut.memoName}&amount={int(opportunityMaya.amountIn)}&destination={MY_ADDRESS_MAYA}&from_address={MY_ADDRESS_MAYA}'
#                         # print(f'url {url}')
#                         # quoteSwap = requests.get(url=url).json()
#                         # expected_amount_out = int(quoteSwap['expected_amount_out']) / 1e8
#                         # outbound_fee = int(quoteSwap['fees']['outbound']) / 1e8
#                         # # liquidity = int(quoteSwap['fees']['liquidity']) / 1e8
#                         # print(f'Expected Amount Out: {expected_amount_out}')
#                         # print(f'Outbound Fee: {outbound_fee}')

#                         # print(f'Slip fees : {liquidity}')

#                         conditionOpp = opportunityMaya.gainNetInDollars > THRESHOLD_GAIN_NET_MAYA and getGain1000OnBlock(opportunityMaya) > THRESHOLD_GAIN1000_NET_MAYA
                    
#                         if conditionOpp:
#                             print(f'ONBLOCK - OPP GAGNANTE - gainNetInDollars {round(opportunityMaya.gainNetInDollars,2)} $ - THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA}')    
#                             queueOpportunitiesMaya.put(opportunityMaya)
#                         print('')

#     except Exception as err:
#         print(f"processCreateOpportunityMayaOnBlock error {err}")
#         # traceback.print_exc()

#     finally:
#         eventScoutOnblockMaya.set()  
        

# def processCreateOpportunityMayaVSBybit(balancesShared : Balances, orderbookDataShared: Dict, queueOpportunitiesMaya:Queue, eventScoutCexDexMaya:Event):
#     try:
        
#         balancesDex = balancesShared.balancesMaya
#         balancesCex = balancesShared.balancesBybit
#         pairsDex = createPairsForBalanceType(listAssets=balancesDex.listAssets, orderbook=orderbookDataShared)
#         pairsCex = createPairsForBalanceType(listAssets=balancesCex.listAssets, orderbook=orderbookDataShared)
#         pairsCexDex = createPairsCexDex(pairsDex=pairsDex, pairsCex=pairsCex)

#         for pairCexDex in pairsCexDex:
#             amountInMax = getAmountInMax(pairCexDex.pairAssetDex, pairCexDex.pairAssetCex)
#             if pairCexDex.pairAssetDex.assetIn.balance > 10:
#                     opportunityMaya = createMayaOpportunityForBybit(
#                         pairMaya=pairCexDex.pairAssetDex,
#                         amountIn=int(amountInMax*10**DECIMALS_CACAO),
#                         typeOpp="CexDexMaya",
#                         orderbookData=pairCexDex.pairAssetCex.orderbook,
#                         balancesMaya=balancesDex
#                     )
                                        
#                     if opportunityMaya.amountInInDollars > 15.0:
#                         opportunityMaya.detectedBlock = pairCexDex.pairAssetDex.assetIn.pool.block
#                         opportunityBybit = createBybitOpportunityForThorchain(opportunityThorchain=opportunityMaya, orderbookData=orderbookDataShared, balances=balancesShared)
#                         opportunityCexDex = createOpportunityCexDex(pairCexDex=pairCexDex, opportunityThorchain=opportunityMaya, opportunityBybit=opportunityBybit)
                        
#                         print(f'CEXDEX MAYA - opportunityMaya - amountIn {opportunityMaya.amountIn/ 10**pairCexDex.pairAssetDex.assetIn.decimals} {opportunityMaya.pairAsset.assetIn.symbol} amountOutEstimated {opportunityMaya.amountOutEstimated/ 10**pairCexDex.pairAssetDex.assetOut.decimals} {opportunityMaya.pairAsset.assetOut.symbol} outboundFees {opportunityMaya.outboundFees/ 10**pairCexDex.pairAssetDex.assetOut.decimals} slipFees {opportunityMaya.slipFees} {opportunityMaya.pairAsset.assetOut.symbol}')
#                         print(f'CEXDEX MAYA - opportunityBybit - amountIn {opportunityBybit.amountInEstimated} {opportunityBybit.pairAsset.assetIn.symbol} amountOutEstimated {opportunityBybit.amountOutEstimated} {opportunityBybit.pairAsset.assetOut.symbol}')
#                         print(f'CEXDEXMAYA - gainTotalEstimated {round(opportunityCexDex.gainTotalEstimated,2)} $ - THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA}')    
                        
#                         conditionOpp = opportunityCexDex.gainTotalEstimated > THRESHOLD_GAIN_NET_MAYA and getGain1000CexDex(opportunityCexDex) > THRESHOLD_GAIN1000_NET_MAYA
                        
#                         if conditionOpp:
#                             print(f'CEXDEXMAYA - OPP GAGNANTE - gainTotalEstimated {round(opportunityCexDex.gainTotalEstimated,2)} $ - THRESHOLD_GAIN_NET_MAYA {THRESHOLD_GAIN_NET_MAYA} - THRESHOLD_GAIN1000_NET_MAYA {THRESHOLD_GAIN1000_NET_MAYA}')    
#                             queueOpportunitiesMaya.put(opportunityCexDex)
        
#     except Exception as err:
#         print(f"processCreateOpportunityMayaVSBybit error {err}")
#         traceback.print_exc()
#     finally:
#         eventScoutCexDexMaya.set()





# def processSelectOpportunitiesMaya(
#     queueOpportunitiesMaya: Queue,
#     queueOpportunitiesToExecute: Queue,
#     balance: Balances,
#     sharedOrderbook: Dict,
#     eventScoutCexDexMaya: Event,
#     eventScoutOnblockMaya: Event,
#     eventScoutDexDex:Event,
# ):
#     try:
#         eventScoutDexDex.wait()
#         eventScoutCexDexMaya.wait()  # Attendre la fin du processus de recherche 1
#         eventScoutOnblockMaya.wait()  # Attendre la fin du processus de recherche 2

#         while not (eventScoutCexDexMaya.is_set() and eventScoutOnblockMaya.is_set() and eventScoutDexDex.is_set()):
#             time.sleep(0.01)

#         # Collecter toutes les opportunités de la queue
#         # updatedBalance = balance
#         # updatedSharedOrderbook = sharedOrderbook
#         opportunities = []
#         opportunitiesToExecute = []
        
#         while not queueOpportunitiesMaya.empty():
#             lastElementInQueue = queueOpportunitiesMaya.get()
#             print(f'Maya - Opp retirée de la queue avec gain total estimé = {lastElementInQueue.gainTotalEstimated}')
#             if isinstance(lastElementInQueue, OpportunityCexDex):
#                 print(f'Maya Slippage Fees = {lastElementInQueue.opportunityThorchain.slipFees}')
#             else :
#                 print(f'Maya Slippage Fees = {lastElementInQueue.slipFees}')
#             opportunities.append(lastElementInQueue)


#         orderedOpportunities = getOrderedOpportunities(opportunities)

#         filteredOpportunitiesPerAsset = getFilteredOpportunitiesPerAsset(
#             orderedOpportunities
#         )

#         for opp in filteredOpportunitiesPerAsset:
#             if isinstance(opp, OpportunityCexDex):

#                 opportunitiesToExecute.append(opp)
#             if isinstance(opp, OpportunityMaya):

#                 opportunitiesToExecute.append(opp)
#         queueOpportunitiesToExecute.put(opportunitiesToExecute)

#     except Exception as e:
#         # Gérer l'exception ici
#         print(
#             f"processSelectOpportunitiesMaya - Une erreur est survenue : {e}"
#         )
#         # Vous pouvez décider de retourner une liste vide, relancer l'exception, ou effectuer une autre action.
#         return []

#     finally:
#         # Le bloc finally est exécuté indépendamment de la survenue ou non d'une exception.
#         eventScoutCexDexMaya.clear()  # Réinitialiser les événements pour le prochain bloc
#         eventScoutOnblockMaya.clear()

#     return filteredOpportunitiesPerAsset


# def processOpportunityConsumer(queueOpportunitiesToExecute: Queue, balances:Balances):
#     while True:
#         try:
#             listOpportunities = []
#             if not queueOpportunitiesToExecute.empty():
#                 listOpportunities=queueOpportunitiesToExecute.get()
                
#             for opportunity in listOpportunities:

#                 if isinstance(opportunity, OpportunityCexDex):
#                     if opportunity.opportunityThorchain.typeOpp=="CexDexMaya":
#                         processExecuteOpportunity_ =  Process(target=executeMayaCexDexOpportunity, args=(balances, opportunity))
#                     elif opportunity.opportunityThorchain.typeOpp=="CexDexThorchain":
#                         processExecuteOpportunity_ = Process(
#                         target=executeCexDexOpportunity, args=(balances, opportunity))
#                     processExecuteOpportunity_.start()

#                 if isinstance(opportunity, OpportunityMaya):
#                     processExecuteOpportunity_ =  Process(target=executeMayaOnBlockOpportunity, args=(balances, opportunity))
#                     processExecuteOpportunity_.start()               
                
#         except Exception as err:
#             print(f"processOpportunityConsumer error {err}")
