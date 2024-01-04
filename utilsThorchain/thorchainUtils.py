from classes.Pool import Pool
from utilsThorchain.thorchainCalcul import getValueInDollarsThorchain
import logging


def updateThorchainAssetPoolData(balances, poolData, currentBlock):
    for pool in poolData:
        status = pool["status"]

        if status == "Available":
            # Extract necessary data from the poolData item
            assetName = pool["asset"]

            # Other attributes like balanceAssetInPool, balanceRuneInPoolAsset, etc.

            # Find the corresponding AssetThorchain object in BalancesThorchain
            for assetThorchain in balances.balancesThorchain.listAssets:
                if assetThorchain.poolName == assetName:
                    # Create a new Pool object with data from poolData
                    newPool = Pool(
                        balanceAssetInPool=int(pool.get("balance_asset")),
                        balanceRuneInPoolAsset=int(pool.get("balance_rune")),
                        synthSupplyRemaining=int(pool.get("synth_supply_remaining")),
                        status=pool.get("status"),
                        block=currentBlock,
                    )
                    assetThorchain.pool = newPool

    # for assetBTC in balances.balancesThorchain.listAssets:
    #     if assetBTC.poolName == "ETH.WBTC-0X2260FAC5E5542A773AA44FBCFEDF7C193BC2C599":
    #         priceWBTC = getValueInDollarsThorchain(
    #             amount=0.3 * 1e8,
    #             asset=assetBTC,
    #             balancesThorchain=balances.balancesThorchain,
    #         )
    #         logging.info(f"priceWBTC {round(priceWBTC/1e8,3)}")
    #     if assetBTC.poolName == "BNB.BTCB-1DE":
    #         priceBTCB = getValueInDollarsThorchain(
    #             amount=0.3 * 1e8,
    #             asset=assetBTC,
    #             balancesThorchain=balances.balancesThorchain,
    #         )
    #         logging.info(f"priceBTCB {round(priceBTCB/1e8,3)}")
    #     if assetBTC.poolName == "BTC.BTC":
    #         priceBTC = getValueInDollarsThorchain(
    #             amount=0.3 * 1e8,
    #             asset=assetBTC,
    #             balancesThorchain=balances.balancesThorchain,
    #         )
    #         logging.info(f"priceBTC {round(priceBTC/1e8,3)}")
    # Update the Pool object in AssetThorchain


def updateDexAssetPoolData(balancesDex, poolData, currentBlock):
    for pool in poolData:
        # Extract necessary data from the poolData item
        assetName = pool["asset"]
        # Other attributes like balanceAssetInPool, balanceRuneInPoolAsset, etc.

        # Find the corresponding AssetThorchain object in BalancesThorchain
        for assetDex in balancesDex.listAssets:
            if assetDex.poolName == assetName:
                # Create a new Pool object with data from poolData
                newPool = Pool(
                    asset=assetName,
                    balanceAssetInPool=int(pool.get("balance_asset")),
                    balanceRuneInPoolAsset=int(pool.get("balance_rune")),
                    synthSupplyRemaining=int(pool.get("synth_supply_remaining")),
                    status=pool.get("status"),
                    block=currentBlock,
                )
                # Update the Pool object in AssetThorchain
                assetDex.pool = newPool


def formattedBalancesData(balancesData):
    newDictFormatted = {}
    for result in balancesData:
        assetBalanceName = result["denom"]
        amount = result["amount"]
        newDictFormatted[assetBalanceName] = float(amount)
    return newDictFormatted