class Tx:
    def __init__(
        self,
        assetIn,
        assetOut,
        amountIn,
        amountOut,
        memo,
        txHash,
        timeReceived,
        isSend,
        signers,
    ):
        self.assetIn = assetIn
        self.assetOut = assetOut
        self.amountIn = amountIn
        self.amountOut = amountOut
        self.memo = memo
        self.txHash = txHash
        self.signers = signers
        self.isSend = isSend
        self.timeReceived = timeReceived
