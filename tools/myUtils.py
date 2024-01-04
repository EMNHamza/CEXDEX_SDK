import csv
import requests
import logging
import json

from constantes.url import URL_MIMIR_THOR, URL_INBOUND_ADD_THOR
from constantes.constantes import NETWORK_FEES_RUNE, NETWORK_FEES_CACAO, DECIMALS_CACAO, DECIMALS_RUNE, MAX_SYNTH_PER_POOL_DEPTH_MAYA

from utilsThorchain.thorchainInteraction import getThorchainBalances
from utilsThorchain.thorchainCalcul import (
    getThorchainWalletValue,
    getValueOfDollarsInAssetThorchain,
)
from utilsMaya.mayaInteraction import getMayaBalances

from utilsBybit.bybit_utils import getBybitBalances, isSell

from classes.Pair import PairCex, PairDex, PairCexDex
from classes.Asset import AssetThorchain, AssetBybit, AssetMaya
from classes.Opportunity import OpportunityThorchain, OpportunityCexDex, OpportunityMaya, OpportunityDexDex
from classes.Pool import Pool, PoolMaya
from classes.Balances import Balances, BalancesThorchain, BalancesBybit, BalancesMaya

from utilsBybit.bybit_utils import orderbook_average_price, getSymbol
from typing import List, Dict
from copy import deepcopy

from multiprocessing import Lock

def updateAssetBalances(assetList, balancesData):
    # Loop through each Asset object in the asset list
    for asset in assetList:
        # If the asset's symbol is in the balances dictionary, update its balance
        if asset.balanceName in balancesData:
            asset.balance = float(balancesData[asset.balanceName])
        else:
            asset.balance = 0.0

    # Return the updated asset list
    return assetList


def updateRequestBalanceData(assetList, balancesData):
    # Loop through each Asset object in the asset list
    for asset in assetList:
        # If the asset's symbol is in the balances dictionary, update its balance
        if asset.balanceName not in balancesData:
            balancesData[asset.balanceName] = 0.0
            
    return balancesData

def updateBalances(balances: Balances):
    balancesDataThorchain = getThorchainBalances()
    balancesDataBybit = getBybitBalances()

    balancesThorchain = BalancesThorchain(
        listAssets=updateAssetBalances(
            assetList=balances.balancesThorchain, balancesData=balancesDataThorchain
        )
    )
    balancesBybit = BalancesBybit(
        listAssets=updateAssetBalances(
            assetList=balances.balancesBybit, balancesData=balancesDataBybit
        )
    )

    balances.balancesThorchain = balancesThorchain
    balances.balancesBybit = balancesBybit


def updateAssetPool(balances: Balances):
    balancesDataThorchain = getThorchainBalances()
    balancesDataBybit = getBybitBalances()

    balancesThorchain = BalancesThorchain(
        listAssets=updateAssetBalances(
            assetList=balances.balancesThorchain, balancesData=balancesDataThorchain
        )
    )
    balancesBybit = BalancesBybit(
        listAssets=updateAssetBalances(
            assetList=balances.balancesBybit, balancesData=balancesDataBybit
        )
    )

    balances.balancesThorchain = balancesThorchain
    balances.balancesBybit = balancesBybit


def createAssetsFromJSON(assetClass):
    file_path = f"constantes/myAssets/{assetClass.__name__}.json"
    with open(file_path, "r") as file:
        json_data = json.load(file)

    assets = []
    for key, value in json_data.items():
        # Initialize a dictionary for constructor arguments
        init_args = {}

        # Get all the constructor argument names, excluding 'self'
        arg_names = assetClass.__init__.__code__.co_varnames[
            1 : assetClass.__init__.__code__.co_argcount
        ]

        for field in arg_names:
            if field in value:
                # Add the fields present in the JSON
                init_args[field] = value[field]
            else:
                # Provide None or some default value if the field is missing
                # You can customize the default value as per your class design
                init_args[field] = None

        # Create an instance of the class with the collected arguments
        asset = assetClass(**init_args)
        assets.append(asset)

    # for asset in assets:
    #     print(f"Symbol: {asset.symbol}, AssetType: {asset.assetType}, BalanceName: {asset.balanceName}, Balance: {asset.balance}, Decimals: {asset.decimals}")

    return assets


def createPairsForBalanceType(listAssets, orderbook):
    pairs = []
    for assetIn in listAssets:
        for assetOut in listAssets:
            if assetIn.symbol != assetOut.symbol:
                if isinstance(assetIn, AssetThorchain):
                    pairDex = PairDex(
                        assetIn=assetIn, assetOut=assetOut, type="THORCHAIN"
                    )
                    pairs.append(pairDex)

                if isinstance(assetIn, AssetBybit):
                    if(assetIn.assetType=='STABLE' or assetOut.assetType=='STABLE'):
                        symbolPair = getSymbol(
                            symbolIn=assetIn.symbol, symbolOut=assetOut.symbol
                        )
                        pairCex = PairCex(
                            assetIn=assetIn,
                            assetOut=assetOut,
                            type="BYBIT",
                            orderbookSymbol=symbolPair,
                            orderbook=orderbook[symbolPair],
                        )
                        pairs.append(pairCex)

                if isinstance(assetIn, AssetMaya):
                    pairDex = PairDex(assetIn=assetIn, assetOut=assetOut, type="MAYA")
                    pairs.append(pairDex)

    return pairs


def dichotomie(
    f,
    low,
    high,
    e,
    poolIn: Pool,
    poolOut: Pool,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    orderbookData: Dict,
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


def getAmountInMax(firstPairToExecute, secondPairToExecute):
    isSell_ = isSell(
        symbolIn=secondPairToExecute.assetIn.symbol,
        symbolOut=secondPairToExecute.assetOut.symbol,
    )

    if isSell_:
        priceAssetInCex = orderbook_average_price(
            orderbook_data=secondPairToExecute.orderbook,
            amount=secondPairToExecute.assetIn.balance
            / 10**secondPairToExecute.assetIn.decimals,
            isSell=True,
        )
        balanceSecondPairAssetInConvertedToFirstPairAssetIn = (
            secondPairToExecute.assetIn.balance
            / 10**secondPairToExecute.assetIn.decimals
        ) * priceAssetInCex
    else:
        priceAssetOutCex = orderbook_average_price(
            orderbook_data=secondPairToExecute.orderbook,
            amount=secondPairToExecute.assetIn.balance
            / 10**secondPairToExecute.assetIn.decimals,
            isSell=False,
        )
        if priceAssetOutCex != 0:
            balanceSecondPairAssetInConvertedToFirstPairAssetIn = (
                secondPairToExecute.assetIn.balance
                / 10**secondPairToExecute.assetIn.decimals
            ) / priceAssetOutCex
        else:
            balanceSecondPairAssetInConvertedToFirstPairAssetIn = 0

    # print(f'getAmountInMax - priceAsset {priceAsset} balanceSecondPairAssetInConvertedToFirstPairAssetIn {balanceSecondPairAssetInConvertedToFirstPairAssetIn}')
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

    return amountInMax


def getAmountInMaxCexDex(firstPairToExecute, secondPairToExecute, balances: Balances):
    isSellOnBybit_ = isSell(
        symbolIn=secondPairToExecute.assetIn.symbol,
        symbolOut=secondPairToExecute.assetOut.symbol,
    )

    if isinstance(firstPairToExecute.assetIn, AssetThorchain):
        dexWalletValue = getThorchainWalletValue(balances.balancesThorchain)
    
    # logging.info(f'getAmountInMaxCexDex - isSellOnBybit_ {isSellOnBybit_}, amount {secondPairToExecute.assetIn.balance/ 10**secondPairToExecute.assetIn.decimals} secondPairToExecute.orderbook {secondPairToExecute.orderbook} ')
    if isSellOnBybit_:
        
        priceAssetInCex = orderbook_average_price(
            orderbook_data=secondPairToExecute.orderbook,
            amount=secondPairToExecute.assetIn.balance
            / 10**secondPairToExecute.assetIn.decimals,
            isSell=True,
        )
        balanceSecondPairAssetInConvertedToFirstPairAssetIn = (
            secondPairToExecute.assetIn.balance
            / 10**secondPairToExecute.assetIn.decimals
        ) * priceAssetInCex
        
        # logging.info(f'dex wallet value : {dexWalletValue}, priceAssetInCex {priceAssetInCex}')

        assetOutMaxBalance = (
            dexWalletValue
            * firstPairToExecute.assetOut.maxBalancePercentage
            / priceAssetInCex
        )
        assetOutCurrentBalance = firstPairToExecute.assetOut.balance/10**firstPairToExecute.assetOut.decimals
        remainingOutBalance = assetOutMaxBalance - assetOutCurrentBalance
        maxDexInputAmount = remainingOutBalance * priceAssetInCex
    else:
        priceAssetOutCex = orderbook_average_price(
            orderbook_data=secondPairToExecute.orderbook,
            amount=secondPairToExecute.assetIn.balance
            / 10**secondPairToExecute.assetIn.decimals,
            isSell=False,
        )

        assetOutMaxBalance = (
            dexWalletValue * firstPairToExecute.assetOut.maxBalancePercentage
        )
        assetOutCurrentBalance = firstPairToExecute.assetOut.balance/10**firstPairToExecute.assetOut.decimals
        remainingOutBalance = assetOutMaxBalance - assetOutCurrentBalance
        maxDexInputAmount = remainingOutBalance / priceAssetOutCex

        if priceAssetOutCex != 0:
            balanceSecondPairAssetInConvertedToFirstPairAssetIn = (
                secondPairToExecute.assetIn.balance
                / 10**secondPairToExecute.assetIn.decimals
            ) / priceAssetOutCex
        else:
            balanceSecondPairAssetInConvertedToFirstPairAssetIn = 0

    if remainingOutBalance < 0:
        maxDexInputAmount = 0
    # print(f'getAmountInMax - priceAsset {priceAsset} balanceSecondPairAssetInConvertedToFirstPairAssetIn {balanceSecondPairAssetInConvertedToFirstPairAssetIn}')
    amountInMax = (
        min(
            balanceSecondPairAssetInConvertedToFirstPairAssetIn,
            (
                firstPairToExecute.assetIn.balance
                / 10**firstPairToExecute.assetIn.decimals
            ),
            maxDexInputAmount / 10**firstPairToExecute.assetIn.decimals,
        )
        * 0.99
    )  # peut être ajouter * 0.999 oui car on utilise bybit pour calculer le montant thorchain
    # logging.info(f'getAmountInMax - maxDexInputAmount {maxDexInputAmount/1e8} for assetIn {firstPairToExecute.assetIn.symbol} to assetOut {firstPairToExecute.assetOut.symbol}')
    # logging.info(f'getAmountInMax - amountInMax {amountInMax} for assetIn {firstPairToExecute.assetIn.symbol} to assetOut {firstPairToExecute.assetOut.symbol}')
    # # logging.info(f'assetOutMaxBalance {assetOutMaxBalance/1e8}')
    # logging.info(f'assetOutCurrentBalance {assetOutCurrentBalance/1e8}')
    # logging.info(f'remainingOutBalance {remainingOutBalance/1e8}')

    return amountInMax


def getAmountInMaxSynthOnBlock(assetPair, balances: Balances):
    if isinstance(assetPair.assetIn, AssetThorchain):
        dexWalletValue = getThorchainWalletValue(balances.balancesThorchain)

    walletValueInAsset = getValueOfDollarsInAssetThorchain(
        dexWalletValue, assetPair.assetOut, balances.balancesThorchain
    )

    assetOutMaxBalance = walletValueInAsset * assetPair.assetOut.maxBalancePercentage
    assetOutCurrentBalance = assetPair.assetOut.balance
    remainingOutBalance = assetOutMaxBalance - assetOutCurrentBalance

    maxInputAmount = (
        remainingOutBalance / (10**assetPair.assetIn.decimals)
        if remainingOutBalance > 0
        else 0
    )

    # logging.info(f'getAmountInMaxSynthOnBlock - maxInputAmount {maxInputAmount} for assetIn {assetPair.assetIn.symbol} to assetOut {assetPair.assetOut.symbol}')
    # logging.info(f'getAmountInMaxSynthOnBlock - walletValueInAsset {walletValueInAsset/(10**assetPair.assetIn.decimals)} for assetIn {assetPair.assetIn.symbol} to assetOut {assetPair.assetOut.symbol}')

    return min(
        maxInputAmount, assetPair.assetIn.balance / 10**assetPair.assetIn.decimals
    )


def getGain1000CexDex(opportunityCexDex: OpportunityCexDex):
    gainEstimated = opportunityCexDex.gainTotalEstimated
    amountInDollarsValue = getAmountInValue(opportunityCexDex)
    if amountInDollarsValue < 3:
        gainEstimated1000 = 0
    else:
        gainEstimated1000 = (gainEstimated / amountInDollarsValue) * 1000
    return gainEstimated1000


def getGain1000DexDex(opportunityDexDex: OpportunityDexDex):
    gainEstimated = opportunityDexDex.gainTotalEstimated
    amountInDollarsValue = opportunityDexDex.opportunityMaya.amountInInDollars
    if amountInDollarsValue < 15:
        gainEstimated1000 = 0
    else:
        gainEstimated1000 = (gainEstimated / amountInDollarsValue) * 1000
    return gainEstimated1000


def getGain1000OnBlock(opportunityThorchain):
    gainEstimated = opportunityThorchain.gainNetInDollars
    amountInDollarsValue = opportunityThorchain.amountInInDollars
    if amountInDollarsValue < 3:
        gainEstimated1000 = 0
    else:
        gainEstimated1000 = (gainEstimated / amountInDollarsValue) * 1000
    return gainEstimated1000


def getAmountInValue(opportunityCexDex: OpportunityCexDex):
    assetPrice = opportunityCexDex.opportunityBybit.bybitAssetPrice
    if opportunityCexDex.opportunityThorchain.pairAsset.assetIn.assetType == "STABLE":
        amountInDollarsValue = (
            opportunityCexDex.opportunityThorchain.amountIn
            / 10**opportunityCexDex.opportunityThorchain.pairAsset.assetIn.decimals
        )
    else:
        amountInDollarsValue = (
            opportunityCexDex.opportunityThorchain.amountIn
            * assetPrice
            / 10**opportunityCexDex.opportunityThorchain.pairAsset.assetIn.decimals
        )
    return amountInDollarsValue


def getOrderedOpportunities(opportunites):
    def get_slip_fee(opp):
        if isinstance(opp, OpportunityThorchain):
            # logging.info(f'getOrderedOpportunities OpportunityThorchain - opp.slipFees {opp.slipFees}')
            return opp.slipFees
        if isinstance(opp, OpportunityMaya):
            # logging.info(f'getOrderedOpportunities OpportunityThorchain - opp.slipFees {opp.slipFees}')
            return opp.slipFees
        elif isinstance(opp, OpportunityCexDex):
            # logging.info(f'getOrderedOpportunities OpportunityCexDex - opp.opportunityThorchain.slipFees {opp.opportunityThorchain.slipFees}')
            return opp.opportunityThorchain.slipFees
        elif isinstance(opp, OpportunityDexDex):
            return opp.opportunityMaya.slipFees
        else:
            return 0  # Retourner 0 ou une valeur appropriée pour les types non reconnus

    # Trier les opportunités directement par slip fees en ordre décroissant
    opportunites.sort(key=get_slip_fee, reverse=True)

    return opportunites


def getFilteredOpportunities(opportunites):
    assets_utilises = set()
    opportunites_filtrées = []

    for opp in opportunites:
        oppAssets = set()  # Initialisation en tant qu'ensemble vide

        if isinstance(opp, OpportunityCexDex):
            oppAssets = {
                opp.opportunityThorchain.pairAsset.assetIn,
                opp.opportunityThorchain.pairAsset.assetOut,
            }
            # logging.info(f'getFilteredOpportunities OpportunityCexDex - oppAssets {oppAssets}')

        if isinstance(opp, OpportunityThorchain):
            oppAssets = {opp.pairAsset.assetIn, opp.pairAsset.assetOut}
            # logging.info(f'getFilteredOpportunities OpportunityThorchain - oppAssets {oppAssets}')

        if isinstance(opp, OpportunityMaya):
            oppAssets = {opp.pairAsset.assetIn, opp.pairAsset.assetOut}
            # logging.info(f'getFilteredOpportunities OpportunityThorchain - oppAssets {oppAssets}')

        # Vérifier si les assets de l'opportunité actuelle ont déjà été utilisés
        if not oppAssets.intersection(assets_utilises):
            opportunites_filtrées.append(opp)
            assets_utilises.update(oppAssets)  # Mettre à jour les assets utilisés

    return opportunites_filtrées


def getFilteredOpportunitiesPerAsset(opportunites):
    assets_utilises = set()
    opportunites_filtrées = []

    for opp in opportunites:
        if isinstance(opp, OpportunityCexDex):
            assetIn_symbol = (
                opp.opportunityThorchain.pairAsset.assetIn.symbol
            )  # Supposons que .id est l'identifiant unique
            assetOut_symbol = opp.opportunityThorchain.pairAsset.assetOut.symbol

        elif isinstance(opp, OpportunityThorchain):
            assetIn_symbol = opp.pairAsset.assetIn.symbol
            assetOut_symbol = opp.pairAsset.assetOut.symbol

        elif isinstance(opp, OpportunityMaya):
            assetIn_symbol = opp.pairAsset.assetIn.symbol
            assetOut_symbol = opp.pairAsset.assetOut.symbol
        elif isinstance(opp, OpportunityDexDex):
            assetIn_symbol = opp.opportunityMaya.pairAsset.assetIn.symbol
            assetOut_symbol = opp.opportunityMaya.pairAsset.assetOut.symbol   
        # Vérifier si les assets de l'opportunité actuelle ont déjà été utilisés
        if (
            assetIn_symbol not in assets_utilises
            and assetOut_symbol not in assets_utilises
        ):
            opportunites_filtrées.append(opp)
            assets_utilises.add(
                assetIn_symbol
            )  # Ajouter l'ID de assetIn aux assets utilisés
            assets_utilises.add(
                assetOut_symbol
            )  # Ajouter l'ID de assetOut aux assets utilisés

    return opportunites_filtrées


def updatePlatformBalance(platformBalance, balanceDict):
    for asset in platformBalance.listAssets:
        if asset.balanceName in balanceDict:
            asset.balance = float(balanceDict[asset.balanceName])
        else:
            asset.balance = 0


def updateAllBalances(balance: Balances):
    updatePlatformBalance(balance.balancesThorchain, getThorchainBalances())
    updatePlatformBalance(balance.balancesMaya, getMayaBalances())
    updatePlatformBalance(balance.balancesBybit, getBybitBalances())


def updateBalancesAssetsWithBalanceDict(listAssets, balanceDict):
    for asset in listAssets:
        balanceName = asset.balanceName
        currentBalance = float(asset.balance)
        if balanceName in balanceDict:
            newBalance = float(balanceDict[balanceName])
            if newBalance > 0 and newBalance != currentBalance:
                asset.balance = newBalance
                # logging.info(f"updateBalancesAssetsWithBalanceDict - Updated balance for {asset.symbol} : currentBalance {currentBalance}, new balance : {newBalance}")
    return listAssets


def updateBalancesObjectWithBalanceDict(balances:Balances,balanceDict):
    balances.balancesThorchain.listAssets = updateBalancesAssetsWithBalanceDict(listAssets=balances.balancesThorchain.listAssets, balanceDict=balanceDict['THORCHAIN'])
    balances.balancesBybit.listAssets = updateBalancesAssetsWithBalanceDict(listAssets=balances.balancesBybit.listAssets, balanceDict=balanceDict['Bybit'])
    balances.balancesMaya.listAssets = updateBalancesAssetsWithBalanceDict(listAssets=balances.balancesMaya.listAssets, balanceDict=balanceDict['MAYA'])
    


def updateAssetPoolData(balances, poolData, type):
    if type == "MAYA":
        for assetMaya in balances.balancesMaya.listAssets:
            for poolAsset, values in poolData['MAYA'].items():
                if assetMaya.poolName == poolAsset:

                    newPool = PoolMaya(
                        balanceAssetInPool=int(values.get("balanceAssetInPool")),
                        balanceCacaoInPoolAsset=int(values.get("balanceCacaoInPool")),
                        synthSupplyRemaining=int(values.get("synthSupplyRemaining")),
                        status=values.get("status"),
                        block=values.get("block")
                    )

                    assetMaya.pool = newPool
    
    if type == "THORCHAIN":
        for assetThorchain in balances.balancesThorchain.listAssets:
            for poolAsset, values in poolData['THORCHAIN'].items():
                if assetThorchain.poolName == poolAsset:

                    newPool = Pool(
                        balanceAssetInPool=int(values.get("balanceAssetInPool")),
                        balanceRuneInPoolAsset=int(values.get("balanceRuneInPool")),
                        synthSupplyRemaining=int(values.get("synthSupplyRemaining")),
                        status=values.get("status"),
                        block=values.get("block")
                    )

                    assetThorchain.pool = newPool


def update_pool_data(pool_data, pool_type, pool_asset, updates):
    
    if pool_type not in pool_data:
        pool_data[pool_type] = {}

    if pool_asset not in pool_data[pool_type]:
        pool_data[pool_type][pool_asset] = {}

    pool_data[pool_type][pool_asset].update(updates)



def fetchPoolData(poolDataShared, block, pool, listAssets):
    
    poolData = {}

    for singlePool in pool:
        for asset in listAssets:
            if singlePool['asset'] == asset.poolName: 
                updates = {
                    'balanceAssetInPool': singlePool['balance_asset'],
                    'status': singlePool['status'],
                    'block': block 
                }
                
                if isinstance(asset,AssetThorchain):
                    updates['balanceRuneInPool'] = singlePool['balance_rune']
                    updates['synthSupplyRemaining'] = singlePool['synth_supply_remaining']
                    updates['synthMintPaused'] = singlePool['synth_mint_paused']
                    poolType = 'THORCHAIN'
                if isinstance(asset,AssetMaya):
                    updates['balanceCacaoInPool'] = singlePool['balance_cacao']
                    synthSupplyRemaining = int((MAX_SYNTH_PER_POOL_DEPTH_MAYA * (int(singlePool.get("balance_asset")) * 2) ) - int(singlePool.get("synth_supply")))
                    updates['synthSupplyRemaining'] = synthSupplyRemaining
                    poolType = 'MAYA'

                update_pool_data(poolData, poolType, asset.poolName, updates)
    
    poolDataShared.update(poolData)


def updateBalanceDictWithOpp(opportunity, balanceDict:Dict, isOppSuccess:bool, isEstimated:bool, lock:Lock):
    
    with lock:
        balanceDictCopy = deepcopy(balanceDict)

        typeOpp = opportunity.typeOpp
        
        assetInBalanceName = opportunity.pairAsset.assetIn.balanceName
        assetOutBalanceName = opportunity.pairAsset.assetOut.balanceName

        if typeOpp == 'Bybit' and isEstimated:
            amountIn = opportunity.amountInEstimated
        elif typeOpp == 'Bybit' and not isEstimated:
            amountIn = opportunity.amountInReal
        else:
            amountIn = opportunity.amountIn
        
        amountOut = opportunity.amountOutEstimated if isEstimated else opportunity.amountOutReal

        if not isEstimated:
            if typeOpp == 'THORCHAIN':
                balanceDictCopy[typeOpp]['rune'] -= NETWORK_FEES_RUNE * 10 ** DECIMALS_RUNE

            elif typeOpp == 'MAYA':
                balanceDictCopy[typeOpp]['cacao'] -= NETWORK_FEES_CACAO * 10 ** DECIMALS_CACAO
            
            amountInEstimated = opportunity.amountInEstimated if typeOpp == "Bybit" else opportunity.amountIn

            update_balance_dict(balanceDictCopy, typeOpp, assetInBalanceName, +amountInEstimated)
            # update_balance_dict(balanceDict, typeOpp, assetOutBalanceName, -opportunity.amountOutEstimated)
            
        
        adjust_amount_in = -amountIn if isOppSuccess else -amountOut
        adjust_amount_out = amountOut if isOppSuccess else 0
        
        if isEstimated:
            adjust_amount_out = 0
        
        if isEstimated == False and isOppSuccess == False and typeOpp == 'Bybit':
            adjust_amount_in = 0

        update_balance_dict(balanceDictCopy, typeOpp, assetInBalanceName, adjust_amount_in)
        update_balance_dict(balanceDictCopy, typeOpp, assetOutBalanceName, adjust_amount_out)
        balanceDict.update(balanceDictCopy)
    

def updateBalanceDictWithDoubleOpp(opportunity1, opportunity2, balanceDict:Dict, isOppSuccess:bool, isEstimated:bool, lock:Lock):
    
    with lock:
        balanceDictCopy = deepcopy(balanceDict)
        
        amountIn1 = opportunity1.amountIn
        amountOut1 = opportunity1.amountOutEstimated if isEstimated else opportunity1.amountOutReal

        if not isEstimated:
            if opportunity1.typeOpp == 'THORCHAIN':
                balanceDictCopy[opportunity1.typeOpp]['rune'] -= NETWORK_FEES_RUNE * 10 ** DECIMALS_RUNE

            elif opportunity1.typeOpp == 'MAYA':
                balanceDictCopy[opportunity1.typeOpp]['cacao'] -= NETWORK_FEES_CACAO * 10 ** DECIMALS_CACAO
            
            amountInEstimated1 = opportunity1.amountIn
            amountInEstimated2 = opportunity2.amountInEstimated if opportunity2.typeOpp == "Bybit" else opportunity2.amountIn

            update_balance_dict(balanceDictCopy, opportunity1.typeOpp, opportunity1.pairAsset.assetIn.balanceName, +amountInEstimated1)
            update_balance_dict(balanceDictCopy, opportunity2.typeOpp, opportunity2.pairAsset.assetIn.balanceName, +amountInEstimated2)
        
            if isOppSuccess == False:
                amountIfRevert = amountIn1 - opportunity1.amountOutReal

        adjust_amount_in1 = -amountIn1 if isOppSuccess else -amountIfRevert
        adjust_amount_out1 = amountOut1 if isOppSuccess else 0

        if isEstimated:
            adjust_amount_out1 = 0

        update_balance_dict(balanceDictCopy, opportunity1.typeOpp, opportunity1.pairAsset.assetIn.balanceName, adjust_amount_in1)
        update_balance_dict(balanceDictCopy, opportunity1.typeOpp, opportunity1.pairAsset.assetOut.balanceName, adjust_amount_out1)
        
        if isOppSuccess == True and isEstimated == False:
            if opportunity2.typeOpp == 'THORCHAIN':
                balanceDictCopy[opportunity2.typeOpp]['rune'] -= NETWORK_FEES_RUNE * 10 ** DECIMALS_RUNE

            elif opportunity2.typeOpp == 'MAYA':
                balanceDictCopy[opportunity2.typeOpp]['cacao'] -= NETWORK_FEES_CACAO * 10 ** DECIMALS_CACAO

            amountIn2 = opportunity2.amountInReal if opportunity2.typeOpp == "Bybit" else opportunity2.amountIn
            amountOut2 = opportunity2.amountOutReal

            adjust_amount_in2 = -amountIn2 
            adjust_amount_out2 = amountOut2 

            update_balance_dict(balanceDictCopy, opportunity2.typeOpp, opportunity2.pairAsset.assetIn.balanceName, adjust_amount_in2)
            update_balance_dict(balanceDictCopy, opportunity2.typeOpp, opportunity2.pairAsset.assetOut.balanceName, adjust_amount_out2)
                    

        elif isOppSuccess == True and isEstimated == True:
            amountIn2 = opportunity2.amountInEstimated if opportunity2.typeOpp == "Bybit" else opportunity2.amountIn
            adjust_amount_in2 = -amountIn2 
            update_balance_dict(balanceDictCopy, opportunity2.typeOpp, opportunity2.pairAsset.assetIn.balanceName, adjust_amount_in2)
        
        balanceDict.update(balanceDictCopy)


def updateBalanceDictWithSingleOpp(opportunity, balanceDict:Dict, isOppSuccess:bool, isEstimated:bool, lock:Lock):
    
    with lock:
        balanceDictCopy = deepcopy(balanceDict)

        typeOpp = opportunity.typeOpp
        
        assetInBalanceName = opportunity.pairAsset.assetIn.balanceName
        assetOutBalanceName = opportunity.pairAsset.assetOut.balanceName

        amountIn = opportunity.amountIn
        
        amountOut = opportunity.amountOutEstimated if isEstimated else opportunity.amountOutReal

        if not isEstimated:
            if typeOpp == 'THORCHAIN':
                balanceDictCopy[typeOpp]['rune'] -= NETWORK_FEES_RUNE * 10 ** DECIMALS_RUNE

            elif typeOpp == 'MAYA':
                balanceDictCopy[typeOpp]['cacao'] -= NETWORK_FEES_CACAO * 10 ** DECIMALS_CACAO
            
            update_balance_dict(balanceDictCopy, typeOpp, assetInBalanceName, amountIn)
            # update_balance_dict(balanceDict, typeOpp, assetOutBalanceName, -opportunity.amountOutEstimated)
        
        if not isOppSuccess:
            amountIfRevert = amountIn - amountOut

        adjust_amount_in = -amountIn if isOppSuccess else -amountIfRevert
        adjust_amount_out = amountOut if isOppSuccess else 0
        
        if isEstimated:
            adjust_amount_out = 0

        update_balance_dict(balanceDictCopy, typeOpp, assetInBalanceName, adjust_amount_in)
        update_balance_dict(balanceDictCopy, typeOpp, assetOutBalanceName, adjust_amount_out)
        balanceDict.update(balanceDictCopy)



def update_balance_dict(balanceDict:Dict, typeOpp:str, assetBalanceName:str, amountChange:float):

    if typeOpp in balanceDict.keys() and assetBalanceName in balanceDict[typeOpp].keys():
        currentBalance = float(balanceDict[typeOpp][assetBalanceName])
        newBalance = currentBalance + amountChange
        balanceDict[typeOpp][assetBalanceName] = newBalance
        # logging.info(f'updateBalanceDictWithOpp - Balance update - {typeOpp} - new balance : {assetBalanceName}: {newBalance} old balance : {currentBalance}')
        
    else:
        logging.warning(f'Invalid balance update attempt for {typeOpp} - {assetBalanceName}')



# def getAmountInMaxDexDex(firstPairToExecute, secondPairToExecute):

    
#     # print(f'getAmountInMax - priceAsset {priceAsset} balanceSecondPairAssetInConvertedToFirstPairAssetIn {balanceSecondPairAssetInConvertedToFirstPairAssetIn}')
#     amountInMax = (
#         min(
#             balanceSecondPairAssetInConvertedToFirstPairAssetIn,
#             (
#                 firstPairToExecute.assetIn.balance
#                 / 10**firstPairToExecute.assetIn.decimals
#             ),
#         )
#         * 0.99
#     )  # peut être ajouter * 0.999 oui car on utilise bybit pour calculer le montant thorchain
#     # print(f'getAmountInMax - amountInMax {amountInMax}')

#     return amountInMax



def get_balance_value(balancesDict:Dict, platform:str, balance_name:str):
    try:
        return float(balancesDict[platform][balance_name])
    except KeyError:
        print(f"balanceName '{balance_name}' not found in platform '{platform}'")
        return 0
    

