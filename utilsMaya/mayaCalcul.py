import math
import logging
import requests 

from classes.Pool import PoolMaya, Pool
from classes.Asset import AssetMaya, AssetThorchain
from classes.Balances import BalancesMaya, Balances
from classes.Pair import PairDex
from classes.Opportunity import OpportunityMaya

from constantes.constantes import OUTBOUND_FEES_CACAO, DECIMALS_CACAO, NETWORK_FEES_CACAO
from constantes.url import URL_TX_DATA_MAYA
from utilsBybit.bybit_price_calculation import orderbook_average_price
from utilsThorchain.thorchainCalcul import formulaDoubleSwapOutput, getValueInDollarsThorchain, formulaSwapOutput

import copy


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


def dichotomieCexDex(
    f,
    low,
    high,
    e,
    assetIn,
    assetOut,
    isSynthSwapIn,
    isSynthSwapOut,
    orderbookData):
    while high - low > e:
        mid = low + (high - low)/2
        
        f_mid = f(mid, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData)
        f_high = f(high, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData)

        if f_mid < f_high:
            low = mid
        else:
            high = mid

    mid = (low + high) / 2
    final_value = f(mid, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, orderbookData)
    return mid, final_value


def dichotomieMayaThor(
    f,
    low,
    high,
    e,
    assetIn:AssetMaya,
    assetOut:AssetMaya,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    balances:Balances):
    while high - low > e:
        mid = low + (high - low)/2
        
        f_mid = f(mid, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, balances)
        f_high = f(high, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, balances)

        if f_mid < f_high:
            low = mid
        else:
            high = mid

    mid = (low + high) / 2
    final_value = f(mid, assetIn, assetOut, isSynthSwapIn, isSynthSwapOut, balances)
    return mid, final_value


# def dichotomieMayaThor(
#     f,
#     low,
#     high,
#     e,
#     assetIn:AssetMaya,
#     assetOut:AssetMaya,
#     poolIn: PoolMaya,
#     poolOut: PoolMaya,
#     isSynthSwapIn: bool,
#     isSynthSwapOut: bool,
#     balancesMaya:BalancesMaya
# ) -> int:
#     mid = 0
#     while high - low > e:
#         mid = int((high + low) / 2)
#         p1 = int(low + (high - low) / 4)
#         p2 = int(low + 3 * (high - low) / 4)
#         if f(p1, assetIn,assetOut, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, balancesMaya) > f(
#             mid, assetIn,assetOut, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, balancesMaya
#         ):
#             high = mid
#         elif f(mid, assetIn,assetOut,poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, balancesMaya) < f(
#             p2, assetIn,assetOut,poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, balancesMaya
#         ):
#             low = mid
#         else:
#             low = p1
#             high = p2

#     return (mid, f(mid, assetIn, assetOut, poolIn, poolOut, isSynthSwapIn, isSynthSwapOut, balancesMaya))


def formulaGainDoubleSwapOutput(
    amountIn: float,
    poolIn: PoolMaya,
    poolOut: PoolMaya,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    synthMultiplier=1,
) -> float:
    
    feesSwap = formulaGetDoubleSwapFee(amountIn=amountIn, poolIn=poolIn, poolOut=poolOut,isSynthSwapIn=isSynthSwapIn,isSynthSwapOut=isSynthSwapOut)
    amountOut = formulaDoubleSwapOutputMaya(amountIn=amountIn,poolIn=poolIn,poolOut=poolOut,isSynthSwapIn=isSynthSwapIn,isSynthSwapOut=isSynthSwapOut)

    return amountOut - amountIn


def formulaSwapInput(
    toCacao: bool, pool: PoolMaya, amountOut: float, isSynthSwap: bool, synthMultiplier=1
) -> float:
    try:
        X = pool.balanceAssetInPool  if toCacao == True else pool.balanceCacaoInPoolAsset 
        Y = pool.balanceCacaoInPoolAsset if toCacao == True else pool.balanceAssetInPool
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
    poolIn: PoolMaya,
    poolOut: PoolMaya,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    synthMultiplier=1,
) -> float:
    r = formulaSwapInput(False, poolOut, amountOut, isSynthSwapIn, synthMultiplier)
    input = formulaSwapInput(True, poolIn, r, isSynthSwapOut, synthMultiplier)
    return input


def formulaSwapOutputMaya(
    toCacao: bool, pool: PoolMaya, amountIn: float, isSynthSwap: bool, synthMultiplier=1
) -> float:
    X = pool.balanceAssetInPool if toCacao == True else pool.balanceCacaoInPoolAsset
    Y = pool.balanceCacaoInPoolAsset if toCacao == True else pool.balanceAssetInPool 
    x = float(amountIn)
    num = x * X * Y
    denum = (x + X) ** 2

    # if isSynthSwap == True:
    #     X = X * synthMultiplier
    #     Y = Y * synthMultiplier
    # logging.info(f" x, X, Y {x,X,Y}")
    amountOut = num / denum

    return amountOut


def formulaDoubleSwapOutputMaya(
    amountIn: float,
    poolIn: PoolMaya,
    poolOut: PoolMaya,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    synthMultiplier=1,
) -> float:
    
    amountAssetInToCacao = formulaSwapOutputMaya(
        True, poolIn, amountIn, isSynthSwapIn, synthMultiplier
    )

    amountOut = formulaSwapOutputMaya(
        False, poolOut, amountAssetInToCacao, isSynthSwapOut, synthMultiplier
    )


    return int(amountOut)


def formulaGetSwapFee(
    toCacao: bool, pool: PoolMaya, amountIn: float, isSynthSwap: bool, synthMultiplier=1
) -> float:
    X = pool.balanceAssetInPool if toCacao == True else pool.balanceCacaoInPoolAsset 
    Y = pool.balanceCacaoInPoolAsset  if toCacao == True else pool.balanceAssetInPool 

    if isSynthSwap == True:
        X = X * synthMultiplier
        Y = Y * synthMultiplier

    x = amountIn

    return (x * x * Y) / (x + X) ** 2


def getValueOfAssetInCacao(amount: float, pool: PoolMaya) -> float:
    R = 0
    A = 1

    # pool = asset.pool
    R = float(pool.balanceCacaoInPoolAsset) 
    A = float(pool.balanceAssetInPool) 

    return (float(amount) * R) / A


def getValueOfCacaoInAsset(amount: float, pool: PoolMaya) -> float:
    R = 1
    A = 0

    R = float(pool.balanceCacaoInPoolAsset) 
    A = float(pool.balanceAssetInPool) 

    return (amount * A) / R


def formulaGetDoubleSwapFee(
    amountIn: float,
    poolIn: PoolMaya,
    poolOut: PoolMaya,
    isSynthSwapIn: bool,
    isSynthSwapOut: bool,
    synthMultiplier=1,
) -> float:
    fee1 = formulaGetSwapFee(True, poolIn, amountIn, isSynthSwapIn, synthMultiplier)
    r = formulaSwapOutputMaya(True, poolIn, amountIn, isSynthSwapIn, synthMultiplier)
    fee2 = formulaGetSwapFee(False, poolOut, r, isSynthSwapOut, synthMultiplier)
    fee1_asset = getValueOfCacaoInAsset(fee1, poolOut)
    return fee1_asset + fee2


def getValueOfCacaoInDollars(amount: float, responsePool) -> float:
    R = 1
    A = 0

    for pool in responsePool:
        if pool["asset"] == "ETH.USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48":
            R = float(pool["balance_cacao"]) 
            A = float(pool["balance_asset"])

    return (amount * A) / R


def getValueOfDollarsInAssetMaya(amount: float, asset: AssetMaya, balancesMaya:BalancesMaya) -> float:

    for asset_ in balancesMaya.listAssets:
        if asset_.poolName == "ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7":
            poolUSDBalanceAsset = asset_.pool.balanceAssetInPool *1e2
            poolUSDBalanceCacao = asset_.pool.balanceCacaoInPoolAsset 

    poolAssetBalanceAsset = asset.pool.balanceAssetInPool
    poolAssetBalanceCacao = asset.pool.balanceCacaoInPoolAsset
    
    valueInDollars = (
        float(amount)
        * (poolAssetBalanceAsset / poolAssetBalanceCacao)
        * (poolUSDBalanceCacao / poolUSDBalanceAsset)
    )
    return valueInDollars


def getValueInDollarsMaya(amount: float, asset: AssetMaya, balancesMaya:BalancesMaya) -> float:

    for asset_ in balancesMaya.listAssets:
        if asset_.poolName == "ETH.USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7":
            poolUSDBalanceAsset = asset_.pool.balanceAssetInPool *1e2
            poolUSDBalanceCacao = asset_.pool.balanceCacaoInPoolAsset 

    poolAssetBalanceAsset = asset.pool.balanceAssetInPool
    poolAssetBalanceCacao = asset.pool.balanceCacaoInPoolAsset
    
    valueInDollars = (
        float(amount)
        * (poolUSDBalanceAsset / poolUSDBalanceCacao)
        * (poolAssetBalanceCacao / poolAssetBalanceAsset)
    )
    return valueInDollars


def formulaGainInStable(amountIn: int, assetIn:AssetMaya, assetOut: AssetMaya, isSynthSwapIn: bool, isSynthSwapOut: bool, orderbookData, synthMultiplier=1):


    amountOutMaya = formulaDoubleSwapOutputMaya(amountIn=amountIn, poolIn=assetIn.pool, poolOut=assetOut.pool, isSynthSwapIn=isSynthSwapIn, isSynthSwapOut=isSynthSwapOut)
    
    if assetIn.assetType == 'STABLE':
        priceAssetInInDollars = 1
        bybitAssetPrice = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutMaya/ 10**DECIMALS_CACAO,  isSell=True)
        amountOutBybit = amountOutMaya*bybitAssetPrice
    else:
        priceAssetInInDollars = orderbook_average_price(orderbook_data=orderbookData, amount=amountOutMaya/ 10**DECIMALS_CACAO,  isSell=False)
        bybitAssetPrice = priceAssetInInDollars
        amountOutBybit = amountOutMaya/bybitAssetPrice


    amountInMayaInStable = amountIn * priceAssetInInDollars
    amountOutBybitInStable = amountOutBybit * priceAssetInInDollars

    gainInStable = amountOutBybitInStable - amountInMayaInStable
    
    return gainInStable


def formulaGainMayaThor(amountIn: int, assetIn:AssetMaya, assetOut:AssetMaya, isSynthSwapIn: bool, isSynthSwapOut: bool, balances:Balances, synthMultiplier=1):
    asset:AssetThorchain
    for asset in balances.balancesThorchain.listAssets:
        if asset.poolName == assetOut.poolName:
            assetInThorchain = asset
        if asset.poolName == assetIn.poolName:
            assetOutThorchain = asset

    amountOutMaya = formulaDoubleSwapOutputMaya(amountIn=amountIn, poolIn=assetIn.pool, poolOut=assetOut.pool, isSynthSwapIn=isSynthSwapIn, isSynthSwapOut=isSynthSwapOut)
    
    amountInThorchain = amountOutMaya * 10**assetInThorchain.decimals / 10**DECIMALS_CACAO

    if assetInThorchain.assetType == 'RUNE':
        amountOutThorchain = formulaSwapOutput(toRune=False,pool=assetOutThorchain.pool,amountIn=amountInThorchain,isSynthSwap=True)
    elif assetOutThorchain.assetType == 'RUNE':
        amountOutThorchain = formulaSwapOutput(toRune=True,pool=assetInThorchain.pool,amountIn=amountInThorchain,isSynthSwap=True)
    else:
        amountOutThorchain = formulaDoubleSwapOutput(amountIn=amountInThorchain, poolIn=assetInThorchain.pool, poolOut=assetOutThorchain.pool, isSynthSwapIn=True, isSynthSwapOut=True)


    gainAssetInMaya = (amountOutThorchain/10**assetOutThorchain.decimals) - (amountIn/10**DECIMALS_CACAO)
    gainAssetOutMaya = (amountOutMaya/10**DECIMALS_CACAO) - (amountInThorchain/10**assetInThorchain.decimals)
    
    gainAssetInMayaInDollars = getValueInDollarsThorchain(amount=gainAssetInMaya*10**assetOutThorchain.decimals, asset=assetOutThorchain, balancesThorchain=balances.balancesThorchain)
    gainAssetOutMayaInDollars = getValueInDollarsThorchain(amount=gainAssetOutMaya*10**assetInThorchain.decimals, asset=assetInThorchain, balancesThorchain=balances.balancesThorchain)

    gainInDollars = gainAssetInMayaInDollars/10**assetOutThorchain.decimals + gainAssetOutMayaInDollars / 10**assetInThorchain.decimals
    
    # logging.info(f'MAYA : {assetIn.symbol} to {assetOut.symbol} amountIn {amountIn/1e10} amountOut {amountOutMaya/1e10} / THOR : {assetInThorchain.symbol} to {assetOutThorchain.symbol} amountIn {amountInThorchain/1e8} amountOut {amountOutThorchain/1e8} gainAssetInMaya {gainAssetInMaya} gainAssetOutMaya {gainAssetOutMaya} gainAssetInMayaInDollars {gainAssetInMayaInDollars} gainAssetOutMayaInDollars {gainAssetOutMayaInDollars} gainInDollars {gainInDollars}')
    return gainInDollars


def getAmountOutRealFromTxMaya(txHash: str):
    txHash = txHash.replace('"', '')
    urlTx = f"{URL_TX_DATA_MAYA}{txHash}/signers"
    try:
        responseTx = requests.get(urlTx)
        if responseTx.status_code == 200:
            responseTx = responseTx.json()
            amountOutReal = int(responseTx["out_txs"][0]["coins"][0]["amount"])
            blockReal = responseTx['finalised_height']
        else:
            logging.warning(f"Failed to fetch data: Status code {responseTx.status_code} {responseTx.text}")
            amountOutReal, blockReal=None, None
    except Exception as err:
        logging.warning(f'error : {err} for {txHash}')

    return amountOutReal, blockReal





def createMayaOpportunityForBybit(
    pairMaya:PairDex, amountIn: float, typeOpp: str, balancesMaya:BalancesMaya, orderbookData
):
    assetIn = pairMaya.assetIn 
    assetOut = pairMaya.assetOut
    
    assetInCopy = copy.deepcopy(pairMaya.assetIn)
    assetOutCopy = copy.deepcopy(pairMaya.assetOut)

    poolInToDichotomie = assetInCopy.pool
    poolOutToDichotomie = assetOutCopy.pool

    poolInToDichotomie.balanceAssetInPool = poolInToDichotomie.balanceAssetInPool * 10**DECIMALS_CACAO / 10**assetIn.decimals
    poolInToDichotomie.balanceCacaoInPoolAsset = poolInToDichotomie.balanceCacaoInPoolAsset 

    poolOutToDichotomie.balanceAssetInPool = poolOutToDichotomie.balanceAssetInPool * 10**DECIMALS_CACAO / 10**assetIn.decimals
    poolOutToDichotomie.balanceCacaoInPoolAsset = poolOutToDichotomie.balanceCacaoInPoolAsset
    poolOutToDichotomie.synthSupplyRemaining = poolOutToDichotomie.synthSupplyRemaining * 10**DECIMALS_CACAO / 10**assetIn.decimals
    
    if poolOutToDichotomie.status == "Available":
        (amountInOpti, gainNetInAssetOut) = dichotomieCexDex(
            f=formulaGainInStable,
            low=1,
            high=float(amountIn),
            e=1,
            assetIn=assetInCopy,
            assetOut=assetOutCopy,
            isSynthSwapIn=True,
            isSynthSwapOut=True,
            orderbookData=orderbookData
        )

        amountOutOpti = formulaDoubleSwapOutputMaya(amountIn=amountInOpti, poolIn=poolInToDichotomie, poolOut=poolOutToDichotomie, isSynthSwapIn=True, isSynthSwapOut=True)
        
        if amountOutOpti < poolOutToDichotomie.synthSupplyRemaining:
            amountOutInCacao = getValueOfAssetInCacao(amount=amountOutOpti,pool=poolOutToDichotomie)
            assetTransitionForOutboundFees = copy.deepcopy(assetOut)
            assetTransitionForOutboundFees.pool.balanceAssetInPool = poolOutToDichotomie.balanceAssetInPool 
            assetTransitionForOutboundFees.pool.balanceCacaoInPoolAsset = poolOutToDichotomie.balanceCacaoInPoolAsset
            assetTransitionForOutboundFees.pool.balanceCacaoInPoolAsset += amountOutInCacao
            
            outboundFees = getValueOfCacaoInAsset(
                amount=OUTBOUND_FEES_CACAO*10**DECIMALS_CACAO, pool=assetTransitionForOutboundFees.pool)
            
            networkFees = getValueOfCacaoInAsset(
                amount=NETWORK_FEES_CACAO*1e10, pool=assetTransitionForOutboundFees.pool)
            
            slipFees = formulaGetDoubleSwapFee(amountIn=amountInOpti, poolIn=poolInToDichotomie, poolOut=poolOutToDichotomie,isSynthSwapIn=True,isSynthSwapOut=True)
            
            if assetOut.assetType != 'STABLE':
                slipFeesInDollars = getValueInDollarsMaya(amount=slipFees, asset=assetTransitionForOutboundFees, balancesMaya=balancesMaya) 
            else:
                slipFeesInDollars = slipFees

            amountOutEstimated = amountOutOpti - outboundFees - networkFees

            if assetIn.assetType != "STABLE":
                amountInInDollars = getValueInDollarsMaya(amount=amountInOpti, asset=assetInCopy, balancesMaya=balancesMaya)
            else:
                amountInInDollars = amountInOpti 
            
            newOpp = OpportunityMaya(
                pairAsset=pairMaya,
                amountIn=int(amountInOpti * 10**assetIn.decimals / 10**DECIMALS_CACAO),
                amountInInDollars=amountInInDollars / 10**DECIMALS_CACAO,
                amountOutEstimated=int(amountOutEstimated* 10**assetOut.decimals / 10**DECIMALS_CACAO),
                amountOutReal=0,
                gainNetInAsset=0,
                gainNetInDollars=0,
                typeOpp=typeOpp,
                outboundFees=int(outboundFees* 10**assetOut.decimals / 10**DECIMALS_CACAO),
                slipFees=slipFeesInDollars / 10**DECIMALS_CACAO,
                txHash='',
                gainTotalEstimated=0,
                gainTotalReal=0,
                networkFees=int(networkFees* 10**assetOut.decimals / 10**DECIMALS_CACAO)
            )

        else:
            print(
                f"synthSupplyRemaining too low for {assetOut.symbol}, amountOut {amountOutOpti} and SynthSupplyRemaining {poolOutToDichotomie.synthSupplyRemaining}"
            )
    else:
        print(
            f"amountIn NULL or pool disable, amountIN {amountIn} poolStatus {poolOutToDichotomie.status}"
        )

    return newOpp


def createMayaSynthOnBlockOpportunity(
    pairMaya:PairDex, amountIn: float, typeOpp: str, balancesMaya:BalancesMaya
):
    assetIn = pairMaya.assetIn 
    assetOut = pairMaya.assetOut
    
    assetInCopy = copy.deepcopy(pairMaya.assetIn)
    assetOutCopy = copy.deepcopy(pairMaya.assetOut)

    poolInToDichotomie = assetInCopy.pool
    poolOutToDichotomie = assetOutCopy.pool

    poolInToDichotomie.balanceAssetInPool = poolInToDichotomie.balanceAssetInPool * 1e2
    poolInToDichotomie.balanceCacaoInPoolAsset = poolInToDichotomie.balanceCacaoInPoolAsset  

    poolOutToDichotomie.balanceAssetInPool = poolOutToDichotomie.balanceAssetInPool *1e2
    poolOutToDichotomie.balanceCacaoInPoolAsset = poolOutToDichotomie.balanceCacaoInPoolAsset 
    poolOutToDichotomie.synthSupplyRemaining = poolOutToDichotomie.synthSupplyRemaining * 10**DECIMALS_CACAO / 10**assetIn.decimals
    
    if poolOutToDichotomie.status == "Available":
        (amountInOpti, gainNetInAssetOut) = dichotomieOnBlock(
            f=formulaGainDoubleSwapOutput,
            low=1,
            high=float(amountIn),
            e=1,
            assetIn=assetInCopy,
            assetOut=assetOutCopy,
            isSynthSwapIn=True,
            isSynthSwapOut=True,
        )
        amountOutOpti = amountInOpti + gainNetInAssetOut
        
        if amountOutOpti < poolOutToDichotomie.synthSupplyRemaining:

            amountOutInCacao = getValueOfAssetInCacao(amount=amountOutOpti,pool=poolOutToDichotomie)
            assetTransitionForOutboundFees = copy.deepcopy(assetOutCopy)
            assetTransitionForOutboundFees.pool.balanceAssetInPool = poolOutToDichotomie.balanceAssetInPool 
            assetTransitionForOutboundFees.pool.balanceCacaoInPoolAsset = poolOutToDichotomie.balanceCacaoInPoolAsset
            assetTransitionForOutboundFees.pool.balanceCacaoInPoolAsset += amountOutInCacao

            outboundFees = getValueOfCacaoInAsset(
                amount=OUTBOUND_FEES_CACAO*1e10, pool=assetTransitionForOutboundFees.pool)
            
            slipFees = formulaGetDoubleSwapFee(amountIn=amountInOpti, poolIn=poolInToDichotomie, poolOut=poolOutToDichotomie,isSynthSwapIn=True,isSynthSwapOut=True)
            if assetOut.assetType != 'STABLE':
                slipFeesInDollars = getValueInDollarsMaya(amount=slipFees, asset=assetTransitionForOutboundFees, balancesMaya=balancesMaya) 
            else:
                slipFeesInDollars = slipFees
                
            networkFees = getValueOfCacaoInAsset(
                amount=NETWORK_FEES_CACAO*1e10, pool=assetTransitionForOutboundFees.pool)
            
            gainNetInAssetOut = gainNetInAssetOut - outboundFees - networkFees

            if assetIn.assetType != 'STABLE':
                gainNetInDollars = getValueInDollarsMaya(amount=gainNetInAssetOut, asset=assetOutCopy, balancesMaya=balancesMaya)
                amountInInDollars = getValueInDollarsMaya(amount=amountInOpti, asset=assetInCopy, balancesMaya=balancesMaya) 
            else:
                gainNetInDollars = gainNetInAssetOut
                amountInInDollars = amountInOpti

            amountOutEstimated = amountOutOpti - outboundFees - networkFees

            newOpp = OpportunityMaya(
                    pairAsset=pairMaya,
                    amountIn=int(amountInOpti * 10**assetIn.decimals / 10**DECIMALS_CACAO),
                    amountInInDollars=amountInInDollars / 10**DECIMALS_CACAO,
                    amountOutEstimated=int(amountOutEstimated* 10**assetOut.decimals / 10**DECIMALS_CACAO),
                    amountOutReal=0,
                    gainNetInAsset=int(gainNetInAssetOut* 10**assetOut.decimals / 10**DECIMALS_CACAO),
                    gainNetInDollars=gainNetInDollars / 10**DECIMALS_CACAO,
                    typeOpp=typeOpp,
                    outboundFees=int(outboundFees* 10**assetOut.decimals / 10**DECIMALS_CACAO),
                    slipFees=slipFeesInDollars / 10**DECIMALS_CACAO,
                    networkFees=int(networkFees* 10**assetOut.decimals / 10**DECIMALS_CACAO),
                    txHash='',
                    gainTotalEstimated=gainNetInDollars / 10**DECIMALS_CACAO,
                    gainTotalReal=0
                )
    else:
        print(
            f"amountIn NULL or pool disable, amountIN {amountIn} poolStatus {poolOutToDichotomie.status}"
        )

    return newOpp


def createMayaOpportunityForThorchain(
    pairMaya:PairDex, amountIn: float, typeOpp: str, balances:Balances
):
    assetIn = pairMaya.assetIn 
    assetOut = pairMaya.assetOut
    
    assetInCopy = copy.deepcopy(pairMaya.assetIn)
    assetOutCopy = copy.deepcopy(pairMaya.assetOut)

    assetInCopy.pool.balanceAssetInPool = assetInCopy.pool.balanceAssetInPool * 1e2
    assetOutCopy.pool.balanceAssetInPool = assetOutCopy.pool.balanceAssetInPool *1e2
    assetOutCopy.pool.synthSupplyRemaining = assetOutCopy.pool.synthSupplyRemaining * 10**DECIMALS_CACAO / 10**assetIn.decimals
    
    if assetInCopy.pool.status == "Available" and assetOutCopy.pool.status == "Available":
        (amountInOpti, gainNetInDollars) = dichotomieMayaThor(
            f=formulaGainMayaThor,
            low=1000,
            high=float(amountIn),
            e=1000,
            assetIn=assetInCopy,
            assetOut=assetOutCopy,
            isSynthSwapIn=True,
            isSynthSwapOut=True,
            balances=balances
        )

        ##################
        # amountInOpti = amountIn
        # amountOut = formulaDoubleSwapOutput(amountIn=amountInOpti,poolIn=assetInCopy.pool, poolOut=assetOutCopy.pool, isSynthSwapIn=True,isSynthSwapOut=True)
        # gainNetInAssetOut= amountOut - amountInOpti
        ##################

        amountOutOpti = formulaDoubleSwapOutputMaya(amountIn=amountInOpti, poolIn=assetInCopy.pool, poolOut=assetOutCopy.pool, isSynthSwapIn=True, isSynthSwapOut=True)
        
        if amountOutOpti < assetOutCopy.pool.synthSupplyRemaining:

            amountOutInCacao = getValueOfAssetInCacao(amount=amountOutOpti,pool=assetOutCopy.pool)
            assetTransitionForOutboundFees = copy.deepcopy(assetOut)
            assetTransitionForOutboundFees.pool.balanceAssetInPool = assetOutCopy.pool.balanceAssetInPool 
            assetTransitionForOutboundFees.pool.balanceCacaoInPoolAsset = assetOutCopy.pool.balanceCacaoInPoolAsset
            assetTransitionForOutboundFees.pool.balanceCacaoInPoolAsset += amountOutInCacao

            outboundFees = getValueOfCacaoInAsset(amount=OUTBOUND_FEES_CACAO*10**DECIMALS_CACAO, pool=assetTransitionForOutboundFees.pool)
            
            slipFees = formulaGetDoubleSwapFee(amountIn=amountInOpti, poolIn=assetInCopy.pool, poolOut=assetOutCopy.pool,isSynthSwapIn=True,isSynthSwapOut=True)
            if assetOut.assetType != 'STABLE':
                slipFeesInDollars = getValueInDollarsMaya(amount=slipFees, asset=assetTransitionForOutboundFees, balancesMaya=balances.balancesMaya) 
            else:
                slipFeesInDollars = slipFees
                
            networkFees = getValueOfCacaoInAsset(amount=NETWORK_FEES_CACAO*10**DECIMALS_CACAO, pool=assetTransitionForOutboundFees.pool)
            
            # gainNetInAssetOut = gainNetInAssetOut - outboundFees - networkFees

            if assetIn.assetType != 'STABLE':
                amountInInDollars = getValueInDollarsMaya(amount=amountInOpti, asset=assetInCopy, balancesMaya=balances.balancesMaya) 
            else:
                amountInInDollars = amountInOpti

            amountOutEstimated = amountOutOpti - outboundFees - networkFees

            newOpp = OpportunityMaya(
                    pairAsset=pairMaya,
                    amountIn=int(amountInOpti * 10**assetIn.decimals / 10**DECIMALS_CACAO),
                    amountInInDollars=amountInInDollars / 10**DECIMALS_CACAO,
                    amountOutEstimated=int(amountOutEstimated* 10**assetOut.decimals / 10**DECIMALS_CACAO),
                    amountOutReal=0,
                    gainNetInAsset=0,
                    gainNetInDollars=0,
                    typeOpp=typeOpp,
                    outboundFees=int(outboundFees* 10**assetOut.decimals / 10**DECIMALS_CACAO),
                    slipFees=slipFeesInDollars / 10**DECIMALS_CACAO,
                    networkFees=int(networkFees* 10**assetOut.decimals / 10**DECIMALS_CACAO),
                    txHash='',
                    gainTotalEstimated=0,
                    gainTotalReal=0
                )
    else:
        logging.warning(
            f"amountIn NULL or pool disable, amountOutOpti {amountOutOpti} poolStatus {assetOutCopy.pool.status}"
        )

    return newOpp

