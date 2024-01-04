from classes.Pool import PoolMaya
from constantes.constantes import MAX_SYNTH_PER_POOL_DEPTH_MAYA

def updateMayaAssetPoolData(balances,poolData,currentBlock):
    for pool in poolData:
        # Extract necessary data from the poolData item
        assetName = pool["asset"]
        # Other attributes like balanceAssetInPool, balanceRuneInPoolAsset, etc.

        # Find the corresponding AssetThorchain object in BalancesThorchain
        for assetMaya in balances.balancesMaya.listAssets:
            if assetMaya.poolName == assetName:
                # Create a new Pool object with data from poolData

                synthSupplyRemaining = (MAX_SYNTH_PER_POOL_DEPTH_MAYA * (int(pool.get("balance_asset")) * 2) ) - int(pool.get("synth_supply")) 
                
                newPool = PoolMaya(
                    balanceAssetInPool=int(pool.get("balance_asset")),
                    balanceCacaoInPoolAsset=int(pool.get("balance_cacao")),
                    synthSupplyRemaining=int(synthSupplyRemaining),
                    status=pool.get("status"),
                    block=currentBlock
                )
                # Update the Pool object in AssetThorchain
                assetMaya.pool = newPool



