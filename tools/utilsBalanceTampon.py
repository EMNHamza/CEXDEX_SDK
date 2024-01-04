from classes.Balances import Balances, BalancesBybit
from classes.Opportunity import OpportunityBybit,OpportunityMaya,OpportunityCexDex,OpportunityThorchain, OpportunityDexDex
import logging
from copy import deepcopy
# def resetBalanceTampon(balanceTampon: Balances):
#     for platformBalance in balanceTampon:
#         for asset in platformBalance:
#             asset.balance = 0


# def updateBalanceTampon(listOpportunities, balanceTampon : Balances, isLock:bool):
#     # updatedBalanceTampon = resetBalanceTampon(balanceTampon)
#     balancesBufferThorchain = balanceTampon.balancesThorchain
#     balancesBufferBybit = balanceTampon.balancesBybit
#     balancesBufferMaya = balanceTampon.balancesMaya

#     for opportunity in listOpportunities:
#         if isinstance(opportunity, OpportunityCexDex):
#             if opportunity.opportunityThorchain.typeOpp == 'CEXDEX':
#                 updateBalanceTamponDex(opportunity.opportunityThorchain,balancesBufferThorchain, isLock)
#             elif opportunity.opportunityThorchain.typeOpp == 'CEXDEXMAYA':
#                 updateBalanceTamponDex(opportunity.opportunityThorchain,balancesBufferMaya, isLock)
#             updateBalanceTamponCex(opportunity.opportunityBybit,balancesBufferBybit, isLock)
        
#         if isinstance(opportunity, OpportunityThorchain):
#             updateBalanceTamponDex(opportunity,balancesBufferThorchain, isLock)

#         if isinstance(opportunity, OpportunityMaya):
#             updateBalanceTamponDex(opportunity,balancesBufferMaya, isLock)
    
#     newBalancesBuffer = Balances(balancesThorchain=balancesBufferThorchain,balancesBybit=balancesBufferBybit,balancesMaya=balancesBufferMaya)
#     return newBalancesBuffer
#     # balanceTampon.balancesThorchain.listAssets = balancesBufferThorchain.listAssets
#     # balanceTampon.balancesBybit.listAssets = balancesBufferBybit.listAssets
#     # balanceTampon.balancesMaya.listAssets = balancesBufferMaya.listAssets


# def updateBalanceTamponDex(opportunity, balanceTamponDex, isLock:bool):
#     typeOpp = opportunity.typeOpp
#     amountInDex = opportunity.amountIn
#     assetIn = opportunity.pairAsset.assetIn
#     assetInBalanceName = assetIn.balanceName

#     try:
#         # Recherche de l'index de l'actif dans balanceTampon
#         index = next(i for i, asset in enumerate(balanceTamponDex.listAssets) if asset.balanceName == assetInBalanceName)
#         # Mise à jour de la balance si l'actif est trouvé
#         if isLock:
#             balanceTamponDex.listAssets[index].balance += amountInDex
#             logging.info(f'updateBalanceTamponDex - {typeOpp} LOCK {amountInDex} {balanceTamponDex.listAssets[index].symbol} - total lock for {balanceTamponDex.listAssets[index].symbol} : {balanceTamponDex.listAssets[index].balance}')
#         else:
#             balanceTamponDex.listAssets[index].balance -= amountInDex
#             logging.info(f'updateBalanceTamponDex - {typeOpp} UNLOCK {amountInDex} {balanceTamponDex.listAssets[index].symbol} - total lock for {balanceTamponDex.listAssets[index].symbol} : {balanceTamponDex.listAssets[index].balance}')

#     except StopIteration:
#         print(f"Erreur : L'actif {assetInBalanceName} n'a pas été trouvé dans balanceTamponDex.")


# def updateBalanceTamponCex(opportunity: OpportunityBybit, balanceTamponCex: BalancesBybit, isLock:bool):
#     typeOpp = opportunity.typeOpp
#     amountInDex = opportunity.amountInEstimated
#     assetIn = opportunity.pairAsset.assetIn
#     assetInBalanceName = assetIn.balanceName

#     try:
#         # Recherche de l'index de l'actif dans balanceTampon
#         index = next(i for i, asset in enumerate(balanceTamponCex.listAssets) if asset.balanceName == assetInBalanceName)
#         # Mise à jour de la balance si l'actif est trouvé
        
#         if isLock:
#             balanceTamponCex.listAssets[index].balance += amountInDex
#             logging.info(f'updateBalanceTamponCex - {typeOpp} BYBIT LOCK {amountInDex} {balanceTamponCex.listAssets[index].symbol} - total lock for {balanceTamponCex.listAssets[index].symbol} : {balanceTamponCex.listAssets[index].balance}')
#         else:
#             balanceTamponCex.listAssets[index].balance -= amountInDex
#             logging.info(f'updateBalanceTamponCex - {typeOpp} BYBIT UNLOCK {amountInDex} {balanceTamponCex.listAssets[index].symbol} - total lock for {balanceTamponCex.listAssets[index].symbol} : {balanceTamponCex.listAssets[index].balance}')

#     except StopIteration:
#         print(f"Erreur : L'actif {assetInBalanceName} n'a pas été trouvé dans balanceTamponCex.")


# # def updateBalancesObject(balances: Balances, balanceTampon: Balances) -> Balances:
# #     updatedThorchain = updateBalancesAssets(existing_assets=balances.balancesThorchain.listAssets, tampon_assets=balanceTampon.balancesThorchain.listAssets)
# #     updatedBybit = updateBalancesAssets(existing_assets=balances.balancesBybit.listAssets, tampon_assets=balanceTampon.balancesBybit.listAssets)
# #     updatedMaya = updateBalancesAssets(existing_assets=balances.balancesMaya.listAssets, tampon_assets=balanceTampon.balancesMaya.listAssets)

# #     return Balances(updatedThorchain, updatedBybit, updatedMaya)


# def updateBalancesAssets(existing_assets, tampon_assets):
#     updated_assets = existing_assets.copy()  # Copy the existing assets

#     for tampon_asset in tampon_assets:
#         for idx, asset in enumerate(existing_assets):
#             if tampon_asset.balanceName == asset.balanceName and tampon_asset.balance > 0:
#                 logging.info(f'updateBalancesAssets - asset to change : {asset.symbol}')
#                 updated_balance = asset.balance - tampon_asset.balance
#                 updated_assets[idx] = type(asset)(tampon_asset.balanceName, updated_balance)
#                 logging.info(f'updateBalancesAssets - old balance : {asset.balance} {asset.symbol} new balance : {updated_balance} {tampon_asset.symbol}')
#                 break  # Once the asset has been found and updated, move to the next tampon_asset

#     return updated_assets


# def updateBalancesObject(balances:Balances,balancesBuffer:Balances):
#     balances.balancesThorchain.listAssets = updateBalancesAssets(existing_assets=balances.balancesThorchain.listAssets, tampon_assets=balancesBuffer.balancesThorchain.listAssets)
#     balances.balancesBybit.listAssets = updateBalancesAssets(existing_assets=balances.balancesBybit.listAssets, tampon_assets=balancesBuffer.balancesBybit.listAssets)
#     balances.balancesMaya.listAssets = updateBalancesAssets(existing_assets=balances.balancesMaya.listAssets, tampon_assets=balancesBuffer.balancesMaya.listAssets)
    


# -----
    
def updateBalanceTampon(listOpportunities, balanceBuffer, isLock:bool):
    
    balanceBufferCopy = deepcopy(balanceBuffer)
    for opportunity in listOpportunities:
        if isinstance(opportunity, OpportunityCexDex):
            if opportunity.opportunityThorchain.typeOpp == 'CEXDEX':
                updateBalanceTamponDex(opportunity.opportunityThorchain, balanceBufferCopy, isLock)
            elif opportunity.opportunityThorchain.typeOpp == 'CEXDEXMAYA':
                updateBalanceTamponDex(opportunity.opportunityThorchain, balanceBufferCopy, isLock)
            updateBalanceTamponCex(opportunity.opportunityBybit, balanceBufferCopy, isLock)
        
        if isinstance(opportunity, OpportunityThorchain):
            updateBalanceTamponDex(opportunity,balanceBufferCopy, isLock)

        if isinstance(opportunity, OpportunityMaya):
            updateBalanceTamponDex(opportunity,balanceBufferCopy, isLock)

        if isinstance(opportunity, OpportunityDexDex):
            updateBalanceTamponDex(opportunity.opportunityMaya,balanceBufferCopy, isLock)
            updateBalanceTamponDex(opportunity.opportunityThorchain,balanceBufferCopy, isLock)

    # balanceBuffer.update(balanceBufferCopy)

    return balanceBufferCopy

def newUpdateBalanceTampon(opportunity, balanceBuffer, isLock:bool):
    
    if isinstance(opportunity, OpportunityCexDex):
        updateBalanceTamponDex(opportunity.opportunityThorchain, balanceBuffer, isLock)
        updateBalanceTamponCex(opportunity.opportunityBybit, balanceBuffer, isLock)
    
    if isinstance(opportunity, OpportunityThorchain):
        updateBalanceTamponDex(opportunity,balanceBuffer, isLock)

    if isinstance(opportunity, OpportunityMaya):
        updateBalanceTamponDex(opportunity,balanceBuffer, isLock)

    if isinstance(opportunity, OpportunityDexDex):
        updateBalanceTamponDex(opportunity.opportunityMaya,balanceBuffer, isLock)
        updateBalanceTamponDex(opportunity.opportunityThorchain,balanceBuffer, isLock)

    # balanceBuffer.update(balanceBufferCopy)

    return balanceBuffer


def updateBalanceTamponDex(opportunity, balanceTamponDex, isLock:bool):
    typeOpp = opportunity.typeOpp
    if opportunity.typeOpp == 'CEXDEX' or opportunity.typeOpp == 'THORMAYA':
        typeOpp = 'THORCHAIN'
    elif opportunity.typeOpp == 'CEXDEXMAYA' or opportunity.typeOpp == 'MAYATHOR':
        typeOpp = 'MAYA'

    amountInDex = opportunity.amountIn
    assetIn = opportunity.pairAsset.assetIn
    assetInBalanceName = assetIn.balanceName
    
    if typeOpp in balanceTamponDex and assetIn.balanceName in balanceTamponDex[typeOpp]:
        
        currentBalance = float(balanceTamponDex[typeOpp][assetInBalanceName])

        if isLock:
            newBalance = currentBalance + amountInDex
            
            logging.info(f'updateBalanceTamponDex - {typeOpp} LOCK {amountInDex} {assetIn.symbol} - total lock for {assetIn.symbol} : {round(newBalance,6)}')
            balanceTamponDex[typeOpp][assetInBalanceName] = round(newBalance,6)
        else:
            newBalance = currentBalance - amountInDex
            logging.info(f'updateBalanceTamponDex - {typeOpp} UNLOCK {amountInDex} {assetIn.symbol} - total lock for {assetIn.symbol} : {round(newBalance,6)}')
            balanceTamponDex[typeOpp][assetInBalanceName] = round(newBalance,6)
  

def updateBalanceTamponCex(opportunity, balanceTamponCex, isLock:bool):
    typeOpp = opportunity.typeOpp
    amountInDex = opportunity.amountInEstimated
    assetIn = opportunity.pairAsset.assetIn
    assetInBalanceName = assetIn.balanceName

    if opportunity.typeOpp in balanceTamponCex and assetIn.balanceName in balanceTamponCex[opportunity.typeOpp]:
        
        currentBalance = float(balanceTamponCex[opportunity.typeOpp][assetInBalanceName])

        if isLock:
            newBalance = currentBalance + amountInDex
            logging.info(f'updateBalanceTamponCex - {typeOpp} LOCK {amountInDex} {assetIn.symbol} - total lock for {assetIn.symbol} : {round(newBalance,6)}')
            balanceTamponCex[opportunity.typeOpp][assetInBalanceName] = round(newBalance,6)
        else:
            newBalance = currentBalance - amountInDex
            logging.info(f'updateBalanceTamponCex - {typeOpp} UNLOCK {amountInDex} {assetIn.symbol} - total lock for {assetIn.symbol} : {round(newBalance,6)}')
            balanceTamponCex[opportunity.typeOpp][assetInBalanceName] = round(newBalance,6)
  

def updateBalancesAssets(listAssets, balanceBuffer):
    for asset in listAssets:
        balanceName = asset.balanceName
        currentBalance = asset.balance
        if balanceName in balanceBuffer:
            newBalance = float(balanceBuffer[balanceName])
            if newBalance > 0:
                asset.balance = currentBalance - newBalance
                logging.info(f"Updated balance for {asset.symbol} : remove {newBalance}, new balance : {asset.balance}")
    return listAssets


def updateBalancesObject(balances:Balances,balanceBuffer):
    balances.balancesThorchain.listAssets = updateBalancesAssets(listAssets=balances.balancesThorchain.listAssets, balanceBuffer=balanceBuffer['THORCHAIN'])
    balances.balancesBybit.listAssets = updateBalancesAssets(listAssets=balances.balancesBybit.listAssets, balanceBuffer=balanceBuffer['Bybit'])
    balances.balancesMaya.listAssets = updateBalancesAssets(listAssets=balances.balancesMaya.listAssets, balanceBuffer=balanceBuffer['MAYA'])
    


def isOppPossible(balanceDict, opportunity):
    
    if isinstance(opportunity, OpportunityCexDex):
        isOppPossible = isAmountInBalance(balanceDict, opportunity.opportunityThorchain.typeOpp, opportunity.opportunityThorchain.pairAsset.assetIn.balanceName, opportunity.opportunityThorchain.amountIn)
        if isOppPossible:
            isOppPossible = isAmountInBalance(balanceDict, opportunity.opportunityBybit.typeOpp, opportunity.opportunityBybit.pairAsset.assetIn.balanceName, opportunity.opportunityBybit.amountInEstimated)
        
    elif isinstance(opportunity,OpportunityDexDex):
        isOppPossible = isAmountInBalance(balanceDict, opportunity.opportunityMaya.typeOpp, opportunity.opportunityMaya.pairAsset.assetIn.balanceName, opportunity.opportunityMaya.amountIn)
        if isOppPossible:
            isOppPossible = isAmountInBalance(balanceDict, opportunity.opportunityThorchain.typeOpp, opportunity.opportunityThorchain.pairAsset.assetIn.balanceName, opportunity.opportunityThorchain.amountIn)

    else:
        isOppPossible = isAmountInBalance(balanceDict, opportunity.typeOpp , opportunity.pairAsset.assetIn.balanceName, opportunity.amountIn)

    return isOppPossible

def isAmountInBalance(balanceDict, typeOpp, assetBalanceName, amount):

    if typeOpp in balanceDict.keys() and assetBalanceName in balanceDict[typeOpp].keys():
        currentBalance = float(balanceDict[typeOpp][assetBalanceName])
        
        if amount < currentBalance:
            logging.info(f'isAmountInBalance - True - {typeOpp} {assetBalanceName} {amount} < {currentBalance}')
            return True
        else:
            logging.warning(f'isAmountInBalance - False - {typeOpp} {assetBalanceName} {amount} > {currentBalance}')
            return False
    

    
def adjustBalanceWithBuffer(balanceDict, balanceBuffer):

    for exchange, assets in balanceBuffer.items():
        if exchange in balanceDict:
            for asset, bufferValue in assets.items():
                if asset in balanceDict[exchange]:
                    bufferValue = float(bufferValue)
                    if bufferValue > 0:
                        # Convert values to float for subtraction
                        currentValue = float(balanceDict[exchange][asset])
                        # Subtract buffer value from current value
                        newBalance = currentValue - bufferValue

                        # Log the adjustment
                        logging.info(f"adjustBalanceWithBuffer - Adjusting {exchange} balance for {asset}: {currentValue} - {bufferValue} = {newBalance}")

                        # Update the current balance dictionary
                        balanceDict[exchange][asset] = max(newBalance, 0)  # Using max to avoid negative values
                else:
                    logging.warning(f"adjustBalanceWithBuffer - Asset {asset} not found in current balance for {exchange}")
        else:
            logging.warning(f"adjustBalanceWithBuffer - Exchange {exchange} not found in current balance")


