from classes.Opportunity import OpportunityBybit, OpportunityThorchain, OpportunityCexDex
from classes.Pair import PairCexDex

from utilsBybit.bybit_utils import getSymbol, orderbook_average_price
from typing import List

import logging


def calculateGainOpportunityCexDex(opportunityCexDex:OpportunityCexDex, isEstimated):

    amountInDex = opportunityCexDex.opportunityThorchain.amountIn / 10**opportunityCexDex.opportunityThorchain.pairAsset.assetIn.decimals

    if isEstimated == True:
        amountInBybit = opportunityCexDex.opportunityBybit.amountInEstimated
        amountOutBybit = opportunityCexDex.opportunityBybit.amountOutEstimated
        amountOutDex = opportunityCexDex.opportunityThorchain.amountOutEstimated / 10**opportunityCexDex.opportunityThorchain.pairAsset.assetOut.decimals
    else:
        amountInBybit = opportunityCexDex.opportunityBybit.amountInReal
        amountOutBybit = opportunityCexDex.opportunityBybit.amountOutReal
        amountOutDex = opportunityCexDex.opportunityThorchain.amountOutReal / 10**opportunityCexDex.opportunityThorchain.pairAsset.assetOut.decimals

    gainAssetInDex = amountOutBybit - amountInDex
    gainAssetOutDex = amountOutDex - amountInBybit
    
    if opportunityCexDex.pairCexDex.pairAssetDex.assetIn.assetType == 'STABLE':
        priceAssetInDexInDollars = 1
        priceAssetOutDexInDollars = orderbook_average_price(orderbook_data=opportunityCexDex.pairCexDex.pairAssetCex.orderbook, amount=gainAssetOutDex, isSell=True)
    else:
        priceAssetInDexInDollars = orderbook_average_price(orderbook_data=opportunityCexDex.pairCexDex.pairAssetCex.orderbook, amount=gainAssetInDex, isSell=True)
        priceAssetOutDexInDollars = 1
        
    if priceAssetInDexInDollars == 0:
        priceAssetInDexInDollars = orderbook_average_price(orderbook_data=opportunityCexDex.pairCexDex.pairAssetCex.orderbook, amount=1, isSell=True)
    elif priceAssetOutDexInDollars == 0:
        priceAssetOutDexInDollars = orderbook_average_price(orderbook_data=opportunityCexDex.pairCexDex.pairAssetCex.orderbook, amount=1, isSell=True)


    gainAssetInInDollars = gainAssetInDex * priceAssetInDexInDollars
    gainAssetOutInDollars = gainAssetOutDex * priceAssetOutDexInDollars
    
    gainTotalInDollars = gainAssetInInDollars + gainAssetOutInDollars
    
    # logging.info(f'calculateGainOpportunityCexDex - amountInDex  {amountInDex} {opportunityCexDex.opportunityThorchain.pairAsset.assetIn.symbol} amountOutDex {amountOutDex} {opportunityCexDex.opportunityThorchain.pairAsset.assetOut.symbol} amountInBybit {amountInBybit} {opportunityCexDex.opportunityBybit.pairAsset.assetIn.symbol}  amountOutBybit {amountOutBybit} {opportunityCexDex.opportunityBybit.pairAsset.assetOut.symbol} ')
    # logging.info(f'calculateGainOpportunityCexDex - gainAssetInDex {gainAssetInDex} gainAssetOutDex {gainAssetOutDex} gainAssetInInDollars {gainAssetInInDollars} gainAssetOutInDollars {gainAssetOutInDollars} gainTotalInDollars {gainTotalInDollars} priceAssetInDexInDollars {priceAssetInDexInDollars} priceAssetOutDexInDollars {priceAssetOutDexInDollars}')

    if isEstimated == True:
        opportunityCexDex.gainAssetInDexEstimated = gainAssetInDex
        opportunityCexDex.gainAssetOutDexEstimated = gainAssetOutDex
        opportunityCexDex.gainTotalEstimated = gainTotalInDollars
    else:
        opportunityCexDex.gainAssetInDexReal = gainAssetInDex
        opportunityCexDex.gainAssetOutDexReal = gainAssetOutDex
        opportunityCexDex.gainTotalReal = gainTotalInDollars

    return opportunityCexDex


def createOpportunityCexDex(pairCexDex:PairCexDex, opportunityThorchain: OpportunityThorchain, opportunityBybit: OpportunityBybit):
    opportunityCexDex = OpportunityCexDex(pairCexDex=pairCexDex, opportunityThorchain=opportunityThorchain, opportunityBybit=opportunityBybit, gainAssetInDexEstimated=0, gainAssetInDexReal=0, gainAssetOutDexEstimated=0, gainAssetOutDexReal=0, gainTotalEstimated=0, gainTotalReal=0)

    opportunityCexDex = calculateGainOpportunityCexDex(opportunityCexDex=opportunityCexDex, isEstimated=True)

    return opportunityCexDex


def scoutOpportunityCexDex(listOpportunities: List):
    listSuccessOpportunities = []
    opportunity: OpportunityCexDex
    for opportunity in listOpportunities:
        if opportunity.gainNetEstimated > 0:
            listSuccessOpportunities.append(opportunity)

    return listSuccessOpportunities


def createPairsCexDex(pairsCex, pairsDex) -> List[PairCexDex]:
    pairsCexDex = []
    for pairCex in pairsCex:
        for pairDex in pairsDex:
            if pairCex.assetIn.assetType == pairDex.assetOut.assetType and pairCex.assetOut.assetType == pairDex.assetIn.assetType:
                if pairCex.assetIn.assetType =='STABLE' or pairCex.assetOut.assetType=='STABLE':
                    pairCexDex = PairCexDex(pairAssetCex=pairCex, pairAssetDex=pairDex)
                    pairsCexDex.append(pairCexDex)
    return pairsCexDex
