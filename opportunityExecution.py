import logging
import traceback
import requests
import time
import math

from typing import Dict, List

from utilsBybit.bybit_utils import place_order, isSell

from constantes.constantes import THRESHOLD_GAIN_NET, MINIMUM_BALANCE_TO_SCOUT

from tools.myUtils import updateBalanceDictWithDoubleOpp, updateBalanceDictWithSingleOpp
from tools.utilsCsv import writeDataOpp, writeDataOppMaya

from utilsThorchain.thorchainInteraction import (
    executeThorchainOpportunity,
    checkThorchainTxStatus,
)
from utilsMaya.mayaInteraction import executeMayaOpportunity, checkMayaTxStatus
from utilsMaya.mayaCalcul import getAmountOutRealFromTxMaya

from utilsThorchain.thorchainCalcul import getAmountOutRealFromTxThorchain

from classes.Opportunity import (
    OpportunityThorchain,
    OpportunityCexDex,
    OpportunityBybit,
    OpportunityMaya,
    OpportunityDexDex
)
from classes.Balances import Balances

from multiprocessing import Lock 

httpClient = requests.Session()


def executeBybitOpportunity(balances: Balances, bybitOpportunity: OpportunityBybit):
    try:
        asset_in_symbol = bybitOpportunity.pairAsset.assetIn.symbol
        asset_out_symbol = bybitOpportunity.pairAsset.assetOut.symbol
        amount = float(bybitOpportunity.amountInEstimated)
        pair_symbol = bybitOpportunity.pairAsset.orderbookSymbol
        isSellBoolean = isSell(asset_in_symbol, asset_out_symbol)
        amount_in, amount_out, order_id = place_order(
            pair_symbol, isSellBoolean, amount, httpClient
        )
        bybitOpportunity.amountInReal = float(amount_in)
        bybitOpportunity.amountOutReal = float(amount_out)
        bybitOpportunity.orderId = order_id
    
    except Exception as e:
        logging.warning(f"Erreur lors de l'execution de la transaction Bybit' : {e}")



def executeThorchainOnBlockOpportunity(
    balances: Balances, opportunity: OpportunityThorchain, lock:Lock, balanceDictShared:Dict, sharedCounter
):
    try:
        txHash = executeThorchainOpportunity(opportunity=opportunity)
        opportunity.txHash = txHash.text
        logging.info(f"checking txStatus loading... {opportunity.txHash}")
        isTxThorchainSuccess = checkThorchainTxStatus(txHash=opportunity.txHash)
        
        opportunity.amountOutReal, opportunity.realBlock = getAmountOutRealFromTxThorchain(opportunity.txHash)
        updateBalanceDictWithSingleOpp(opportunity=opportunity,balanceDict=balanceDictShared, isOppSuccess=isTxThorchainSuccess, isEstimated=False, lock=lock)


        logging.info(f'executeThorchainOnBlockOpportunity balance update, {balanceDictShared}')

        writeDataOpp(
            opportunity=opportunity,
            isTxThorchainSuccess=isTxThorchainSuccess,
            balances=balances,
        )
        
        with lock:
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update FROM {sharedCounter} ')
            sharedCounter.value = sharedCounter.value - 1
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update TO {sharedCounter} ')
        
        

    except Exception as err:
        logging.warning(f"executeThorchainOnBlockOpportunity error {err}")
        # traceback.print_exc()


def executeMayaOnBlockOpportunity(
    balances: Balances, opportunity: OpportunityMaya, lock:Lock, balanceDictShared:Dict, sharedCounter
):
    try:
        txHash = executeMayaOpportunity(opportunity=opportunity)
        logging.info(f"checking maya txStatus loading... {opportunity.txHash}")
        opportunity.txHash = txHash.text
        isTxMayaSuccess = checkMayaTxStatus(txHash=opportunity.txHash)

        opportunity.amountOutReal, opportunity.realBlock = getAmountOutRealFromTxMaya(opportunity.txHash)
        updateBalanceDictWithSingleOpp(opportunity=opportunity,balanceDict=balanceDictShared, isOppSuccess=isTxMayaSuccess, isEstimated=False, lock=lock)


        logging.info(f'executeMayaOnBlockOpportunity balance update, {balanceDictShared}')

        writeDataOppMaya(
            opportunity=opportunity,
            isTxThorchainSuccess=isTxMayaSuccess,
            balances=balances,
        )

        with lock:
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update FROM {sharedCounter} ')
            sharedCounter.value = sharedCounter.value - 1
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update TO {sharedCounter} ')
        

    except Exception as err:
        print(f"executeMayaOnBlockOpportunity error {err}")
        traceback.print_exc()



def executeCexDexOpportunity(balances: Balances, opportunity: OpportunityCexDex, lock:Lock, balanceDictShared:Dict, sharedCounter):
    try:
        txHash = executeThorchainOpportunity(opportunity=opportunity)
        opportunity.opportunityThorchain.txHash = txHash.text
        logging.info(
            f"checking txStatus loading... {opportunity.opportunityThorchain.txHash}"
        )
        isTxThorchainSuccess = checkThorchainTxStatus(
            txHash=opportunity.opportunityThorchain.txHash
        )
        opportunity.opportunityThorchain.amountOutReal, opportunity.opportunityThorchain.realBlock = getAmountOutRealFromTxThorchain(opportunity.opportunityThorchain.txHash)

        if isTxThorchainSuccess == True:
            executeBybitOpportunity(
                balances=balances, bybitOpportunity=opportunity.opportunityBybit
            )

        updateBalanceDictWithDoubleOpp(opportunity1=opportunity.opportunityThorchain, opportunity2=opportunity.opportunityBybit, balanceDict=balanceDictShared, isOppSuccess=isTxThorchainSuccess, isEstimated=False, lock=lock)

        logging.info(
            f"executeCexDexOpportunity completed for : txHash : {opportunity.opportunityThorchain.txHash} orderID : {opportunity.opportunityBybit.orderId}"
        )

        logging.info(f'executeCexDexOpportunity balance update, {balanceDictShared}')


        writeDataOpp(
            opportunity=opportunity,
            isTxThorchainSuccess=isTxThorchainSuccess,
            balances=balances,
        )

        with lock:
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update FROM {sharedCounter} ')
            sharedCounter.value = sharedCounter.value - 1
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update TO {sharedCounter} ')
        

    except Exception as err:
        logging.warning(f"executeCexDexOpportunity error {err}")
        # traceback.print_exc()


def executeMayaCexDexOpportunity(balances: Balances, opportunity: OpportunityCexDex, lock:Lock, balanceDictShared:Dict, sharedCounter):
    try:
        txHash = executeMayaOpportunity(opportunity=opportunity)
        opportunity.opportunityThorchain.txHash = txHash.text

        logging.info(f"checking maya txStatus loading... {opportunity.opportunityThorchain.txHash}")

        isTxMayaSuccess = checkMayaTxStatus(txHash=opportunity.opportunityThorchain.txHash)

        opportunity.opportunityThorchain.amountOutReal, opportunity.opportunityThorchain.realBlock = getAmountOutRealFromTxMaya(opportunity.opportunityThorchain.txHash)

        if isTxMayaSuccess == True:
            executeBybitOpportunity(balances=balances, bybitOpportunity=opportunity.opportunityBybit)
        
        updateBalanceDictWithDoubleOpp(opportunity1=opportunity.opportunityThorchain, opportunity2=opportunity.opportunityBybit, balanceDict=balanceDictShared, isOppSuccess=isTxMayaSuccess, isEstimated=False, lock=lock)

        logging.info(f"executeMayaCexDexOpportunity completed for : maya txHash : {opportunity.opportunityThorchain.txHash} orderID : {opportunity.opportunityBybit.orderId}")

        logging.info(f'executeMayaCexDexOpportunity balance update, {balanceDictShared}')

        writeDataOppMaya(
            opportunity=opportunity,
            isTxThorchainSuccess=isTxMayaSuccess,
            balances=balances,
        )

        with lock:
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update FROM {sharedCounter} ')
            sharedCounter.value = sharedCounter.value - 1
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update TO {sharedCounter} ')
        

    except Exception as err:
        print(f"executeMayaCexDexOpportunity error {err}")
        # traceback.print_exc()



def executeMayaThorOpportunity(balances: Balances, opportunity: OpportunityDexDex, lock:Lock, balanceDictShared:Dict, sharedCounter):
    try:
        txHash = executeMayaOpportunity(opportunity=opportunity)
        opportunity.opportunityMaya.txHash = txHash.text
        logging.info(
            f"executeMayaThorOpportunity - checking maya txStatus loading... {opportunity.opportunityMaya.txHash}"
        )
        isTxMayaSuccess = checkMayaTxStatus(
            txHash=opportunity.opportunityMaya.txHash
        )

        opportunity.opportunityMaya.amountOutReal, opportunity.opportunityMaya.realBlock = getAmountOutRealFromTxMaya(opportunity.opportunityMaya.txHash)
        
        logging.info(f'executeMayaThorOpportunity MAYATHOR -  opportunity.opportunityMaya.amountOutReal {opportunity.opportunityMaya.amountOutReal}')

        if isTxMayaSuccess == True:
            txHashThor = executeThorchainOpportunity(opportunity=opportunity)
            opportunity.opportunityThorchain.txHash = txHashThor.text
            logging.info(
                f"executeMayaThorOpportunity - checking thor txStatus loading... {opportunity.opportunityThorchain.txHash}"
            )
            isTxThorchainSuccess = checkThorchainTxStatus(
                txHash=opportunity.opportunityThorchain.txHash
            )
        
            opportunity.opportunityThorchain.amountOutReal, opportunity.opportunityThorchain.realBlock = getAmountOutRealFromTxThorchain(opportunity.opportunityThorchain.txHash)
            logging.info(f'executeMayaThorOpportunity - opportunity.opportunityThorchain.amountOutReal {opportunity.opportunityThorchain.amountOutReal} opportunity.opportunityThorchain.realBlock {opportunity.opportunityThorchain.realBlock}')
        

        updateBalanceDictWithDoubleOpp(opportunity1=opportunity.opportunityMaya, opportunity2=opportunity.opportunityThorchain, balanceDict=balanceDictShared, isOppSuccess=isTxMayaSuccess, isEstimated=False, lock=lock)

        logging.info(f'executeMayaThorOpportunity balance update, {balanceDictShared}')


        with lock:
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update FROM {sharedCounter} ')
            sharedCounter.value = sharedCounter.value - 1
            logging.info(f'executeThorchainOnBlockOpportunity sharedCounter update TO {sharedCounter} ')
            
        writeDataOppMaya(
            opportunity=opportunity,
            isTxThorchainSuccess=isTxMayaSuccess,
            balances=balances,
        )
        

        

    except Exception as err:
        print(f"executeMayaThorOpportunity error {err}")
        # traceback.print_exc()
