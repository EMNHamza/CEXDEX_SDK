class SinglePoolModification:
    def __init__(self, assetName: str, amount: int, isSynth: bool, isNativeAsset: bool):
        self.assetName = assetName
        self.amount = amount
        self.isSynth = isSynth
        self.isNativeAsset = isNativeAsset

    def __str__(self):
        return f"SinglePoolModification(assetName='{self.assetName}', amount={self.amount}, isSynth={self.isSynth}, isNativeAsset={self.isNativeAsset})"



class SwapModification:
    def __init__(self, poolName: str, swapAssetIn: SinglePoolModification, swapAssetOut: SinglePoolModification):
        self.poolName = poolName
        self.swapAssetIn = swapAssetIn
        self.swapAssetOut = swapAssetOut


    def __str__(self):
        return f"SwapModification(poolName='{self.poolName}', swapAssetIn={self.swapAssetIn}, swapAssetOut={self.swapAssetOut})"
    


class BlockPoolModifications:
    def __init__(self, block: int, swapModificationList: list[SwapModification]):
        self.block = block
        self.swapModificationList = swapModificationList

    def __str__(self):
        return f"PoolModifications(block={self.block}, swapModificationList={self.swapModificationList})"




