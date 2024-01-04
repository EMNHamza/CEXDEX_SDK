from utilsThorchain.thorchainInteraction import getThorchainPool, getBlock
from utilsMaya.mayaInteraction import getMayaBlock, getMayaPool

from classes.Asset import AssetThorchain, AssetMaya
from classes.Pool import Pool, PoolMaya
from tools.myUtils import createAssetsFromJSON

from constantes.constantes import MAX_SYNTH_PER_POOL_DEPTH_MAYA

import time 

from multiprocessing import Process, Manager

from tools.init import initBalance



def updateAssetPoolData(balances, poolData):
    for assetMaya in balances.balancesMaya.listAssets:
        for poolAsset, values in poolData['MAYA'].items():
            if assetMaya.poolName == poolAsset:

                newPool = PoolMaya(
                    balanceAssetInPool=int(values.get("balanceAssetInPool")),
                    balanceCacaoInPoolAsset=int(values.get("balanceCacaoInPool")),
                    synthSupplyRemaining=int(values.get("synthSupplyRemaining")),
                    status=values.get("status"),
                    block=values.get("block")
                )

                assetMaya.pool = newPool

    for assetThorchain in balances.balancesThorchain.listAssets:
        for poolAsset, values in poolData['THORCHAIN'].items():
            if assetThorchain.poolName == poolAsset:

                newPool = Pool(
                    balanceAssetInPool=int(values.get("balanceAssetInPool")),
                    balanceRuneInPoolAsset=int(values.get("balanceRuneInPool")),
                    synthSupplyRemaining=int(values.get("synthSupplyRemaining")),
                    status=values.get("status"),
                    block=values.get("block")
                )

                assetThorchain.pool = newPool


def update_pool_data(pool_data, pool_type, pool_asset, updates):
    
    if pool_type not in pool_data:
        pool_data[pool_type] = {}

    if pool_asset not in pool_data[pool_type]:
        pool_data[pool_type][pool_asset] = {}

    pool_data[pool_type][pool_asset].update(updates)



def fetchPoolData(poolDataShared, block, pool, listAssets):
    
    poolData = {}

    for singlePool in pool:
        for asset in listAssets:
            if singlePool['asset'] == asset.poolName: 
                updates = {
                    'balanceAssetInPool': singlePool['balance_asset'],
                    'status': singlePool['status'],
                    'block': block 
                }
                
                if isinstance(asset,AssetThorchain):
                    updates['balanceRuneInPool'] = singlePool['balance_rune']
                    updates['synthSupplyRemaining'] = singlePool['synth_supply_remaining']
                    updates['synthMintPaused'] = singlePool['synth_mint_paused']
                    poolType = 'THORCHAIN'
                if isinstance(asset,AssetMaya):
                    updates['balanceCacaoInPool'] = singlePool['balance_cacao']
                    synthSupplyRemaining = int((MAX_SYNTH_PER_POOL_DEPTH_MAYA * (int(singlePool.get("balance_asset")) * 2) ) - int(singlePool.get("synth_supply")))
                    updates['synthSupplyRemaining'] = synthSupplyRemaining
                    poolType = 'MAYA'

                update_pool_data(poolData, poolType, asset.poolName, updates)
    
    poolDataShared.update(poolData)


blockThorchain = getBlock()
poolsThorchain = getThorchainPool()
blockMaya = getMayaBlock()
poolsMaya = getMayaPool()

manager = Manager()

balances = initBalance()

poolDataShared = manager.dict()
fetchPoolData(poolDataShared,block=blockThorchain,pool=poolsThorchain,listAssets=balances.balancesThorchain.listAssets)
fetchPoolData(poolDataShared,block=blockMaya,pool=poolsMaya,listAssets=balances.balancesMaya.listAssets)

print(poolDataShared)
# for asset in balances.balancesMaya.listAssets:
#     if asset.assetType != 'CACAO':
#         print(f'AVANT - asset {asset.symbol} balanceAssetInPool {asset.pool.balanceAssetInPool}, balanceRuneInPool {asset.pool.balanceRuneInPool}')

# for pool_type, pools in poolDataShared.items():
#     print(f"Pool Type: {pool_type}")
#     for pool_asset, pool_info in pools.items():
#         print(f"\tPool Asset: {pool_asset}")
#         for key, value in pool_info.items():
#             print(f"\t\t{key}: {value}")


updateAssetPoolData(balances=balances, poolData=poolDataShared)


for asset in balances.balancesThorchain.listAssets:
    if asset.assetType != 'RUNE':
        print(f'APRES - asset {asset.symbol} balanceAssetInPool {asset.pool.balanceAssetInPool}, balanceRuneInPoolAsset {asset.pool.balanceRuneInPoolAsset}')








# def updatePoolDataShared(poolDataShared):
    
#     poolTest = {}

#     blockThorchain = getBlock()
#     poolsThorchain = getThorchainPool()
#     blockMaya = getMayaBlock()
#     poolsMaya = getMayaPool()

#     listAssetsThorchain = createAssetsFromJSON(AssetThorchain)
#     listAssetsMaya = createAssetsFromJSON(AssetMaya)
    

#     for singlePool in poolsThorchain:
#         asset:AssetThorchain
#         for asset in listAssetsThorchain:
#             if singlePool['asset'] == asset.poolName: 
#                 updates = {
#                     'balanceAssetInPool': singlePool['balance_asset'],
#                     'balanceRuneInPool': singlePool['balance_rune'],
#                     'status': singlePool['status'],
#                     'synthSupplyRemaining': singlePool['synth_supply_remaining'],
#                     'synthMintPaused': singlePool['synth_mint_paused'],
#                     'block': blockThorchain 
#                 }

#                 update_pool_data(poolTest, 'THORCHAIN', asset.poolName, updates)


#     for singlePool in poolsMaya:
#         asset:AssetMaya
#         for asset in listAssetsMaya:
#             if singlePool['asset'] == asset.poolName:
#                 synthSupplyRemaining = int((MAX_SYNTH_PER_POOL_DEPTH_MAYA * (int(singlePool.get("balance_asset")) * 2) ) - int(singlePool.get("synth_supply")))
#                 updates = {
#                     'balanceAssetInPool': singlePool['balance_asset'],
#                     'balanceCacaoInPool': singlePool['balance_cacao'],
#                     'status': singlePool['status'],
#                     'synthSupplyRemaining': synthSupplyRemaining,
#                     'block': blockMaya 
#                 }

#                 # poolDataShared['MAYA'][asset.poolName].update(updates)

#                 update_pool_data(poolTest, 'MAYA', asset.poolName, updates)
    
#     poolDataShared.update(poolTest)














# def process1(dictShared):
#     while True:
#         print('')
#         print("Process 1 Reading")
#         for platform in dictShared:
#             if platform == 'MAYA':
#                 print(f'Process 1 platform : {platform} - dictShared[platform] {dictShared[platform]}')
#         print('')
#         time.sleep(5)
        
# def process2(dictShared):
#     compteur = 0
#     while True:
#         compteur += 1
#         if compteur >= 2:
#             print('')
#             print("Process 2 Updating")
#             for platform in dictShared:
#                 if platform == 'MAYA':
#                     print(f'Process 2 platform : {platform} - dictShared[platform] {dictShared[platform]}')
#                     for assetPoolName in dictShared[platform]:
#                         updates = {
#                             'balanceAssetInPool': 0,
#                             'balanceCacaoInPool': 0,
#                             'status': 0,
#                             'synthSupplyRemaining': 0,
#                             'block': 0 
#                         }
#                         update_pool_data(poolDataShared, 'MAYA', assetPoolName, updates)

#                     print(f"Updated balances in process 2 - platform : {platform} - dictShared[platform] {dictShared[platform]}")
#             print('')
#             if compteur >= 10:

#                 process3_ = Process(target=process3, args=(dictShared,))
#                 # process3__ = Process(target=process3, args=(balances,))
#                 process3_.start()
#                 # process3__.start()

#         time.sleep(1)

# def process3(dictShared):
#     print('')
#     print("Process 3 Updating Aswell")
#     for platform in dictShared:
#         if platform == 'MAYA':
#             print(f'Process 3 platform : {platform} - dictShared[platform] {dictShared[platform]}')
#             for assetPoolName in dictShared[platform]:
#                 updates = {
#                     'balanceAssetInPool': 10,
#                     'balanceCacaoInPool': 10,
#                     'status': 10,
#                     'synthSupplyRemaining': 10,
#                     'block': 10 
#                 }
#                 update_pool_data(poolDataShared, 'MAYA', assetPoolName, updates)
#             print(f"Updated balances in process 3 - platform : {platform} - dictShared[platform] {dictShared[platform]}")
#     print('')


# def initPoolDataShared(poolDataShared):
#     dictInit = {"THORCHAIN" : [], 'MAYA':[]}
#     poolDataShared.update(dictInit)


# if __name__ == "__main__":
#     manager = Manager()
    
#     poolDataShared = manager.dict()
#     initPoolDataShared(poolDataShared=poolDataShared)

#     print(f'INIT - poolDataShared {poolDataShared}')
#     process1_ = Process(target=process1, args=(poolDataShared, ))
#     process2_ = Process(target=process2, args=(poolDataShared, ))

#     process1_.start()
#     process2_.start()

#     process1_.join()
#     process2_.join()


# # import time
# # from multiprocessing import Process, Manager, Lock
# # from copy import deepcopy

# # def initBalanceBuffer():
# #     return {
# #         'THORCHAIN': {'asset1': 0, 'asset2': 0},
# #         'Bybit': {'asset1': 0, 'asset2': 0},
# #         'MAYA': {'asset1': 0, 'asset2': 0}
# #     }

# # def process1(balancesBuffer):
# #     while True:
# #         print("Process 1 Reading")
# #         for platform, assets in balancesBuffer.items():
# #             for asset, value in assets.items():
# #                 print(f"process1 - balanceBuffer - {platform} - {asset}: {value}")
# #         time.sleep(5)  # Increased to 5 seconds

# # def process2(balancesBuffer):
# #     compteur = 0
# #     while True:
# #         compteur += 1
# #         if compteur >= 2:
# #             print("Process 2 Updating")
# #             # Create a deep copy for updates
# #             new_balances = deepcopy(dict(balancesBuffer))
# #             for platform, assets in new_balances.items():
# #                 for asset in assets.keys():
# #                     new_balances[platform][asset] += 10

# #             # Reassign the updated dictionary back to the Manager
# #             for platform in new_balances:
# #                 balancesBuffer[platform] = new_balances[platform]
# #             compteur = 0
# #             print(f"Updated balancesBuffer in process 2: {balancesBuffer}")
            
# #             process3_ = Process(target=process3, args=(balanceBuffer,))
# #             process3__ = Process(target=process3, args=(balanceBuffer,))
# #             process3_.start()
# #             process3__.start()
# #         time.sleep(1)


# # def process3(balancesBuffer):

# #     print("Process 3 Updating Aswell")
# #     # Create a deep copy for updates
# #     new_balances = deepcopy(dict(balancesBuffer))
# #     for platform, assets in new_balances.items():
# #         for asset in assets.keys():
# #             new_balances[platform][asset] += 1000

# #     # Reassign the updated dictionary back to the Manager
# #     for platform in new_balances:
# #         balancesBuffer[platform] = new_balances[platform]

# #     print(f"Updated balancesBuffer in process 3: {balancesBuffer}")


# # if __name__ == "__main__":
# #     manager = Manager()
# #     balanceBuffer = manager.dict(initBalanceBuffer())

# #     process1_ = Process(target=process1, args=(balanceBuffer,))
# #     process2_ = Process(target=process2, args=(balanceBuffer,))

# #     process1_.start()
# #     process2_.start()

# #     process1_.join()
# #     process2_.join()




# # import time
# # from multiprocessing import Process, Manager, Lock
# # from classes.Balances import Balances, BalancesThorchain, BalancesBybit, BalancesMaya
# # from tools.init import initBalance

# # def initBalanceBuffer():
# #     return {
# #         'THORCHAIN': {'asset1': 0, 'asset2': 0},
# #         'Bybit': {'asset1': 0, 'asset2': 0},
# #         'MAYA': {'asset1': 0, 'asset2': 0}
# #     }

# # def process1(balances):
# #     while True:
# #         print("Process 1 Reading")
# #         for platform in balances:
# #             if isinstance(platform,BalancesThorchain):
# #                 for asset in platform:
# #                     print(f"process1 - balances - {asset.symbol}: {asset.balance}")
# #         time.sleep(5)

# # def process2(balances):
# #     compteur = 0
# #     while True:
# #         compteur += 1
# #         if compteur >= 2:
# #             print("Process 2 Updating")
# #             for platform in balances:
# #                 if isinstance(platform,BalancesThorchain):
# #                     for asset in platform:
# #                         asset.balance += 100
# #                         print(f"Updated balances in process 2 - {asset.symbol}: {asset.balance}")

# #             compteur = 0

# #             process3_ = Process(target=process3, args=(balances,))
# #             # process3__ = Process(target=process3, args=(balances,))
# #             process3_.start()
# #             # process3__.start()

# #         time.sleep(1)

# # def process3(balances):
# #     print("Process 3 Updating Aswell")

# #     for platform in balances:
# #         if isinstance(platform,BalancesThorchain):
# #             for asset in platform:
# #                 asset.balance += 5000
# #                 print(f"Updated balances in process 3 - {asset.symbol}: {asset.balance}")


# # if __name__ == "__main__":
    
# #     balancesT:BalancesThorchain = BalancesThorchain(listAssets=[])
# #     balancesM:BalancesMaya = BalancesMaya(listAssets=[])
# #     balancesB:BalancesBybit = BalancesBybit(listAssets=[])

# #     with Manager() as manager:

# #         manager.register('Balances', Balances)

# #         balances = manager.Balances(balancesT,balancesB,balancesM)


#     # balances = initBalance()
    
#     # for platform in balances:
#     #     if isinstance(platform,BalancesThorchain):
#     #         for asset in platform:
#     #             asset.balance = asset.balance / 1e8

#     #         print(f"Process2 - balances - 'thorchain' - {asset.symbol}: {asset.balance}")

#     # process1_ = Process(target=process1, args=(balances, ))
#     # process2_ = Process(target=process2, args=(balances, ))

#     # process1_.start()
#     # process2_.start()

#     # process1_.join()
#     # process2_.join()
