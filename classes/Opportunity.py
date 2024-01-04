from classes.Pair import PairCex,PairDex,PairCexDex, PairDexDex

class OpportunityBybit:

    def __init__(self, pairAsset : PairCex, amountInEstimated:float, amountInReal:float, amountOutEstimated:float, amountOutReal:float, typeOpp:str, bybitAssetPrice:float, orderId:int):
        self.pairAsset = pairAsset
        self.amountInEstimated = amountInEstimated
        self.amountInReal = amountInReal
        self.amountOutEstimated = amountOutEstimated
        self.amountOutReal = amountOutReal
        self.typeOpp = typeOpp
        self.bybitAssetPrice = bybitAssetPrice
        self.orderId = orderId

class OpportunityThorchain:

    def __init__(self, pairAsset:PairDex, amountIn:int, amountInInDollars:float, amountOutEstimated:int, amountOutReal:int, typeOpp:str, txHash:str, gainNetInAsset:int, gainNetInDollars:float, gainTotalEstimated, gainTotalReal,detectedBlock=1, realBlock=1, slipFees=0, outboundFees=0):
        self.pairAsset = pairAsset
        self.amountIn = amountIn
        self.amountInInDollars = amountInInDollars
        self.amountOutEstimated = amountOutEstimated
        self.amountOutReal = amountOutReal
        self.typeOpp = typeOpp
        self.txHash = txHash
        self.gainNetInAsset = gainNetInAsset
        self.gainNetInDollars = gainNetInDollars
        self.gainTotalEstimated = gainTotalEstimated
        self.gainTotalReal = gainTotalReal
        self.detectedBlock = detectedBlock
        self.realBlock = realBlock
        self.slipFees = slipFees
        self.outboundFees = outboundFees
    

class OpportunityCexDex:

    def __init__(self, pairCexDex:PairCexDex, opportunityThorchain:OpportunityThorchain, opportunityBybit:OpportunityBybit, gainAssetInDexEstimated, gainAssetInDexReal, gainAssetOutDexEstimated, gainAssetOutDexReal, gainTotalEstimated, gainTotalReal):
        self.pairCexDex = pairCexDex
        self.opportunityThorchain = opportunityThorchain
        self.opportunityBybit = opportunityBybit
        self.gainAssetInDexEstimated = gainAssetInDexEstimated
        self.gainAssetInDexReal = gainAssetInDexReal
        self.gainAssetOutDexEstimated = gainAssetOutDexEstimated
        self.gainAssetOutDexReal = gainAssetOutDexReal
        self.gainTotalEstimated = gainTotalEstimated
        self.gainTotalReal = gainTotalReal


class OpportunityMaya:

    def __init__(self, pairAsset:PairDex, amountIn:int, amountInInDollars:float, amountOutEstimated:int, amountOutReal:int, typeOpp:str, txHash:str, gainNetInAsset:int, gainNetInDollars:float, gainTotalEstimated, gainTotalReal, detectedBlock=1, realBlock=1, slipFees=0, outboundFees=0, networkFees=0):
        self.pairAsset = pairAsset
        self.amountIn = amountIn
        self.amountInInDollars = amountInInDollars
        self.amountOutEstimated = amountOutEstimated
        self.amountOutReal = amountOutReal
        self.typeOpp = typeOpp
        self.txHash = txHash
        self.gainNetInAsset = gainNetInAsset
        self.gainNetInDollars = gainNetInDollars
        self.gainTotalEstimated = gainTotalEstimated
        self.gainTotalReal = gainTotalReal
        self.detectedBlock = detectedBlock
        self.realBlock = realBlock
        self.slipFees = slipFees
        self.outboundFees = outboundFees
        self.networkFees = networkFees



class OpportunityDexDex:

    def __init__(self, pairDexDex:PairDexDex, opportunityThorchain:OpportunityThorchain, opportunityMaya:OpportunityMaya, gainAssetInDexEstimated, gainAssetInDexReal, gainAssetOutDexEstimated, gainAssetOutDexReal, gainTotalEstimated, gainTotalReal):
        self.pairDexDex = pairDexDex
        self.opportunityThorchain = opportunityThorchain
        self.opportunityMaya = opportunityMaya
        self.gainAssetInDexEstimated = gainAssetInDexEstimated
        self.gainAssetInDexReal = gainAssetInDexReal
        self.gainAssetOutDexEstimated = gainAssetOutDexEstimated
        self.gainAssetOutDexReal = gainAssetOutDexReal
        self.gainTotalEstimated = gainTotalEstimated
        self.gainTotalReal = gainTotalReal