class Pool:
    def __init__(self,balanceAssetInPool, balanceRuneInPoolAsset, synthSupplyRemaining, status, block):
        self.balanceAssetInPool = balanceAssetInPool
        self.balanceRuneInPoolAsset = balanceRuneInPoolAsset
        self.synthSupplyRemaining = synthSupplyRemaining
        self.status = status
        self.block = block
    


class PoolMaya:
    def __init__(self,balanceAssetInPool, balanceCacaoInPoolAsset, synthSupplyRemaining, status, block):
        self.balanceAssetInPool = balanceAssetInPool
        self.balanceCacaoInPoolAsset = balanceCacaoInPoolAsset
        self.synthSupplyRemaining = synthSupplyRemaining
        self.status = status
        self.block = block
        