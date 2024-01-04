from classes.Asset import AssetBybit, AssetMaya, AssetThorchain
from typing import Dict, List

class Balances:
    def __init__(self, balancesThorchain, balancesBybit, balancesMaya):
        self.balancesThorchain = balancesThorchain
        self.balancesBybit = balancesBybit
        self.balancesMaya = balancesMaya

    def __getstate__(self):
        state = self.__dict__.copy()
        # remove or modify unserializable items
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        
class BalancesThorchain:
    def __init__(self, listAssets:List[AssetThorchain]):
        self.listAssets = listAssets


class BalancesBybit:
    def __init__(self, listAssets:List[AssetBybit]):
        self.listAssets = listAssets

class BalancesMaya:
    def __init__(self, listAssets:List[AssetMaya]):
        self.listAssets = listAssets
