from utilsMaya.mayaCalcul import getValueInDollarsMaya, getValueOfCacaoInAsset, getValueOfAssetInCacao
from utilsMaya.mayaInteraction import getMayaPool


poolsMaya = getMayaPool()

for pool in poolsMaya:
    if pool['asset'] == 'KUJI.KUJI':
        balance_asset = int(pool['balance_asset']) * 1e2
        balance_cacao = int(pool['balance_cacao'])



def getValueOfAssetInCacao(amount, balance_asset, balance_cacao):
    R = 0
    A = 1

    # pool = asset.pool
    R = float(balance_cacao) 
    A = float(balance_asset) 

    return (float(amount) * R) / A


def getValueOfCacaoInAsset(amount: float, balance_asset, balance_cacao) -> float:
    R = 1
    A = 0

    R = float(balance_cacao) 
    A = float(balance_asset) 

    return (amount * A) / R





# Example usage
new_price_cacao = 7.26  # Example new price of cacao

amount_to_add = calculate_amount_to_add(new_price_cacao, balance_asset, balance_cacao)

print(f"Amount to add: {amount_to_add/1e10}")