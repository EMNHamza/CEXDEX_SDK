import math
import logging
import requests
import copy

from classes.Pool import Pool
from classes.Asset import AssetThorchain
from classes.Message import Message
from classes.Opportunity import OpportunityThorchain
from classes.Balances import BalancesThorchain
from classes.Pair import PairDex

from constantes.url import URL_TX_DATA_THOR
from constantes.constantes import DECIMALS_RUNE, OUTBOUND_FEES_RUNE, NETWORK_FEES_RUNE
from typing import Dict, List
from utilsBybit.bybit_price_calculation import orderbook_average_price

 

def formulaSwapInput(
    toRune: bool, pool: Pool, amountOut: float, isSynthSwap: bool, synthMultiplier=1
) -> float:
    try:
        X = pool.balanceAssetInPool if toRune == True else pool.balanceRuneInPoolAsset
        Y = pool.balanceRuneInPoolAsset if toRune == True else pool.balanceAssetInPool
        y = amountOut

        if isSynthSwap == True:
            X = X * synthMultiplier
            Y = Y * synthMultiplier

        part1 = (X * Y) / y - 2 * X
        part2 = 4 * X**2

        amountIn = (part1 - math.sqrt(part1**2 - part2)) / 2

    except Exception:
        # means we exceeds pool balance, then we put infinity input amount
        return float("inf")
    return amountIn


def formulaDoubleSwapInput(
    amountOut: float,
    poolIn: Pool,
    poolOut: Pool,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    synthMultiplier=1,
) -> float:
    r = formulaSwapInput(False, poolOut, amountOut, isSynthSwapIn, synthMultiplier)
    input = formulaSwapInput(True, poolIn, r, isSynthSwapOut, synthMultiplier)
    return input


def formulaSwapOutput(
    toRune: bool, pool: Pool, amountIn: float, isSynthSwap: bool, synthMultiplier=1
) -> float:
    X = pool.balanceAssetInPool if toRune == True else pool.balanceRuneInPoolAsset
    Y = pool.balanceRuneInPoolAsset if toRune == True else pool.balanceAssetInPool
    x = float(amountIn)
    num = x * X * Y
    denum = (x + X) ** 2

    # if isSynthSwap == True:
    #     X = X * synthMultiplier
    #     Y = Y * synthMultiplier
    # logging.info(f" x, X, Y {x,X,Y}")
    amountOut = num / denum

    return amountOut


def formulaGainSwapOutput(
    toRune: bool, pool: Pool, amountIn: float, isSynthSwap: bool, synthMultiplier=1
) -> float:
    X = pool.balanceAssetInPool if toRune == True else pool.balanceRuneInPoolAsset
    Y = pool.balanceRuneInPoolAsset if toRune == True else pool.balanceAssetInPool
    x = float(amountIn)
    num = x * X * Y
    denum = (x + X) ** 2

    # if isSynthSwap == True:
    #     X = X * synthMultiplier
    #     Y = Y * synthMultiplier
    # logging.info(f" x, X, Y {x,X,Y}")
    amountOut = num / denum

    return amountOut - amountIn


def formulaDoubleSwapOutput(
    amountIn: float,
    poolIn: Pool,
    poolOut: Pool,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    synthMultiplier=1,
) -> float:
    
    amountAssetInToRune = formulaSwapOutput(
        True, poolIn, amountIn, isSynthSwapIn, synthMultiplier
    )

    amountOut = formulaSwapOutput(
        False, poolOut, amountAssetInToRune, isSynthSwapOut, synthMultiplier
    )


    return float(amountOut)


def formulaGetSwapFee(
    toRune: bool, pool: Pool, amountIn: float, isSynthSwap: bool, synthMultiplier=1
) -> float:
    X = pool.balanceAssetInPool if toRune == True else pool.balanceRuneInPoolAsset
    Y = pool.balanceRuneInPoolAsset if toRune == True else pool.balanceAssetInPool

    if isSynthSwap == True:
        X = X * synthMultiplier
        Y = Y * synthMultiplier

    x = amountIn

    return (x * x * Y) / (x + X) ** 2


def getValueOfAssetInRune(amount: float, asset: AssetThorchain) -> float:
    R = 0
    A = 1

    pool = asset.pool
    R = float(pool.balanceRuneInPoolAsset)
    A = float(pool.balanceAssetInPool)

    return (float(amount) * R) / A


def getValueOfRuneInAsset(amount: float, asset: AssetThorchain) -> float:
    R = 1
    A = 0

    pool = asset.pool
    R = float(pool.balanceRuneInPoolAsset)
    A = float(pool.balanceAssetInPool)

    return (amount * A) / R


def formulaGetDoubleSwapFee(
    amountIn: float,
    poolIn: Pool,
    poolOut: Pool,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    assetOut:AssetThorchain,
    synthMultiplier=1,
) -> float:
    fee1 = formulaGetSwapFee(True, poolIn, amountIn, isSynthSwapIn, synthMultiplier)
    r = formulaSwapOutput(True, poolIn, amountIn, isSynthSwapIn, synthMultiplier)
    fee2 = formulaGetSwapFee(False, poolOut, r, isSynthSwapOut, synthMultiplier)
    fee1_asset = getValueOfRuneInAsset(fee1,assetOut)
        
    return fee1_asset + fee2


def simulePool(
    responsePool,
    asset: AssetThorchain,
    amountIn: float,
    amountOut: float,
    runeIn: bool,
    synthIn: bool,
    synthOut: bool,
) -> float:
    for pool in responsePool:
        if pool["asset"] == asset:
            if runeIn == True:
                balanceAsset = pool["balance_asset"]
                balanceRune = pool["balance_rune"]
                balanceAsset = float(pool["balance_asset"]) - float(amountOut)
                balanceRune = float(pool["balance_rune"]) + float(amountIn)
                pool["balance_asset"] = balanceAsset
                pool["balance_rune"] = balanceRune

            if runeIn == False:
                balanceAsset = pool["balance_asset"]
                balanceRune = pool["balance_rune"]
                balanceAsset = float(pool["balance_asset"]) + float(amountIn)
                balanceRune = float(pool["balance_rune"]) - float(amountOut)
                pool["balance_asset"] = balanceAsset
                pool["balance_rune"] = balanceRune

    return responsePool


def getThorchainWalletValue(balancesThorchain: BalancesThorchain) -> float:
    totalValue = 0.0

    for asset in balancesThorchain.listAssets:
        try:
            # Ici, nous supposons que chaque 'asset' a des attributs 'amount' et 'asset' appropriés.
            amount = asset.balance  # ou la quantité de l'asset que vous souhaitez convertir
            valueInDollars = getValueInDollarsThorchain(amount, asset, balancesThorchain)
            totalValue += valueInDollars
            # logging.info(f"Asset {asset.symbol}: {amount} -> {valueInDollars} USD")

        except Exception as e:
            logging.error(f"Erreur lors de la conversion de l'asset {asset.symbol}: {e}")
    
    # logging.info(f"Asset total value -> {totalValue} USD")
    return totalValue


def getValueInDollarsThorchain(amount: float, asset: AssetThorchain, balancesThorchain: BalancesThorchain) -> float:
    try:

        if asset.assetType == "RUNE":
            valueInDollars = getValueOfRuneInDollars(amount=amount,balancesThorchain=balancesThorchain)
            return valueInDollars
            
        poolUSDBalanceAsset = None
        poolUSDBalanceRune = None
        
        for asset_ in balancesThorchain.listAssets:
            if asset_.poolName == "ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48" and asset_.pool is not None:
                poolUSDBalanceAsset = asset_.pool.balanceAssetInPool
                poolUSDBalanceRune = asset_.pool.balanceRuneInPoolAsset
                
            if asset_.poolName == asset.poolName:
                newAsset = asset_

        if poolUSDBalanceAsset is None or poolUSDBalanceRune is None:
            raise ValueError("USD Pool values not found")

        if newAsset.pool is None:
            raise ValueError("Asset pool is None")
        
        # logging.info(f'newAsset {newAsset.symbol} newAsset.pool.balanceAssetInPool {newAsset.pool.balanceAssetInPool} newAsset.pool.balanceRuneInPoolAsset {newAsset.pool.balanceRuneInPoolAsset}' )
        poolAssetBalanceAsset = newAsset.pool.balanceAssetInPool
        poolAssetBalanceRune = newAsset.pool.balanceRuneInPoolAsset

        if poolAssetBalanceAsset == 0 or poolUSDBalanceRune == 0:
            raise ZeroDivisionError("Division by zero encountered in pool balances")

        valueInDollars = (
            float(amount)
            * (poolUSDBalanceAsset / poolUSDBalanceRune)
            * (poolAssetBalanceRune / poolAssetBalanceAsset)
        )
        return valueInDollars

    except ZeroDivisionError as zde:
        logging.error(f"Zero division error: {zde}")
        return 0.0
    except ValueError as ve:
        logging.error(f"Value error: {ve}")
        return 0.0
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 0.0


def getValueOfDollarsInAssetThorchain(amount: float, asset: AssetThorchain, balancesThorchain: BalancesThorchain) -> float:
    try:

        if asset.assetType == "RUNE":
            valueInRune = getValueOfDollarsInRune(amount=amount,balancesThorchain=balancesThorchain)
            return valueInRune
            
        poolUSDBalanceAsset = None
        poolUSDBalanceRune = None
        
        for asset_ in balancesThorchain.listAssets:
            if asset_.poolName == "ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48" and asset_.pool is not None:
                poolUSDBalanceAsset = asset_.pool.balanceAssetInPool
                poolUSDBalanceRune = asset_.pool.balanceRuneInPoolAsset
                
            if asset_.poolName == asset.poolName:
                newAsset = asset_

        if poolUSDBalanceAsset is None or poolUSDBalanceRune is None:
            raise ValueError("USD Pool values not found")

        if newAsset.pool is None:
            raise ValueError("Asset pool is None")
        
        # logging.info(f'newAsset {newAsset.symbol} newAsset.pool.balanceAssetInPool {newAsset.pool.balanceAssetInPool} newAsset.pool.balanceRuneInPoolAsset {newAsset.pool.balanceRuneInPoolAsset}' )
        poolAssetBalanceAsset = newAsset.pool.balanceAssetInPool
        poolAssetBalanceRune = newAsset.pool.balanceRuneInPoolAsset

        if poolAssetBalanceAsset == 0 or poolUSDBalanceRune == 0:
            raise ZeroDivisionError("Division by zero encountered in pool balances")

        valueInAsset = (
            float(amount)
            * (poolAssetBalanceAsset/ poolAssetBalanceRune)
            * (poolUSDBalanceRune/poolUSDBalanceAsset)
            
        )
        return valueInAsset

    except ZeroDivisionError as zde:
        logging.error(f"Zero division error: {zde}")
        return 0.0
    except ValueError as ve:
        logging.error(f"Value error: {ve}")
        return 0.0
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 0.0


def formulaGainDoubleSwapOutput(
    amountIn: float,
    poolIn: Pool,
    poolOut: Pool,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    synthMultiplier=1,
) -> float:
    
    amountOut = formulaDoubleSwapOutput(amountIn=amountIn,poolIn=poolIn,poolOut=poolOut,isSynthSwapIn=isSynthSwapIn,isSynthSwapOut=isSynthSwapOut)
    return amountOut - amountIn


def getValueOfRuneInDollars(amount: float, balancesThorchain:BalancesThorchain) -> float:
    R = 1
    A = 0

    for asset in balancesThorchain.listAssets:
        if asset.poolName == "ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48":
            R = float(asset.pool.balanceRuneInPoolAsset)
            A = float(asset.pool.balanceAssetInPool)

    return (amount * A) / R


def getValueOfDollarsInRune(amount: float, balancesThorchain:BalancesThorchain) -> float:
    R = 0
    A = 1

    for asset in balancesThorchain.listAssets:
        if asset.poolName == "ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48":
            R = float(asset.pool.balanceRuneInPoolAsset)
            A = float(asset.pool.balanceAssetInPool)

    return (amount * R) / A


def getValueOfDollarsInAsset(amount: float, asset: AssetThorchain, responsePool) -> float:
    poolAssetBalanceAsset = 1
    poolAssetBalanceRune = 1
    poolUSDBalanceAsset = 1
    poolUSDBalanceRune = 1

    for pool in responsePool:
        if pool["asset"] == asset.poolName:
            poolAssetBalanceAsset = float(pool["balance_asset"])
            poolAssetBalanceRune = float(pool["balance_rune"])
        if pool["asset"] == "ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48":
            poolUSDBalanceAsset = float(pool["balance_asset"])
            poolUSDBalanceRune = float(pool["balance_rune"])
    valueInAsset = (
        float(amount)
        * (poolAssetBalanceAsset / poolAssetBalanceRune)
        * (poolUSDBalanceRune / poolUSDBalanceAsset)
    )
    return valueInAsset


def modifyPoolOpportunity(opportunity: OpportunityThorchain):
    
    if opportunity.pairAsset.assetIn.assetType == "RUNE":

        if opportunity.pairAsset.assetOut.isSynth:
            opportunity.pairAsset.assetOut.pool.balanceRuneInPoolAsset += int(opportunity.amountIn)

        else:
            opportunity.pairAsset.assetOut.pool.balanceAssetInPool -= int(opportunity.amountOutEstimated)
            opportunity.pairAsset.assetOut.pool.balanceRuneInPoolAsset += int(opportunity.amountIn)


    if opportunity.pairAsset.assetOut.assetType == "RUNE":

        if opportunity.pairAsset.assetIn.isSynth:
            opportunity.pairAsset.assetIn.pool.balanceRuneInPoolAsset -= int(opportunity.amountIn)

        else:
            opportunity.pairAsset.assetIn.pool.balanceAssetInPool += int(opportunity.amountIn)
            opportunity.pairAsset.assetIn.pool.balanceRuneInPoolAsset -= int(opportunity.amountOutEstimated)

    return opportunity


def simulePoolAfterOpportunity(opportunity: OpportunityThorchain):
        
    assetRUNE = createAsset(poolName="THOR.RUNE")

    copyOpportunity = copy.deepcopy(opportunity)

    if (
        copyOpportunity.assetIn.assetType == "RUNE"
        or copyOpportunity.assetOut.assetType == "RUNE"
    ):
        copyOpportunity = modifyPoolOpportunity(opportunity=copyOpportunity)
        return copyOpportunity



    copyOpportunity.amountOutEstimated = getValueOfAssetInRune(
        amount=copyOpportunity.amountIn,
        asset=copyOpportunity.assetIn,
    )

    copyOpportunity.assetOut = assetRUNE

    copyOpportunity = modifyPoolOpportunity(opportunity=copyOpportunity)

    copyOpportunity.amountIn = copyOpportunity.amountOutEstimated
    copyOpportunity.assetIn = copyOpportunity.assetOut
    copyOpportunity.amountOutEstimated = opportunity.amountOutEstimated
    copyOpportunity.assetOut = opportunity.assetOut

    copyOpportunity = modifyPoolOpportunity(opportunity=copyOpportunity)
    
    return copyOpportunity


def createAsset(poolName: str) -> AssetThorchain:
    balanceName = poolName.replace(".", "/").lower()
    memoName = balanceName.upper()
    splitPoolName = poolName.split(".")
    chain = splitPoolName[0]
    symbol = splitPoolName[1]
    ticker = splitPoolName[1]
    asset = AssetThorchain(
        chain=chain,
        symbol=symbol,
        ticker=ticker,
        isSynth=True,
        poolName=poolName,
        balanceName=balanceName,
        memoName=memoName,
        assetType='RUNE',
        pool='',
        balance=0,
        )
    
    
    return asset


def dichotomieOnBlockOld(
    f,
    low,
    high,
    e,
    poolIn: Pool,
    poolOut: Pool,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
):
    mid = 0
    while high - low > e:
        mid = float((high + low) / 2)
        p1 = float(low + (high - low) / 4)
        p2 = float(low + 3 * (high - low) / 4)
        if f(p1, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut) > f(
            mid, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut
        ):
            high = mid
        elif f(mid, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut) < f(
            p2, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut
        ):
            low = mid
        else:
            low = p1
            high = p2

    return (mid, f(mid, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut))


def dichotomieOnBlock(
    f,
    low,
    high,
    e,
    assetIn,
    assetOut,
    isSynthSwapIn,
    isSynthSwapOut,
):
    while high - low > e:
        mid = low + (high - low)/2
        
        f_mid = f(mid, assetIn.pool, assetOut.pool, isSynthSwapIn, isSynthSwapOut)
        f_high = f(high, assetIn.pool, assetOut.pool, isSynthSwapIn, isSynthSwapOut)

        if f_mid < f_high:
            low = mid
        else:
            high = mid

    mid = (low + high) / 2
    final_value = f(mid, assetIn.pool, assetOut.pool, isSynthSwapIn, isSynthSwapOut)
    return mid, final_value


def dichotomieCexDexOld(
    f,
    low,
    high,
    e,
    assetIn:AssetThorchain,
    assetOut:AssetThorchain,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    orderbookData: Dict,
    balancesThorchain:BalancesThorchain
):
    mid = 0
    while high - low > e:
        mid = float((high + low) / 2)
        p1 = float(low + (high - low) / 4)
        p2 = float(low + 3 * (high - low) / 4)
        if f(p1, assetIn,assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain) > f(
            mid, assetIn,assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain
        ):
            high = mid
        elif f(mid, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain) < f(
            p2, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain
        ):
            low = mid
        else:
            low = p1
            high = p2

    return (mid, f(mid, assetIn,assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain))


def dichotomieCexDex(
    f,
    low,
    high,
    e,
    assetIn,
    assetOut,
    isSynthSwapIn,
    isSynthSwapOut,
    orderbookData,
    balancesThorchain
):
    while high - low > e:
        mid = low + (high - low)/2
        
        f_mid = f(mid, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain)
        f_high = f(high, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain)
        f_low = f(low, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain)
        
        # logging.info(f' DICHOTOMIE - assetIn {assetIn.symbol} assetOut {assetOut.symbol} low {low/1e8} f_low {f_low/1e8} mid {mid/1e8} f_mid {f_mid/1e8} high {high/1e8} f_high {f_high/1e8}')

        if f_mid < f_high:
            low = mid
        else:
            high = mid

    mid = (low + high) / 2
    final_value = f(mid, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain)
    # logging.info(f'Dichotomie : gain =  {final_value / 1e8} $ amountInOpti = {mid/1e8} {assetIn.symbol} vers {assetOut.symbol}')

    return mid, final_value


def dichotomieCexDexLog(
    f,
    low,
    high,
    e,
    assetIn,
    assetOut,
    isSynthSwapIn,
    isSynthSwapOut,
    orderbookData,
    balancesThorchain
):
    while high - low > e:

        mid = low + (high - low)/2
        
        f_mid = f(mid, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain)
        f_high = f(high, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain)
        f_low = f(low, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain)
        
        logging.info(f' DICHOTOMIE - low {low/1e8} f_low {f_low/1e8} mid {mid/1e8} f_mid {f_mid/1e8} high {high/1e8} f_high {f_high/1e8}')
        
        if f_mid < f_high:
            low = mid
        else:
            high = mid

    mid = (low + high) / 2
    final_value = f(mid, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData, balancesThorchain)
    logging.info(f'final_value : {final_value}')
    return mid, final_value


def getThorchainSwapOutput(amountIn, assetIn, assetOut):
    if assetIn.assetType == 'RUNE':
        amountOut = formulaSwapOutput(toRune=False,pool=assetOut.pool,amountIn=amountIn,isSynthSwap=True)
    elif assetOut.assetType == 'RUNE':
        amountOut = formulaSwapOutput(toRune=True,pool=assetIn.pool,amountIn=amountIn,isSynthSwap=True)
    else:
        amountOut = formulaDoubleSwapOutput(amountIn=amountIn, poolIn=assetIn.pool, poolOut=assetOut.pool, isSynthSwapIn=True, isSynthSwapOut=True)
    
    return amountOut


def formulaGainInStable(amountIn: int, assetIn:AssetThorchain, assetOut:AssetThorchain, isSynthSwapIn: bool, isSynthSwapOut: bool, orderbookData: Dict, balancesThorchain:BalancesThorchain, synthMultiplier=1):


    amountOutNet = formulaDoubleSwapOutput(amountIn=amountIn, poolIn=assetIn.pool, poolOut=assetOut.pool, isSynthSwapIn=isSynthSwapIn, isSynthSwapOut=isSynthSwapOut)
    
    if assetIn.assetType == 'STABLE':
        # priceAssetInInDollars = 1
        # priceAssetOutInDollars = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutNet, isSell=False) #False avant 30/11
        amountInInStable = amountIn
        amountOutInStable = getValueInDollarsThorchain(amount=amountOutNet,asset=assetOut,balancesThorchain=balancesThorchain)
    else:
        amountInInStable = getValueInDollarsThorchain(amount=amountIn,asset=assetIn,balancesThorchain=balancesThorchain)
        amountOutInStable = amountOutNet
        # priceAssetInInDollars = orderbook_average_price(orderbook_data=orderbookData, amount=amountIn,  isSell=True)
        # priceAssetOutInDollars = 1


    # amountInInStable = amountIn * priceAssetInInDollars
    # amountOutInStable = amountOutNet * priceAssetOutInDollars

    gainInStable = amountOutInStable - amountInInStable
    
    # logging.info(f'formulaGainInStable - assetIn {assetIn.symbol} gainInStable {gainInStable} amountInInStable {amountInInStable} amountOutInStable {amountOutInStable} amountIn {amountIn} amountOutNet {amountOutNet}')
    return gainInStable


def formulaGainStableCexDex(amountIn:int, assetIn:AssetThorchain, assetOut:AssetThorchain, isSynthSwapIn: bool, isSynthSwapOut: bool, orderbookData: Dict, balancesThorchain:BalancesThorchain, synthMultiplier=1):
    
    amountOutThorchain = formulaDoubleSwapOutput(amountIn=amountIn, poolIn=assetIn.pool, poolOut=assetOut.pool, isSynthSwapIn=isSynthSwapIn, isSynthSwapOut=isSynthSwapOut)
    
    if assetIn.assetType == 'STABLE':
        priceAssetInInDollars = 1
        bybitAssetPrice = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutThorchain/ 10**assetOut.decimals,  isSell=True)
        amountOutBybit = amountOutThorchain*bybitAssetPrice

    else:
        priceAssetInInDollars = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutThorchain/ 10**assetOut.decimals,  isSell=False)
        bybitAssetPrice = priceAssetInInDollars
        amountOutBybit = amountOutThorchain/bybitAssetPrice

    # amountOutBybit = amountOutThorchain*bybitAssetPrice
    amountInThorchainInStable = amountIn * priceAssetInInDollars
    amountOutBybitInStable = amountOutBybit * priceAssetInInDollars

    gainInStable = amountOutBybitInStable - amountInThorchainInStable
    
    # logging.info(f'formulaGainInStable - gainInStable {gainInStable/1e8} amountInThorchain {amountIn/1e8} amountInThorchainInStable {amountInThorchainInStable/1e8} amountOutBybit {amountOutBybit/1e8} amountOutBybitInStable {amountOutBybitInStable/1e8}')
    return gainInStable


def formulaGainMayaThor(amountIn: int, assetIn:AssetThorchain, assetOut:AssetThorchain, poolIn: Pool, poolOut: Pool, isSynthSwapIn: bool, isSynthSwapOut: bool, balancesThorchain:BalancesThorchain, synthMultiplier=1):
    
    if assetIn.assetType == 'RUNE':
        amountOut = formulaSwapOutput(toRune=False,pool=poolIn,amountIn=amountIn,isSynthSwap=True)
    elif assetOut.assetType == 'RUNE':
        amountOut = formulaSwapOutput(toRune=True,pool=poolIn,amountIn=amountIn,isSynthSwap=True)
    else:
        amountOut = formulaDoubleSwapOutput(amountIn=amountIn, poolIn=poolIn, poolOut=poolOut, isSynthSwapIn=isSynthSwapIn, isSynthSwapOut=isSynthSwapOut)

    amountInInDollars = getValueInDollarsThorchain(amount=amountIn,asset=assetIn,balancesThorchain=balancesThorchain)
    amountOutInDollars = getValueInDollarsThorchain(amount=amountOut,asset=assetOut,balancesThorchain=balancesThorchain)

    gainInDollars = amountOutInDollars - amountInInDollars

    return gainInDollars

    
    # if assetIn.assetType == 'STABLE':
    #     priceAssetInInDollars = 1
    #     priceAssetOutInDollars = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutNet, isSell=False)
    #     amountOut = getValueOfAssetInRune
    # else:
    #     priceAssetInInDollars = orderbook_average_price(orderbook_data=orderbookData, amount=amountIn,  isSell=True)
    #     priceAssetOutInDollars = 1


    # amountInInStable = amountIn * priceAssetInInDollars
    # amountOutInStable = amountOutNet * priceAssetOutInDollars

    # gainInStable = amountOutInStable - amountInInStable
    
    # logging.info(f'assetIn {assetIn.symbol} gainInStable {gainInStable} amountInInStable {amountInInStable} amountOutInStable {amountOutInStable} amountIn {amountIn} amountOutNet {amountOutNet}')
    # return gainInStable


def calculateThorchainOutboundFees(assetOut):
    if assetOut.assetType != 'RUNE':
        outboundFees = getValueOfRuneInAsset(amount=OUTBOUND_FEES_RUNE * 10**DECIMALS_RUNE, asset=assetOut)
    else:
        outboundFees=OUTBOUND_FEES_RUNE * 10**DECIMALS_RUNE
    return outboundFees


def calculateThorchainSlipFeesInDollars(amountIn, assetIn, assetOut, balancesThorchain):
    if assetIn.assetType == 'RUNE':
        slipFees = formulaGetSwapFee(toRune=False, pool=assetOut.pool,amountIn=amountIn,isSynthSwap=True)
    elif assetOut.assetType == 'RUNE':
        slipFees = formulaGetSwapFee(toRune=True, pool=assetIn.pool,amountIn=amountIn,isSynthSwap=True)
    else:
        slipFees = formulaGetDoubleSwapFee(amountIn=amountIn, poolIn=assetIn.pool, poolOut=assetOut.pool,isSynthSwapIn=True,isSynthSwapOut=True,assetOut=assetOut)


    if assetOut.assetType != 'STABLE':
        slipFeesInDollars = getValueInDollarsThorchain(amount=slipFees, asset=assetOut, balancesThorchain=balancesThorchain) 
    else:
        slipFeesInDollars = slipFees

    return slipFeesInDollars


def getAmountOutRealFromTxThorchain(txHash: str):
    txHash = txHash.replace('"', '')
    urlTx = f"{URL_TX_DATA_THOR}{txHash}/signers"
    try:
        responseTx = requests.get(urlTx)
        if responseTx.status_code == 200:
            responseTx = responseTx.json()
            amountOutReal = int(responseTx["out_txs"][0]["coins"][0]["amount"])
            blockReal = responseTx['consensus_height']
        else:
            logging.warning(f"Failed to fetch data: Status code {responseTx.status_code} {responseTx.text}")
            amountOutReal, blockReal=None, None
    except Exception as err:
        logging.warning(f'error : {err} for {txHash}')

    return amountOutReal, blockReal


def createThorchainOpportunityForBybit(pairThorchain:PairDex, amountInMax: float, typeOpp: str, orderbookData: Dict, balancesThorchain:BalancesThorchain
):
    assetIn = pairThorchain.assetIn
    assetOut = pairThorchain.assetOut
    poolIn = assetIn.pool
    poolOut = assetOut.pool
    
    if poolIn.status == "Available" and poolOut.status == "Available":
        (amountInOpti, gainNetInStable) = dichotomieCexDex(
            f=formulaGainStableCexDex,
            low=10,
            high=int(amountInMax),
            e=500,
            assetIn=assetIn,
            assetOut=assetOut,
            isSynthSwapIn=True,
            isSynthSwapOut=True,
            orderbookData=orderbookData,
            balancesThorchain=balancesThorchain
        )
        
        
        amountOutOpti = formulaDoubleSwapOutput(amountIn=amountInOpti, poolIn=poolIn, poolOut=poolOut, isSynthSwapIn=True, isSynthSwapOut=True)
        # logging.info(f'out de la dichotomie, amountInOpti/1e8 = {amountInOpti/1e8} amountOutNet/1e8 = {amountOutNet/1e8}')
        
    #     if assetIn.assetType == 'STABLE':
    #         priceAssetInInDollars = 1
    #         bybitAssetPrice = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutOpti/ 10**assetIn.decimals,  isSell=True)
    #         amountOutBybit = amountOutOpti*bybitAssetPrice

    #     else:
    #         priceAssetInInDollars = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutOpti/ 10**assetIn.decimals,  isSell=False)
    #         bybitAssetPrice = priceAssetInInDollars
    #         amountOutBybit = amountOutOpti/bybitAssetPrice

    #     priceBuy = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutOpti/ 10**assetIn.decimals,  isSell=False)
    #     priceSell = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutOpti/ 10**assetIn.decimals,  isSell=True)

    # # amountOutBybit = amountOutThorchain*bybitAssetPrice
    #     amountInThorchainInStable = amountInOpti * priceAssetInInDollars
    #     amountOutBybitInStable = amountOutBybit * priceAssetInInDollars

    #     gainInStable = amountOutBybitInStable - amountInThorchainInStable
        
        # logging.info(f'FIN DE DICHOTOMIE : amountOutNetThor {amountOutOpti/1e8} amountOutBybit {amountOutBybit/1e8} priceAssetInInDollars {priceAssetInInDollars} bybitAssetPrice {bybitAssetPrice} priceSell {priceSell} priceBuy {priceBuy} gainInStable {gainInStable/1e8}')

        if amountOutOpti < poolOut.synthSupplyRemaining:
            
            amountOutInRune = getValueOfAssetInRune(amount=amountOutOpti,asset=assetOut)
            assetTransitionForOutboundFees = copy.deepcopy(assetOut)
            assetTransitionForOutboundFees.pool.balanceRuneInPoolAsset += amountOutInRune    
            
            outboundFees = getValueOfRuneInAsset(
                amount=OUTBOUND_FEES_RUNE * 10**DECIMALS_RUNE, asset=assetTransitionForOutboundFees)
            
            networkFees = getValueOfRuneInAsset(
                amount=NETWORK_FEES_RUNE * 10**DECIMALS_RUNE, asset=assetTransitionForOutboundFees)
            
            # logging.info(f'outboundFees = {outboundFees/1e8}')

            slipFees = formulaGetDoubleSwapFee(amountIn=amountInOpti, poolIn=poolIn, poolOut=poolOut,isSynthSwapIn=True,isSynthSwapOut=True,assetOut=assetOut)
            if assetOut.assetType != 'STABLE':
                slipFeesInDollars = getValueInDollarsThorchain(amount=slipFees, asset=assetOut, balancesThorchain=balancesThorchain) 
            else:
                slipFeesInDollars = slipFees

            if assetIn.assetType != "STABLE":
                amountInInDollars = getValueInDollarsThorchain(amount=amountInOpti, asset=assetIn, balancesThorchain=balancesThorchain)
            else:
                amountInInDollars = amountInOpti 
            
            amountOutEstimated = amountOutOpti - outboundFees - networkFees
            
            # logging.info(f'out de la dichotomie, amountInOpti/1e8 = {amountInOpti/1e8} amountOutEstimated/1e8 = {amountOutEstimated/1e8}')
            # logging.info(f'createThorchainOpportunityForBybit assetIn : {assetIn.symbol} assetOut {assetOut.symbol} amountInOpti {amountInOpti} amountInInDollars {amountInInDollars} amountOutEstimated {amountOutEstimated}')

            newOpp = OpportunityThorchain(
                pairAsset=pairThorchain,
                amountIn=int(amountInOpti),
                amountInInDollars=amountInInDollars / 10**assetIn.decimals,
                amountOutEstimated=int(amountOutEstimated),
                amountOutReal=0,
                typeOpp=typeOpp,
                outboundFees=int(outboundFees),
                slipFees=slipFeesInDollars/10**assetOut.decimals,
                txHash='',
                gainNetInAsset=0,
                gainNetInDollars=0,
                gainTotalEstimated=0,
                gainTotalReal=0
            )

        else:
            logging.warning(
                f"synthSupplyRemaining too low for {assetOut.symbol}, amountOutOpti {amountOutOpti} and SynthSupplyRemaining {poolOut.synthSupplyRemaining}"
            )
    else:
        logging.warning(
            f"amountIn NULL or pool disable assetIn {assetIn.symbol} assetOut.symbol {assetOut.symbol} poolIn.status {poolIn.status} poolOut.status {poolOut.status}"
        )

    return newOpp


def createThorchainOpportunityForBybitScout(pairThorchain:PairDex, amountIn: float, typeOpp: str, orderbookData: Dict, balancesThorchain:BalancesThorchain
):
    assetIn = pairThorchain.assetIn
    assetOut = pairThorchain.assetOut
    poolIn = assetIn.pool
    poolOut = assetOut.pool
    
    if poolOut.status == "Available":
        
        amountOutNet = formulaDoubleSwapOutput(amountIn=amountIn, poolIn=poolIn, poolOut=poolOut, isSynthSwapIn=True, isSynthSwapOut=True)

        if amountOutNet < poolOut.synthSupplyRemaining:
            
            amountOutInRune = getValueOfAssetInRune(amount=amountOutNet,asset=assetOut)
            assetTransitionForOutboundFees = copy.deepcopy(assetOut)
            assetTransitionForOutboundFees.pool.balanceRuneInPoolAsset += amountOutInRune    
            
            outboundFees = getValueOfRuneInAsset(
                amount=OUTBOUND_FEES_RUNE * 10**DECIMALS_RUNE, asset=assetTransitionForOutboundFees)
            
            slipFees = formulaGetDoubleSwapFee(amountIn=amountIn, poolIn=poolIn, poolOut=poolOut,isSynthSwapIn=True,isSynthSwapOut=True,assetOut=assetOut)
            if assetOut.assetType != 'STABLE':
                slipFeesInDollars = getValueInDollarsThorchain(amount=slipFees, asset=assetOut, balancesThorchain=balancesThorchain) 
            else:
                slipFeesInDollars = slipFees

            if assetIn.assetType != "STABLE":
                amountInInDollars = getValueInDollarsThorchain(amount=amountIn, asset=assetIn, balancesThorchain=balancesThorchain)
            else:
                amountInInDollars = amountIn 
            
            amountOutEstimated = amountOutNet - outboundFees*2
            
            # logging.info(f'createThorchainOpportunityForBybit assetIn : {assetIn.symbol} assetOut {assetOut.symbol} amountInOpti {amountInOpti} amountInInDollars {amountInInDollars} amountOutEstimated {amountOutEstimated}')

            newOpp = OpportunityThorchain(
                pairAsset=pairThorchain,
                amountIn=amountIn,
                amountInInDollars=amountInInDollars / 10**assetIn.decimals,
                amountOutEstimated=amountOutEstimated,
                amountOutReal=0,
                typeOpp=typeOpp,
                outboundFees=outboundFees,
                slipFees=slipFeesInDollars/10**assetOut.decimals,
                txHash='',
                gainNetInAsset=0,
                gainNetInDollars=0,
                gainTotalEstimated=0,
                gainTotalReal=0
            )

        else:
            logging.warning(
                f"synthSupplyRemaining too low for {assetOut.symbol}, amountIN {amountIn} and SynthSupplyRemaining {poolOut.synthSupplyRemaining}"
            )
    else:
        logging.warning(
            f"amountIn NULL or pool disable, amountIN {amountIn} poolStatus {poolOut.status}"
        )

    return newOpp


def createThorchainSynthOnBlockOpportunity(
    pairThorchain:PairDex, amountIn: float, typeOpp: str, balancesThorchain:BalancesThorchain
):
    assetIn = pairThorchain.assetIn
    assetOut = pairThorchain.assetOut

    poolIn = assetIn.pool
    poolOut = assetOut.pool

    if poolIn.status == "Available" and poolOut.status == "Available":
        (amountInOpti, gainNetInAssetOut) = dichotomieOnBlock(
            f=formulaGainDoubleSwapOutput,
            low=10,
            high=float(amountIn),
            e=1,
            assetIn=assetIn,
            assetOut=assetOut,
            isSynthSwapIn=True,
            isSynthSwapOut=True,
        )
        
        amountOutOpti = amountInOpti + gainNetInAssetOut
        
        if amountOutOpti < poolOut.synthSupplyRemaining:
            amountOutInRune = getValueOfAssetInRune(amount=amountOutOpti,asset=assetOut)
            assetTransitionForOutboundFees = copy.deepcopy(assetOut)
            assetTransitionForOutboundFees.pool.balanceRuneInPoolAsset += amountOutInRune

            outboundFees = getValueOfRuneInAsset(
                amount=OUTBOUND_FEES_RUNE * 10**DECIMALS_RUNE, asset=assetTransitionForOutboundFees)

            networkFees = getValueOfRuneInAsset(
                amount=NETWORK_FEES_RUNE * 10**DECIMALS_RUNE, asset=assetTransitionForOutboundFees)
            
            slipFees = formulaGetDoubleSwapFee(amountIn=amountInOpti, poolIn=poolIn, poolOut=poolOut,isSynthSwapIn=True,isSynthSwapOut=True,assetOut=assetOut)
            
            if assetOut.assetType != 'STABLE':
                slipFeesInDollars = getValueInDollarsThorchain(amount=slipFees, asset=assetOut, balancesThorchain=balancesThorchain) 
            else:
                slipFeesInDollars = slipFees

            gainNetInAssetOut = gainNetInAssetOut - outboundFees - networkFees #network fee = outbound fee, on simplifie en ôtant network fee en assetOut

            gainNetInDollars = gainNetInAssetOut
            amountInInDollars = amountInOpti
            
            if assetIn.assetType != 'STABLE':
                gainNetInDollars = getValueInDollarsThorchain(amount=gainNetInAssetOut, asset=assetOut, balancesThorchain=balancesThorchain) 
                amountInInDollars = getValueInDollarsThorchain(amount=amountInOpti, asset=assetIn, balancesThorchain=balancesThorchain)
                
            amountOutEstimated = amountOutOpti - outboundFees - networkFees

            newOpp = OpportunityThorchain(
                pairAsset=pairThorchain,
                amountIn=int(amountInOpti),
                amountInInDollars=amountInInDollars/ 10**assetIn.decimals,
                amountOutEstimated=int(amountOutEstimated),
                amountOutReal=0,
                gainNetInAsset=gainNetInAssetOut/ 10**assetOut.decimals,
                gainNetInDollars=gainNetInDollars/ 10**assetOut.decimals,
                typeOpp=typeOpp,
                outboundFees=outboundFees,
                slipFees=slipFeesInDollars/10**assetOut.decimals,
                txHash='',
                gainTotalEstimated=gainNetInDollars/10**assetOut.decimals,
                gainTotalReal=0
            )

        else:
            logging.warning(
                f"synthSupplyRemaining too low for {assetIn.symbol}, amountOpti {amountInOpti} and SynthSupplyRemaining {poolOut.synthSupplyRemaining}"
            )
    else:
        logging.warning(
            f"amountIn NULL or pool disable, amountIN {amountIn} assetIn {assetIn.symbol} assetOut.symbol {assetOut.symbol} poolIn.status {poolIn.status} poolOut.status {poolOut.status}"
        )

    return newOpp




def createThorchainOpportunityForMaya(
    pairThorchain, amountIn, typeOpp, balancesThorchain):

    assetIn = pairThorchain.assetIn
    assetOut = pairThorchain.assetOut

    if assetIn.assetType == 'RUNE':
        poolOut = assetOut.pool
        poolIn = poolOut
    elif assetOut.assetType=='RUNE':
        poolIn = assetIn.pool
        poolOut = poolIn
    else:
        poolIn = assetIn.pool
        poolOut = assetOut.pool

    if poolIn.status == "Available" and poolOut.status == "Available":
        amountOut = getThorchainSwapOutput(amountIn, assetIn, assetOut)
        
        if assetOut.assetType != 'RUNE' and amountOut >= poolOut.synthSupplyRemaining:
            logging.warning(
                f"createThorchainOpportunityForMaya - synthSupplyRemaining too low for {assetOut.symbol}, amountOut {amountOut} and SynthSupplyRemaining {poolOut.synthSupplyRemaining}"
            )
            return  # Exit the function as the condition is not met

        outboundFees = calculateThorchainOutboundFees(assetOut)
        slipFeesInDollars = calculateThorchainSlipFeesInDollars(amountIn, assetIn, assetOut, balancesThorchain)

        amountInInDollars = amountIn
        if assetIn.assetType != 'STABLE':
            amountInInDollars = getValueInDollarsThorchain(amount=amountInInDollars, asset=assetIn, balancesThorchain=balancesThorchain)

        amountOutEstimated = amountOut - outboundFees*2

        newOpp = OpportunityThorchain(
            pairAsset=pairThorchain,
            amountIn=int(amountIn),
            amountInInDollars=amountInInDollars/ 10**assetIn.decimals,
            amountOutEstimated=int(amountOutEstimated),
            amountOutReal=0,
            gainNetInAsset=0,
            gainNetInDollars=0,
            typeOpp=typeOpp,
            outboundFees=int(outboundFees),
            slipFees=slipFeesInDollars/10**assetOut.decimals,
            txHash='',
            gainTotalEstimated=0,
            gainTotalReal=0
        )
        return newOpp
    
    else:
        logging.warning(
            f"createThorchainOpportunityForMaya - amountIn NULL or pool disable, amountIN {amountIn} poolInStatus {poolIn.status} poolOutStatus {poolOut.status}"
        )




















