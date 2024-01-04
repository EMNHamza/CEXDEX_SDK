import csv 
from datetime import datetime
from classes.Opportunity import OpportunityBybit, OpportunityCexDex, OpportunityThorchain, OpportunityMaya, OpportunityDexDex
from classes.Balances import Balances
from utilsThorchain.thorchainCalcul import getAmountOutRealFromTxThorchain, getValueInDollarsThorchain, getValueOfRuneInDollars
from utilsMaya.mayaCalcul import getAmountOutRealFromTxMaya, getValueInDollarsMaya
from tools.utilsCEXDEX import calculateGainOpportunityCexDex
from tools.utilsMAYATHOR import calculateGainOpportunityDexDex
from constantes.constantes import DECIMALS_RUNE, DECIMALS_CACAO, NETWORK_FEES_CACAO
import logging
import copy



def writeInCSV(fileName: str, rowToAdd: list):
    with open(fileName, "a", newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(rowToAdd)



def writeDataOpp(opportunity, isTxThorchainSuccess: bool, balances:Balances):
    
    current_datetime = datetime.now()
    formatted_date = current_datetime.date().strftime("%Y-%m-%d")
    formatted_time = current_datetime.time().strftime("%H:%M:%S")
    
    
    if isinstance(opportunity, OpportunityCexDex):
        typeOpp = 'CEXDEXTHORCHAIN'
        networkFeesRune = opportunity.opportunityThorchain.outboundFees
        opportunity.opportunityThorchain.amountOutReal -=  networkFeesRune
        opportunity = calculateGainOpportunityCexDex(opportunityCexDex=opportunity, isEstimated=False)

        txStatus = ""
        if isTxThorchainSuccess == True:
            txStatus = 'OK'
        else:
            txStatus = 'REVERTED'
            opportunity.gainAssetInDexReal = 0
            opportunity.gainAssetOutDexReal = 0
            
            opportunity.opportunityThorchain.amountOutReal +=  networkFeesRune

            if opportunity.opportunityThorchain.pairAsset.assetIn.assetType == 'STABLE':
                networkFeesRune = (opportunity.opportunityBybit.bybitAssetPrice * networkFeesRune / 10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals)
                opportunity.gainTotalReal = (opportunity.opportunityThorchain.amountOutReal/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals) - (opportunity.opportunityThorchain.amountIn/10**opportunity.opportunityThorchain.pairAsset.assetIn.decimals) - networkFeesRune
            else:
                networkFeesRune = (networkFeesRune / 10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals)
                gainTotalReal = opportunity.opportunityThorchain.amountOutReal/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals - opportunity.opportunityThorchain.amountIn /10**opportunity.opportunityThorchain.pairAsset.assetIn.decimals 
                opportunity.gainTotalReal = (gainTotalReal * opportunity.opportunityBybit.bybitAssetPrice) - networkFeesRune
        
        if opportunity.opportunityBybit.amountInReal == 0 and txStatus == 'OK':
            txStatus = 'PROBLEMBYBIT'
            opportunity.gainTotalReal = -3
            
        # txHash = opportunity.opportunityThorchain.txHash.replace
        rowToAdd = [formatted_date, formatted_time, typeOpp, txStatus, opportunity.opportunityThorchain.txHash, opportunity.opportunityBybit.orderId, opportunity.opportunityThorchain.detectedBlock, opportunity.opportunityThorchain.realBlock, "NONE", "NONE", opportunity.opportunityThorchain.pairAsset.assetIn.symbol, opportunity.opportunityThorchain.pairAsset.assetOut.symbol, round(opportunity.opportunityThorchain.amountIn/10**opportunity.opportunityThorchain.pairAsset.assetIn.decimals,8), round(opportunity.opportunityThorchain.amountOutEstimated/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals,8),
                round(opportunity.opportunityThorchain.amountOutReal/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals,8), opportunity.opportunityBybit.pairAsset.assetIn.symbol, opportunity.opportunityBybit.pairAsset.assetOut.symbol, round(opportunity.opportunityBybit.amountInEstimated,8), round(opportunity.opportunityBybit.amountInReal,8), round(opportunity.opportunityBybit.amountOutEstimated,8), round(opportunity.opportunityBybit.amountOutReal,8), round(opportunity.gainAssetInDexEstimated,8), round(opportunity.gainAssetInDexReal,8), round(opportunity.gainAssetOutDexEstimated,8), round(opportunity.gainAssetOutDexReal,8), round(opportunity.gainTotalEstimated,3), round(opportunity.gainTotalReal,3)]

    if isinstance(opportunity, OpportunityThorchain):
        
        networkFeesRune = opportunity.outboundFees
        opportunity.amountOutReal -= networkFeesRune

        opportunity.gainTotalReal = (opportunity.amountOutReal / 10**opportunity.pairAsset.assetOut.decimals) - opportunity.amountIn / 10**opportunity.pairAsset.assetIn.decimals
        
        if opportunity.pairAsset.assetOut.assetType != 'STABLE':
            priceInDollars = opportunity.amountInInDollars / (opportunity.amountIn/10**opportunity.pairAsset.assetIn.decimals)
            opportunity.gainTotalReal = opportunity.gainTotalReal * priceInDollars

        txStatus = ""
        if isTxThorchainSuccess == True:
            txStatus = 'OK'
        else:
            txStatus = 'REVERTED'

        rowToAdd = [formatted_date, formatted_time, opportunity.typeOpp, txStatus, opportunity.txHash, "NONE", opportunity.detectedBlock, opportunity.realBlock,"NONE","NONE", opportunity.pairAsset.assetIn.symbol, opportunity.pairAsset.assetOut.symbol, round(opportunity.amountIn/10**opportunity.pairAsset.assetIn.decimals,8), round(opportunity.amountOutEstimated/10**opportunity.pairAsset.assetOut.decimals,8),
                round(opportunity.amountOutReal/10**opportunity.pairAsset.assetOut.decimals,8), "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", round(opportunity.gainTotalEstimated,3), round(opportunity.gainTotalReal,3)]

    writeInCSV(fileName='csv/dataOpp.csv', rowToAdd=rowToAdd)



def writeDataOppMaya(opportunity, isTxThorchainSuccess: bool, balances:Balances):
    
    current_datetime = datetime.now()
    formatted_date = current_datetime.date().strftime("%Y-%m-%d")
    formatted_time = current_datetime.time().strftime("%H:%M:%S")
    
    
    if isinstance(opportunity, OpportunityCexDex):
        typeOpp='CEXDEXMAYA'
        networkFeesCacao = opportunity.opportunityThorchain.networkFees
        opportunity.opportunityThorchain.amountOutReal -= networkFeesCacao
        opportunity = calculateGainOpportunityCexDex(opportunityCexDex=opportunity, isEstimated=False)
        
        txStatus = ""
        if isTxThorchainSuccess == True:
            txStatus = 'OK'
        else:
            txStatus = 'REVERTED'
            opportunity.gainAssetInDexReal = 0
            opportunity.gainAssetOutDexReal = 0
            
            opportunity.opportunityThorchain.amountOutReal += networkFeesCacao

            if opportunity.opportunityThorchain.pairAsset.assetIn.assetType == 'STABLE':
                networkFeesCacao = (networkFeesCacao*opportunity.opportunityBybit.bybitAssetPrice)/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals
                opportunity.gainTotalReal = (opportunity.opportunityThorchain.amountOutReal/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals) - (opportunity.opportunityThorchain.amountIn/10**opportunity.opportunityThorchain.pairAsset.assetIn.decimals) - networkFeesCacao
            else:
                gainTotalReal = opportunity.opportunityThorchain.amountOutReal/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals - opportunity.opportunityThorchain.amountIn /10**opportunity.opportunityThorchain.pairAsset.assetIn.decimals
                opportunity.gainTotalReal = (gainTotalReal * opportunity.opportunityBybit.bybitAssetPrice) - networkFeesCacao/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals
        
        if opportunity.opportunityBybit.amountInReal == 0 and txStatus == 'OK':
            txStatus = 'PROBLEMBYBIT'
            opportunity.gainTotalReal = -3
        # txHash = opportunity.opportunityThorchain.txHash.replace
        rowToAdd = [formatted_date, formatted_time, typeOpp, txStatus, opportunity.opportunityThorchain.txHash, opportunity.opportunityBybit.orderId, opportunity.opportunityThorchain.detectedBlock, opportunity.opportunityThorchain.realBlock,"NONE","NONE",opportunity.opportunityThorchain.pairAsset.assetIn.symbol, opportunity.opportunityThorchain.pairAsset.assetOut.symbol, round(opportunity.opportunityThorchain.amountIn/10**opportunity.opportunityThorchain.pairAsset.assetIn.decimals,8), round(opportunity.opportunityThorchain.amountOutEstimated/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals,8),
                round(opportunity.opportunityThorchain.amountOutReal/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals,8), opportunity.opportunityBybit.pairAsset.assetIn.symbol, opportunity.opportunityBybit.pairAsset.assetOut.symbol, round(opportunity.opportunityBybit.amountInEstimated,8), round(opportunity.opportunityBybit.amountInReal,8), round(opportunity.opportunityBybit.amountOutEstimated,8), round(opportunity.opportunityBybit.amountOutReal,8), round(opportunity.gainAssetInDexEstimated,8), round(opportunity.gainAssetInDexReal,8), round(opportunity.gainAssetOutDexEstimated,8), round(opportunity.gainAssetOutDexReal,8), round(opportunity.gainTotalEstimated,3), round(opportunity.gainTotalReal,3)]

    if isinstance(opportunity, OpportunityMaya):
        
        txStatus = ""
        if isTxThorchainSuccess == True:
            txStatus = 'OK'
        else:
            txStatus = 'REVERTED'
        
        networkFeesCacao = opportunity.networkFees
        opportunity.amountOutReal -= networkFeesCacao
        opportunity.gainTotalReal = (opportunity.amountOutReal / 10**opportunity.pairAsset.assetOut.decimals) - (opportunity.amountIn / 10**opportunity.pairAsset.assetIn.decimals)
        
        if opportunity.pairAsset.assetOut.assetType != 'STABLE':
            assetOutForValueInDollars=copy.deepcopy(opportunity.pairAsset.assetOut)
            assetOutForValueInDollars.pool.balanceAssetInPool = assetOutForValueInDollars.pool.balanceAssetInPool * 1e2
            opportunity.gainTotalReal = getValueInDollarsMaya(amount=opportunity.gainTotalReal*10**opportunity.pairAsset.assetOut.decimals, asset=assetOutForValueInDollars, balancesMaya=balances.balancesMaya)

        rowToAdd = [formatted_date, formatted_time, opportunity.typeOpp, txStatus, opportunity.txHash, "NONE", opportunity.detectedBlock, opportunity.realBlock, "NONE", "NONE", opportunity.pairAsset.assetIn.symbol, opportunity.pairAsset.assetOut.symbol, round(opportunity.amountIn/10**opportunity.pairAsset.assetIn.decimals,8), round(opportunity.amountOutEstimated/10**opportunity.pairAsset.assetOut.decimals,8),
                round(opportunity.amountOutReal/10**opportunity.pairAsset.assetOut.decimals,8), "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", "NONE", round(opportunity.gainTotalEstimated,3), round(opportunity.gainTotalReal,3)]

    if isinstance(opportunity, OpportunityDexDex):
        # opportunity.opportunityMaya.amountOutReal, opportunity.opportunityMaya.realBlock = getAmountOutRealFromTxMaya(opportunity.opportunityMaya.txHash)
        # opportunity.opportunityThorchain.amountOutReal, opportunity.opportunityThorchain.realBlock = getAmountOutRealFromTxThorchain(opportunity.opportunityThorchain.txHash)
        
        typeOpp='MAYATHOR'

        networkFeesCacao = opportunity.opportunityMaya.networkFees
        opportunity.opportunityMaya.amountOutReal -= networkFeesCacao

        networkFeesRune = opportunity.opportunityThorchain.outboundFees
        opportunity.opportunityThorchain.amountOutReal -=  networkFeesRune
        
        opportunity = calculateGainOpportunityDexDex(opportunityDexDex=opportunity, balancesThorchain=balances.balancesThorchain, isEstimated=False)
        
        txStatus = ""
        if isTxThorchainSuccess == True:
            txStatus = 'OK'
        else:
            txStatus = 'REVERTED'
            opportunity.gainAssetInDexReal = 0
            opportunity.gainAssetOutDexReal = 0
            opportunity.opportunityThorchain.amountOutReal +=  networkFeesRune
            opportunity.opportunityMaya.amountOutReal += networkFeesCacao

            # logging.info(f'writeDataOppMaya MAYATHOR -  opportunity.opportunityMaya.amountOutReal {opportunity.opportunityMaya.amountOutReal}')
            # opportunity.opportunityMaya.amountOutReal += networkFeesCacao

            opportunity.gainTotalReal = opportunity.opportunityMaya.amountOutReal / 10 ** opportunity.opportunityMaya.pairAsset.assetOut.decimals - opportunity.opportunityMaya.amountIn / 10 ** opportunity.opportunityMaya.pairAsset.assetIn.decimals
            # logging.info(f'writeDataOppMaya MAYATHOR -  opportunity.opportunityMaya.gainTotalReal {opportunity.opportunityMaya.gainTotalReal}')

            assetInCopy = copy.deepcopy(opportunity.opportunityMaya.pairAsset.assetIn)
            assetInCopy.pool.balanceAssetInPool = assetInCopy.pool.balanceAssetInPool * 1e2
            assetOutCopy = copy.deepcopy(opportunity.opportunityMaya.pairAsset.assetOut)
            assetOutCopy.pool.balanceAssetInPool = assetOutCopy.pool.balanceAssetInPool * 1e2

            networkFeesCacaoInDollars = getValueInDollarsMaya(amount=networkFeesCacao*(10**DECIMALS_CACAO/10**assetOutCopy.decimals),asset=assetOutCopy,balancesMaya=balances.balancesMaya) / 10**DECIMALS_CACAO

            if opportunity.opportunityMaya.pairAsset.assetIn.assetType != 'STABLE':
                opportunity.gainTotalReal = (getValueInDollarsMaya(amount=opportunity.gainTotalReal*10**DECIMALS_CACAO,asset=assetInCopy,balancesMaya=balances.balancesMaya) / 10**DECIMALS_CACAO) - networkFeesCacaoInDollars
            else:
                opportunity.gainTotalReal = opportunity.gainTotalReal - networkFeesCacaoInDollars
            
            # logging.info(f'writeDataOppMaya MAYATHOR -  opportunity.opportunityMaya.gainTotalReal in DOLLARS {opportunity.opportunityMaya.gainTotalReal}')
        if opportunity.opportunityThorchain.amountIn == 0 and txStatus == 'OK':
            txStatus = 'PROBLEMTHOR'
            opportunity.gainTotalReal = -3
        # txHash = opportunity.opportunityThorchain.txHash.replace
            
        rowToAdd = [formatted_date, formatted_time, typeOpp, txStatus, opportunity.opportunityMaya.txHash, opportunity.opportunityThorchain.txHash, opportunity.opportunityMaya.detectedBlock, opportunity.opportunityMaya.realBlock, opportunity.opportunityThorchain.detectedBlock, opportunity.opportunityThorchain.realBlock, opportunity.opportunityMaya.pairAsset.assetIn.symbol, opportunity.opportunityMaya.pairAsset.assetOut.symbol, round(opportunity.opportunityMaya.amountIn/10**opportunity.opportunityMaya.pairAsset.assetIn.decimals,8), round(opportunity.opportunityMaya.amountOutEstimated/10**opportunity.opportunityMaya.pairAsset.assetOut.decimals,8),
                round(opportunity.opportunityMaya.amountOutReal/10**opportunity.opportunityMaya.pairAsset.assetOut.decimals,8), opportunity.opportunityThorchain.pairAsset.assetIn.symbol, opportunity.opportunityThorchain.pairAsset.assetOut.symbol, round(opportunity.opportunityThorchain.amountIn/10**opportunity.opportunityThorchain.pairAsset.assetIn.decimals,8), round(opportunity.opportunityThorchain.amountIn/10**opportunity.opportunityThorchain.pairAsset.assetIn.decimals,8), round(opportunity.opportunityThorchain.amountOutEstimated/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals,8), round(opportunity.opportunityThorchain.amountOutReal/10**opportunity.opportunityThorchain.pairAsset.assetOut.decimals,8), round(opportunity.gainAssetInDexEstimated,8), round(opportunity.gainAssetInDexReal,8), round(opportunity.gainAssetOutDexEstimated,8), round(opportunity.gainAssetOutDexReal,8), round(opportunity.gainTotalEstimated,3), round(opportunity.gainTotalReal,3)]



    writeInCSV(fileName='csv/dataOpp.csv', rowToAdd=rowToAdd)