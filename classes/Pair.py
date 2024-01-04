class PairCex:
    def __init__(self, assetIn, assetOut, type, orderbookSymbol:str, orderbook):
        self.assetIn = assetIn
        self.assetOut = assetOut
        self.type = type
        self.orderbookSymbol=orderbookSymbol    
        self.orderbook = orderbook

class PairDex:
    def __init__(self, assetIn, assetOut, type):
        self.assetIn = assetIn
        self.assetOut = assetOut
        self.type = type        

class PairCexDex:
    def __init__(self, pairAssetCex:PairCex, pairAssetDex:PairDex):
        self.pairAssetCex = pairAssetCex
        self.pairAssetDex = pairAssetDex   
    

class PairDexDex:
    def __init__(self, pairAssetDex1:PairDex, pairAssetDex2:PairDex):
        self.pairAssetDex1 = pairAssetDex1
        self.pairAssetDex2 = pairAssetDex2   
     