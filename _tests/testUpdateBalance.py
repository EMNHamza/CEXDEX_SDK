from classes.Opportunity import OpportunityBybit, OpportunityCexDex, OpportunityDexDex, OpportunityMaya, OpportunityThorchain
from multiprocessing import Process, Queue, Manager, Event, Lock
from classes.Asset import AssetThorchain, AssetBybit, AssetMaya
from tools.myUtils import createAssetsFromJSON
from classes.Pair import PairCexDex, PairCex, PairDex, PairDexDex
from tools.myUtils import updateBalanceDictWithDoubleOpp, updateBalanceDictWithSingleOpp

listAssetsThorchain = createAssetsFromJSON(AssetThorchain)
listAssetsBybit = createAssetsFromJSON(AssetBybit)
listAssetsMaya = createAssetsFromJSON(AssetMaya)


myBalanceDict = {'THORCHAIN': {'bnb/eth-1c9': 5669121.0, 'btc/btc': 37141.0, 'eth/dai-0x6b175474e89094c44da98b954eedeac495271d0f': 520896353.0, 'eth/eth': 76632341.0, 'eth/usdc-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 11327221556.0, 'eth/usdt-0xdac17f958d2ee523a2206206994597c13d831ec7': 209988541609.0, 'eth/wbtc-0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 12837.0, 'rune': 50988553626.0, 'bnb/btcb-1de': 0.0}, 'Bybit': {'CORE': '0', 'MATIC': '0', 'APT': '0', 'STG': '0', 'SHIB': '0', 'USDT': '4.4343', 'DOGE': '0', 'HBAR': '0', 'NEAR': '0', 'FLOW': '0', 'WLD': '0', 'PEPE': '0', 'COMP': '0', 'WAVES': '0', 'MEME': '0', 'CHZ': '0', 'SLP': '0', 'XRP': '0', 'HFT': '0', 'PYTH': '0', 'JASMY': '0', 'TRX': '0', 'ZRX': '0', 'SAND': '0', 'BCH': '0', 'SUI': '0', 'DOT': '0', 'METH': '0', 'GMT': '0', 'BTC': '0.000008', 'TWT': '0', 'ARB': '0', 'AR': '0', 'AVAX': '0', 'IMX': '0', 'TUSD': '0', 'SEI': '0', 'USDD': '0', 'USDC': '5735.713675', 'LTC': '0', 'EGLD': '0', 'FTM': '0', 'THETA': '0', 'STETH': '0', 'INJ': '0', 'CRV': '0', 'GRT': '0', 'DYDX': '0', 'AGIX': '0', 'SUSHI': '0', 'ENS': '0', 'ALGO': '0', 'ARKM': '0', 'ATOM': '0', 'MASK': '0', 'UNI': '0', 'AAVE': '0', 'MNT': '0', 'MAGIC': '0', 'LDO': '0', 'QNT': '0', 'XLM': '0', 'LINK': '0', 'LUNC': '0', 'YFI': '0', 'CYBER': '0', 'OP': '0', 'MANA': '0', 'EOS': '0', 'FIL': '0', 'RNDR': '0', 'BICO': '0', 'DAI': '0', 'TIA': '0', 'GALA': '0', 'SOL': '0', 'ETC': '0', 'BAT': '0', 'APE': '0', 'ICP': '0', 'BNB': '0', 'ETH': '2.65494', 'BLUR': '0', 'BUSD': '0', 'AXS': '0', 'ZIL': '0', 'ADA': '0'}, 'MAYA': {'btc/btc': 14935669.0, 'cacao': 1670505706344.0, 'eth/eth': 704482.0, 'eth/usdc-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 1450790270.0, 'eth/usdt-0xdac17f958d2ee523a2206206994597c13d831ec7': 439260910237.0, 'thor/rune': 28414985799.0}}

manager=Manager()
lock = Lock()
balanceDictSd = manager.dict()
balanceDictSd.update(myBalanceDict)

# print(f'balanceDictShared {balanceDictSd}')

for asset in listAssetsThorchain:
    if asset.balanceName == 'eth/usdc-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':
        assetTHORUSDC = asset
    if asset.balanceName == 'eth/usdt-0xdac17f958d2ee523a2206206994597c13d831ec7':
        assetTHORUSDT = asset
    if asset.balanceName == 'rune':
        assetTHORRUNE = asset
    if asset.balanceName == 'eth/eth':
        assetTHORETH = asset
    if asset.balanceName == 'eth/wbtc-0x2260fac5e5542a773aa44fbcfedf7c193bc2c599':
        assetTHORWBTC = asset



for asset in listAssetsBybit:
    if asset.balanceName == 'USDC':
        assetBYBITUSDC = asset
    if asset.balanceName == 'ETH':
        assetBYBITETH = asset
    if asset.balanceName == 'BTC':
        assetBYBITBTC = asset


for asset in listAssetsMaya:
    if asset.balanceName == 'eth/usdc-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':
        assetMAYAUSDC = asset
    if asset.balanceName == 'eth/usdt-0xdac17f958d2ee523a2206206994597c13d831ec7':
        assetMAYAUSDT = asset
    if asset.balanceName == 'thor/rune':
        assetMAYARUNE = asset
    if asset.balanceName == 'btc/btc':
        assetMAYABTC = asset
    if asset.balanceName == 'eth/eth':
        assetMAYAETH = asset
    if asset.balanceName == 'cacao':
        assetMAYACACAO = asset
        

pair1 = PairDex(assetIn=assetTHORETH, assetOut=assetTHORUSDC, type='THORCHAIN')
pair2 = PairCex(assetIn=assetBYBITETH, assetOut=assetBYBITUSDC, type='Bybit', orderbookSymbol='', orderbook='')
pair3 = PairDex(assetIn=assetMAYAUSDT, assetOut=assetMAYAETH, type='MAYA')

oppThor = OpportunityThorchain(pairAsset=pair1,amountIn=0.1*1e8,amountInInDollars=100,amountOutEstimated=101*1e8,amountOutReal=101*1e8,typeOpp='THORCHAIN',txHash='',gainNetInAsset=0,gainNetInDollars=0, gainTotalEstimated=0, gainTotalReal=0)
oppBybit = OpportunityBybit(pairAsset=pair2,amountInEstimated=0.1,amountInReal=0.1,amountOutEstimated=101,amountOutReal=101,typeOpp='Bybit',bybitAssetPrice=2000,orderId='')
oppMaya = OpportunityMaya(pairAsset=pair3,amountIn=100*1e8,amountInInDollars=100,amountOutEstimated=0.1*1e8,amountOutReal=99*1e8,typeOpp='MAYA',txHash='',gainNetInAsset=0,gainNetInDollars=0, gainTotalEstimated=0, gainTotalReal=0)

print('')
print('INIT : ')
for platform, assets in balanceDictSd.items():
    if platform == oppThor.typeOpp:
        for asset, value in assets.items():
            if asset == assetTHORETH.balanceName:
                print(f'{asset} : {balanceDictSd[platform][asset] / 1e8}')
            if asset == assetTHORUSDC.balanceName:
                print(f'{asset} : {balanceDictSd[platform][asset] / 1e8}')
            if asset == assetTHORRUNE.balanceName:
                print(f'{asset} : {balanceDictSd[platform][asset]/ 1e8}')

    # if platform == oppBybit.typeOpp:
    #     for asset, value in assets.items():
    #         if asset == assetBYBITETH.balanceName:
    #             print(f'{asset} : {float(balanceDictSd[platform][asset])}')
    #         if asset == assetBYBITUSDC.balanceName:
    #             print(f'{asset} : {float(balanceDictSd[platform][asset])}')

    if platform == oppMaya.typeOpp:
        for asset, value in assets.items():
            if asset == assetMAYAUSDT.balanceName:
                print(f'{asset} : {float(balanceDictSd[platform][asset])/ 1e8}')
            if asset == assetMAYAETH.balanceName:
                print(f'{asset} : {float(balanceDictSd[platform][asset])/ 1e8}')
            if asset == assetMAYACACAO.balanceName:
                print(f'{asset} : {float(balanceDictSd[platform][asset])/ 1e10}')


print('')
# updateBalanceDictWithSingleOpp(opportunity=oppMaya,balanceDict=balanceDictSd, isOppSuccess=True, isEstimated=True, lock=lock)
updateBalanceDictWithDoubleOpp(opportunity1=oppMaya,opportunity2=oppThor, balanceDict=balanceDictSd, isOppSuccess=True, isEstimated=True, lock=lock)


print('BEFORE OPP : ')
for platform, assets in balanceDictSd.items():
    if platform == oppThor.typeOpp:
        for asset, value in assets.items():
            if asset == assetTHORETH.balanceName:
                print(f'{asset} : {balanceDictSd[platform][asset] / 1e8}')
            if asset == assetTHORUSDC.balanceName:
                print(f'{asset} : {balanceDictSd[platform][asset] / 1e8}')
            if asset == assetTHORRUNE.balanceName:
                print(f'{asset} : {balanceDictSd[platform][asset]/ 1e8}')

    # if platform == oppBybit.typeOpp:
    #     for asset, value in assets.items():
    #         if asset == assetBYBITETH.balanceName:
    #             print(f'{asset} : {float(balanceDictSd[platform][asset])}')
    #         if asset == assetBYBITUSDC.balanceName:
    #             print(f'{asset} : {float(balanceDictSd[platform][asset])}')

    if platform == oppMaya.typeOpp:
        for asset, value in assets.items():
            if asset == assetMAYAUSDT.balanceName:
                print(f'{asset} : {float(balanceDictSd[platform][asset])/ 1e8}')
            if asset == assetMAYAETH.balanceName:
                print(f'{asset} : {float(balanceDictSd[platform][asset])/ 1e8}')
            if asset == assetMAYACACAO.balanceName:
                print(f'{asset} : {float(balanceDictSd[platform][asset])/ 1e10}')

# updateBalanceDictWithSingleOpp(opportunity=oppMaya,balanceDict=balanceDictSd, isOppSuccess=True, isEstimated=False, lock=lock)
updateBalanceDictWithDoubleOpp(opportunity1=oppMaya,opportunity2=oppThor, balanceDict=balanceDictSd, isOppSuccess=False, isEstimated=False, lock=lock)

print('')
print('OPP : ')
for platform, assets in balanceDictSd.items():
    if platform == oppThor.typeOpp:
        for asset, value in assets.items():
            if asset == assetTHORETH.balanceName:
                print(f'{asset} : {balanceDictSd[platform][asset] / 1e8}')
            if asset == assetTHORUSDC.balanceName:
                print(f'{asset} : {balanceDictSd[platform][asset] / 1e8}')
            if asset == assetTHORRUNE.balanceName:
                print(f'{asset} : {balanceDictSd[platform][asset]/ 1e8}')

    # if platform == oppBybit.typeOpp:
    #     for asset, value in assets.items():
    #         if asset == assetBYBITETH.balanceName:
    #             print(f'{asset} : {float(balanceDictSd[platform][asset])}')
    #         if asset == assetBYBITUSDC.balanceName:
    #             print(f'{asset} : {float(balanceDictSd[platform][asset])}')

    if platform == oppMaya.typeOpp:
        for asset, value in assets.items():
            if asset == assetMAYAUSDT.balanceName:
                print(f'{asset} : {float(balanceDictSd[platform][asset])/ 1e8}')
            if asset == assetMAYAETH.balanceName:
                print(f'{asset} : {float(balanceDictSd[platform][asset])/ 1e8}')
            if asset == assetMAYACACAO.balanceName:
                print(f'{asset} : {float(balanceDictSd[platform][asset])/ 1e10}')


print('')