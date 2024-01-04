from classes.Asset import AssetThorchain, AssetBybit, AssetMaya
from classes.Balances import Balances, BalancesThorchain, BalancesBybit, BalancesMaya
from tools.myUtils import createAssetsFromJSON, updateAssetBalances, updateRequestBalanceData
from datetime import datetime
from utilsThorchain.thorchainInteraction import getThorchainBalances
from utilsMaya.mayaInteraction import getMayaBalances

# from utilsMaya.mayaInteraction import getMayaBalances
from tools.utilsCsv import writeInCSV
from utilsBybit.bybit_utils import getBybitBalances


# def initNbNodes() -> int:
#     responseNodes = requests.get(URL_NODES_DATA).json()
#     compteur = 0

#     for response in responseNodes:
#         if response["status"] == "Active":
#             compteur += 1
#     return compteur


def initBalance():
    balancesDataThorchain = getThorchainBalances()
    balancesDataBybit = getBybitBalances()
    balancesDataMaya = getMayaBalances()

    listAssetsThorchain = createAssetsFromJSON(AssetThorchain)
    listAssetsBybit = createAssetsFromJSON(AssetBybit)
    listAssetsMaya = createAssetsFromJSON(AssetMaya)

    balancesThorchain = BalancesThorchain(
        listAssets=updateAssetBalances(listAssetsThorchain, balancesDataThorchain)
    )
    balancesBybit = BalancesBybit(
        listAssets=updateAssetBalances(listAssetsBybit, balancesDataBybit)
    )
    balancesMaya = BalancesMaya(listAssets=updateAssetBalances(listAssetsMaya,balancesDataMaya))

    balances = Balances(
        balancesThorchain=balancesThorchain,
        balancesBybit=balancesBybit,
        balancesMaya=balancesMaya,
    )

    return balances


def initBalanceBuffer():
    balancesDataThorchain = getThorchainBalances()
    balancesDataBybit = getBybitBalances()
    balancesDataMaya = getMayaBalances()

    balancesBuffer = {'THORCHAIN' : balancesDataThorchain, 'Bybit' : balancesDataBybit, 'MAYA' : balancesDataMaya}

    for platform in balancesBuffer:
        for asset in balancesBuffer[platform]:
            balancesBuffer[platform][asset] = '0'

    return balancesBuffer


def initBalanceDict():
    balancesDataThorchain = getThorchainBalances()
    balancesDataBybit = getBybitBalances()
    balancesDataMaya = getMayaBalances()

    listAssetsThorchain = createAssetsFromJSON(AssetThorchain)
    listAssetsBybit = createAssetsFromJSON(AssetBybit)
    listAssetsMaya = createAssetsFromJSON(AssetMaya)

    balancesDataThorchain = updateRequestBalanceData(listAssetsThorchain, balancesDataThorchain)
    balancesDataBybit = updateRequestBalanceData(listAssetsBybit, balancesDataBybit)
    balancesDataMaya = updateRequestBalanceData(listAssetsMaya, balancesDataMaya)

    balancesDict = {'THORCHAIN' : balancesDataThorchain, 'Bybit' : balancesDataBybit, 'MAYA' : balancesDataMaya}

    return balancesDict





def initBalanceNull():
    listAssetsThorchain = createAssetsFromJSON(AssetThorchain)
    listAssetsBybit = createAssetsFromJSON(AssetBybit)
    listAssetsMaya = createAssetsFromJSON(AssetMaya)

    balancesThorchain = BalancesThorchain(
        listAssets=updateAssetBalances(listAssetsThorchain, '')
    )
    balancesBybit = BalancesBybit(
        listAssets=updateAssetBalances(listAssetsBybit, '')
    )
    balancesMaya = BalancesMaya(listAssets=updateAssetBalances(listAssetsMaya, ''))

    balances = Balances(
        balancesThorchain=balancesThorchain,
        balancesBybit=balancesBybit,
        balancesMaya=balancesMaya,
    )

    return balances