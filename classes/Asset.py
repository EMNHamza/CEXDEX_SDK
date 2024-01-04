from classes.Pool import Pool


class AssetThorchain:

    def __init__(self, chain, symbol, ticker, isSynth, poolName, balanceName, memoName, assetType, pool, decimals=8, balance=0,maxBalancePercentage=1):
        self.chain = chain
        self.symbol = symbol
        self.ticker = ticker
        self.isSynth = isSynth
        self.poolName = poolName
        self.balanceName = balanceName
        self.memoName = memoName
        self.assetType = assetType
        self.pool = pool
        self.balance = balance
        self.decimals = decimals
        self.maxBalancePercentage=maxBalancePercentage

class AssetBybit:

    def __init__(self, symbol:str, assetType:str, balanceName:str, balance=0, decimals=0):
        self.symbol = symbol
        self.assetType = assetType
        self.balance = balance
        self.decimals = decimals
        self.balanceName = balanceName

class AssetMaya:

    def __init__(self, chain, symbol, ticker, isSynth, poolName, balanceName, memoName, decimals, assetType, pool, balance=0, maxBalancePercentage=1):
        self.chain = chain
        self.symbol = symbol
        self.ticker = ticker
        self.isSynth = isSynth
        self.poolName = poolName
        self.balanceName = balanceName
        self.memoName = memoName
        self.decimals = decimals
        self.assetType = assetType
        self.pool = pool
        self.balance = balance
        self.maxBalancePercentage=maxBalancePercentage
