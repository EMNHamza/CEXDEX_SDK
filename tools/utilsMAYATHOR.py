from typing import List

from classes.Pair import PairDexDex 
from classes.Opportunity import OpportunityMaya, OpportunityThorchain, OpportunityDexDex
from classes.Balances import BalancesThorchain

from constantes.constantes import DECIMALS_CACAO, DECIMALS_RUNE

from utilsMaya.mayaCalcul import getValueOfAssetInCacao, getValueOfCacaoInAsset, getValueInDollarsMaya
from utilsThorchain.thorchainCalcul import getValueInDollarsThorchain 
from copy import deepcopy
import logging

def createPairsDexDex(pairsDex1, pairsDex2) -> List[PairDexDex]:
    pairsDexDex = []
    for pairDex1 in pairsDex1:
        for pairDex2 in pairsDex2:
            if pairDex1.assetIn.assetType == pairDex2.assetOut.assetType and pairDex1.assetOut.assetType == pairDex2.assetIn.assetType and pairDex1.assetIn.assetType != pairDex1.assetOut.assetType:
                pairCexDex = PairDexDex(pairAssetDex1=pairDex1, pairAssetDex2=pairDex2)
                pairsDexDex.append(pairCexDex)
    return pairsDexDex


def getAmountInMaxDexDex(firstPairToExecute, secondPairToExecute):

    balanceSecondPairAssetInConvertedToFirstPairAssetIn = convertAssetInSecondPairToAssetInFirstPair(firstPairToExecute, secondPairToExecute)
    
    amountInMax = (
        min(
            balanceSecondPairAssetInConvertedToFirstPairAssetIn,
            (
                firstPairToExecute.assetIn.balance
                / 10**firstPairToExecute.assetIn.decimals
            ),
        )
        * 0.99
    )  # peut être ajouter * 0.999 oui car on utilise bybit pour calculer le montant thorchain
    # print(f'getAmountInMax - amountInMax {amountInMax}')
    # print(f'getAmountInMax - amountInMax {amountInMax} firstPairToExecute.assetIn.balance {firstPairToExecute.assetIn.balance/ 10**firstPairToExecute.assetIn.decimals} balanceSecondPairAssetInConvertedToFirstPairAssetIn {balanceSecondPairAssetInConvertedToFirstPairAssetIn} ')
    return amountInMax


def convertAssetInSecondPairToAssetInFirstPair(firstPairToExecute, secondPairToExecute):
    balanceAssetInSecondPair = secondPairToExecute.assetIn.balance/ 10**secondPairToExecute.assetIn.decimals
    
    balanceAssetInSecondPair = balanceAssetInSecondPair * 10 ** DECIMALS_CACAO

    assetInMaya = firstPairToExecute.assetIn
    assetOutMaya = firstPairToExecute.assetOut

    poolMayaAssetIn = deepcopy(assetInMaya.pool)
    poolMayaAssetOut = deepcopy(assetOutMaya.pool)

    balanceAssetInInPool = poolMayaAssetIn.balanceAssetInPool
    balanceAssetOutInPool = poolMayaAssetOut.balanceAssetInPool

    poolMayaAssetIn.balanceAssetInPool = balanceAssetInInPool * 10**DECIMALS_CACAO / 10**assetInMaya.decimals
    poolMayaAssetOut.balanceAssetInPool = balanceAssetOutInPool * 10**DECIMALS_CACAO / 10**assetOutMaya.decimals

    valueInCacao = getValueOfAssetInCacao(amount=balanceAssetInSecondPair,pool=poolMayaAssetOut)
    valueInAssetInFirstPair = getValueOfCacaoInAsset(amount=valueInCacao,pool=poolMayaAssetIn) / 10 ** DECIMALS_CACAO

    return valueInAssetInFirstPair 


def createOpportunityDexDex(pairDexDex:PairDexDex, opportunityThorchain: OpportunityThorchain, opportunityMaya: OpportunityMaya, balancesThorchain:BalancesThorchain):
    opportunityDexDex = OpportunityDexDex(pairDexDex=pairDexDex, opportunityThorchain=opportunityThorchain, opportunityMaya=opportunityMaya, gainAssetInDexEstimated=0, gainAssetInDexReal=0, gainAssetOutDexEstimated=0, gainAssetOutDexReal=0, gainTotalEstimated=0, gainTotalReal=0)

    opportunityDexDex = calculateGainOpportunityDexDex(opportunityDexDex=opportunityDexDex, isEstimated=True, balancesThorchain=balancesThorchain)

    return opportunityDexDex


def calculateGainOpportunityDexDex(opportunityDexDex:OpportunityDexDex, balancesThorchain:BalancesThorchain, isEstimated:bool):

    amountInDex1 = opportunityDexDex.opportunityMaya.amountIn / 10**opportunityDexDex.opportunityMaya.pairAsset.assetIn.decimals
    amountInDex2 = opportunityDexDex.opportunityThorchain.amountIn / 10**opportunityDexDex.opportunityThorchain.pairAsset.assetIn.decimals
        
    if isEstimated == True:
        amountOutDex1 = opportunityDexDex.opportunityMaya.amountOutEstimated / 10**opportunityDexDex.opportunityMaya.pairAsset.assetOut.decimals
        amountOutDex2 = opportunityDexDex.opportunityThorchain.amountOutEstimated / 10**opportunityDexDex.opportunityThorchain.pairAsset.assetOut.decimals
    else:
        amountOutDex1 = opportunityDexDex.opportunityMaya.amountOutReal / 10**opportunityDexDex.opportunityMaya.pairAsset.assetOut.decimals
        amountOutDex2 = opportunityDexDex.opportunityThorchain.amountOutReal / 10**opportunityDexDex.opportunityThorchain.pairAsset.assetOut.decimals

    gainAssetInDex1 = amountOutDex2 - amountInDex1
    gainAssetOutDex1 = amountOutDex1 - amountInDex2

    gainAssetInDex1InDollars = getValueInDollarsThorchain(amount=gainAssetInDex1*10**DECIMALS_RUNE,asset=opportunityDexDex.opportunityThorchain.pairAsset.assetOut, balancesThorchain=balancesThorchain)
    gainAssetOutDex1InDollars = getValueInDollarsThorchain(amount=gainAssetOutDex1*10**DECIMALS_RUNE,asset=opportunityDexDex.opportunityThorchain.pairAsset.assetIn, balancesThorchain=balancesThorchain)
    
    gainTotalInDollars = (gainAssetInDex1InDollars + gainAssetOutDex1InDollars ) / 10**DECIMALS_RUNE
    
    

    if isEstimated == True:
        opportunityDexDex.gainAssetInDexEstimated = gainAssetInDex1
        opportunityDexDex.gainAssetOutDexEstimated = gainAssetOutDex1
        opportunityDexDex.gainTotalEstimated = gainTotalInDollars
    else:
        logging.info(f'gainAssetInDex1InDollars {gainAssetInDex1InDollars} gainAssetOutDex1InDollars {gainAssetOutDex1InDollars} gainTotalInDollars {gainTotalInDollars}')
        opportunityDexDex.gainAssetInDexReal = gainAssetInDex1
        opportunityDexDex.gainAssetOutDexReal = gainAssetOutDex1
        opportunityDexDex.gainTotalReal = gainTotalInDollars

    return opportunityDexDex
