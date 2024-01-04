class Message:
    def __init__(
        self,
        assetIn,
        assetOut,
        amountIn,
        amountOut,
        dictTxHash,
        typeMsg,
        synthIn,
        synthOut,
        finalisedBlock=1,
    ):
        self.assetIn = assetIn
        self.assetOut = assetOut
        self.amountIn = amountIn
        self.amountOut = amountOut
        self.dictTxHash = dictTxHash
        self.typeMsg = typeMsg
        self.synthIn = synthIn
        self.synthOut = synthOut
        self.finalisedBlock = finalisedBlock
