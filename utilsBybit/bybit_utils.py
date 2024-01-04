from typing import Dict
import requests
import time
import hashlib
import hmac
import math
from utilsBybit.api_config_manager import load_config
from utilsBybit.bybit_price_calculation import orderbook_average_price
from classes.Opportunity import OpportunityThorchain, OpportunityBybit
from classes.Balances import Balances
from classes.Pair import PairCex,PairDex,PairCexDex
from classes.Asset import AssetBybit
import json
import logging

# from logging.handlers import RotatingFileHandler

config = load_config()
api_key = config.get("api_key")
secret_key = config.get("secret_key")

httpClient = requests.Session()
httpClientGetOrderDetail = requests.Session()
httpClientGetBalance = requests.Session()

recv_window = str(10000)
url = "https://api.bybit.com"

logger = logging.getLogger(__name__)


def HTTP_Request(endPoint, method, payload, Info, httpClient, max_attempts=10):
    httpClient = requests.Session()
    global time_stamp
    for attempt in range(max_attempts):
        time_stamp = str(int(time.time() * 10 ** 3))
        signature = genSignature(payload)
        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-TIMESTAMP': time_stamp,
            'X-BAPI-RECV-WINDOW': recv_window,
            'Content-Type': 'application/json'
        }

        try:
            if method == "POST":
                response = httpClient.request(method, url+endPoint, headers=headers, data=payload)
            else:
                response = httpClient.request(method, url+endPoint+"?"+payload, headers=headers)

            # Log the response. Be cautious as responses may contain sensitive information.
            logTest = Info + " Elapsed Time : " + str(response.elapsed)
            logging.info(f'Bybit {logTest}')

            # Check if the response status code is not 200
            if response.status_code != 200:
                logging.warning(f'Request failed with status code {response.status_code}. Retrying...')
                time.sleep(0.2)  # Attendez un peu avant de réessayer.
                continue  # Continue with the next iteration to retry

            return response.text  # Return the response text if status code is 200

        except Exception as e:
            logging.error(f'An error occurred: {e}')
            time.sleep(0.3)  # Attendez un peu avant de réessayer.

    return None  # Retournez None si toutes les tentatives échouent.


def genSignature(payload):
    param_str = str(time_stamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    return signature


def getBybitBalances():
    try:
        endpoint = "/v5/asset/transfer/query-account-coins-balance"
        method = "GET"
        params = 'accountType=UNIFIED'

        response_data = HTTP_Request(endpoint, method, params, "Get Balances", httpClientGetBalance)
        # logging.info("response_data")
        return extract_all_balances(response_data)
        # logging.info(extract_wallet_balances(response_data))

    except Exception as e:
        logging.info(f"Erreur lors de la récupération des soldes du portefeuille :{e}")
        return None


def extract_all_balances(data_json):
    try:
        # Charger la donnée JSON
        data = json.loads(data_json)

        # Initialiser un dictionnaire pour stocker les balances de tous les actifs
        all_balances = {}

        # Parcourir les soldes
        for balance_entry in data.get("result", {}).get("balance", []):
            coin = balance_entry.get("coin")
            wallet_balance = balance_entry.get("walletBalance")

            # Ajouter la balance de l'actif au dictionnaire
            all_balances[coin] = wallet_balance

        return all_balances

    except Exception as e:
        logging.info(f"Erreur lors de l'extraction des balances : {e}")
        return None


def place_order(pair_symbol, isSell, amount, httpClient):
    try:
        side = 'Sell' if isSell else 'Buy'
        endpoint = "/v5/order/create"
        method = "POST"
        params = f'{{"category":"spot","symbol":"{pair_symbol}","side":"{side}","orderType":"Market","qty":"{amount}"}}'
        response_data = HTTP_Request(endpoint, method, params, "Order", httpClient)
        logging.info(f'response_data {response_data}')
        parsed_data = json.loads(response_data)
        order_id = parsed_data["result"]["orderId"]
        logging.info(f'order Id {order_id}')
        return get_order_details(order_id, httpClientGetOrderDetail)
        # logging.info(extract_wallet_balances(response_data))

    except Exception as e:
        logging.info(f"Erreur lors du placement de l'ordre :{e}")
        return None


def get_order_details(order_id, httpClient):
    max_attempts = 20
    attempt = 0

    while attempt < max_attempts:
        try:
            time.sleep(2)
            endpoint = "/v5/order/history"
            method = "GET"
            params = f'category=spot&orderId={order_id}'

            response_data = HTTP_Request(endpoint, method, params, "Get Transaction Output", httpClient)
            amount_in, amount_out = extract_montants_order_reels(response_data)

            if amount_out is not None:
                logging.info(f"Amount In {amount_in}")
                logging.info(f"Amount Out {amount_out}")
                return amount_in, amount_out, order_id

            attempt += 1

        except Exception as e:
            logging.info(f'Erreur lors du get Output de la transaction {order_id}: {e}')

            if attempt == max_attempts - 1:
                return None
            attempt += 1

    logging.info("Nombre maximal de tentatives atteint sans obtenir de résultat.")
    return None


def extract_montants_order_reels(json_data):
    try:
        # Charger le JSON en tant que dictionnaire Python
        data = json.loads(json_data)

        # Accéder à la liste des éléments
        order_list = data["result"]["list"]

        if order_list:
            # Supposons qu'il y ait un seul élément dans la liste (comme dans votre exemple)
            order = order_list[0]

            # Extraire la valeur du champ "side"
            side = order.get("side")

            # Extraire les valeurs de cumExecValue et cumExecQty
            token1_amount = order.get("cumExecQty")
            token2_amount = order.get("cumExecValue")

            # Vérifier le côté (side) et inverser les montants si nécessaire
            if side == "Buy":
                return token2_amount, token1_amount
            elif side == "Sell":
                return token1_amount, token2_amount
            else:
                logging.info("Side inconnu :", side)
                return None, None
        else:
            logging.info("La liste de l'ordre est vide.")
            return None, None
    except Exception as e:
        logging.info("Erreur lors de l'extraction des valeurs :", e)
        return None, None


def getSymbolList(httpClient):
    try:
        endpoint = "/v5/market/tickers"
        method = "GET"
        params = 'category=spot'

        response_data = HTTP_Request(endpoint, method, params, "Tickers", httpClient)
        # logging.info("response_data")
        return extract_all_symbols(response_data)
        # logging.info(extract_wallet_balances(response_data))

    except Exception as e:
        logging.info(f"Erreur lors de la récupération de la symbol list :{e}")
        return None


def extract_all_symbols(api_response_json):
    try:
        # Convertir la réponse JSON en un dictionnaire Python
        response_data = json.loads(api_response_json)

        # Vérifier si la réponse contient la clé "result" et si elle contient la clé "list"
        if "result" in response_data and "list" in response_data["result"]:
            # Extraire la liste des symboles
            symbols = [entry["symbol"] for entry in response_data["result"]["list"]]
            # Trier les symboles par ordre alphabétique
            symbols.sort()
            return symbols
        else:
            # Si les clés ne sont pas présentes, renvoyer une liste vide
            return []

    except Exception as e:
        logging.info("Erreur lors de l'analyse de la réponse API :", e)
        return []

allSymbols=getSymbolList(httpClient)


def getSymbol(symbolIn, symbolOut):
    # Chercher les symboles associés aux paires de tokens
    symbol_in_first = f"{symbolIn}{symbolOut}"
    symbol_out_first = f"{symbolOut}{symbolIn}"

    # Vérifier si l'un des symboles existe dans la liste des symboles
    if symbol_in_first in allSymbols:
        return symbol_in_first
    elif symbol_out_first in allSymbols:
        return symbol_out_first
    else:
        logging.info(f'Pas de symbol trouvé pour les assets : {symbolIn}/{symbolOut}')
        return None  # Aucun symbole trouvé


def getOrderbookSymbolFromAssetPair(assetPair: PairDex):
    symbolIn = assetPair.assetIn.symbol
    symbolOut = assetPair.assetIn.symbol
    return getSymbol(symbolIn,symbolOut)


def isSell(symbolIn:str, symbolOut:str):
    symbolPair=getSymbol(symbolIn, symbolOut)
    # Créez le symbole attendu en fonction des tokens d'entrée
    expected_symbol = f"{symbolIn}{symbolOut}"
    # Comparez le symbole attendu avec le symbole donné
    return symbolPair == expected_symbol


def createBybitOpportunityForThorchain(opportunityThorchain: OpportunityThorchain, orderbookData: Dict, balances: Balances):
    # assetIn, assetOut, amountIn, amountOutEstimated, amountOutReal, gainNetInStableEstimated, gainNetInStableReal, typeOpp
    
    
    # amountInFloor = math.floor((opportunityThorchain.amountOutEstimated / 10**opportunityThorchain.pairAsset.assetOut.decimals)*10**5)/10**5
    
    # amountInThorchain = opportunityThorchain.amountIn / 10**opportunityThorchain.pairAsset.assetOut.decimals
    # amountInThorchainRounded = round(amountInThorchain,6)
    amountOutThorchain = opportunityThorchain.amountOutEstimated / 10**opportunityThorchain.pairAsset.assetOut.decimals
    
    # logging.info(f'amountInThorchainRounded {amountInThorchainRounded} - amountOutThorchain Rounded {amountInBybit}')
    # logging.info(f'AmountIn floor {amountInFloor} - amountOut Rounded {amountInBybit}')

    assetIn : AssetBybit = findMatchingBybitAsset(balances, opportunityThorchain.pairAsset.assetOut.assetType)
    assetOut : AssetBybit= findMatchingBybitAsset(balances, opportunityThorchain.pairAsset.assetIn.assetType)
    
    amountInBybit = math.floor(amountOutThorchain * 10**5) / 10**5
    
    if amountInBybit > assetIn.balance:
        amountInBybit = assetIn.balance

    pairSymbol = getSymbol(assetIn.symbol,assetOut.symbol)
    pairOrderbook = orderbookData[pairSymbol]
    pairCex = PairCex(assetIn=assetIn,assetOut=assetOut,orderbook=pairOrderbook,type="Bybit",orderbookSymbol=pairSymbol)
    
    isAssetSell = isSell(assetIn.symbol,assetOut.symbol)
    assetPrice = orderbook_average_price(pairOrderbook,amountInBybit, isAssetSell)
    # assetPriceisSellFalse = orderbook_average_price(pairOrderbook,amountIn, False)
    # assetPriceisSellTrue = orderbook_average_price(pairOrderbook,amountIn, True)

    # logging.info(f'createBybitOpportunityForThorchain - pairSymbol {pairSymbol} assetIn.symbol {assetIn.symbol} assetOut.symbol {assetOut.symbol} isAssetSell {isAssetSell} assetPrice {assetPrice} amountIn {amountInBybit}')
    
    if isAssetSell and assetPrice != 0:
        amountOutEstimated = amountInBybit*assetPrice
    else:
        if amountInBybit == 0 or assetPrice==0:
            amountOutEstimated=0
        else:
            amountOutEstimated = amountInBybit/assetPrice

    opportunityBybit = OpportunityBybit(pairCex, amountInEstimated=amountInBybit, bybitAssetPrice=assetPrice, amountInReal=0, amountOutEstimated=amountOutEstimated, amountOutReal=0, typeOpp="Bybit", orderId='')

    # logging.info(f'createBybitOpportunityForThorchain - isSell {isSell} assetIn {assetIn.symbol} amountIn {amountIn} assetOut {assetOut.symbol} amountOutEstimated {amountOutEstimated}')
    return opportunityBybit

def findMatchingBybitAsset(balances: Balances, asset_type: str) -> AssetBybit:
    for asset in balances.balancesBybit.listAssets:
        if asset.assetType == asset_type:
            return asset
    return None  # Retourne None si aucun asset correspondant n'est trouvé



def getOrderbookUSDCPairSymbols():
    # Ouvrir et lire le fichier JSON
    filename='constantes/myAssets/AssetBybit.json'
    with open(filename, 'r') as file:
        data = json.load(file)
    # Construire le tableau des symboles
    symbols = []
    for asset in data:
        if asset != "USDC":  # Exclure l'USDC
            symbols.append(data[asset]["symbol"] + "USDC")
    return symbols


# #Create Order
# endpoint="/v5/order/create"
# method="POST"
# orderLinkId=uuid.uuid4().hex
# params='{"category":"linear","symbol": "BTCUSDT","side": "Buy","positionIdx": 0,"orderType": "Limit","qty": "0.001","price": "10000","timeInForce": "GTC","orderLinkId": "' + orderLinkId + '"}'
# HTTP_Request(endpoint,method,params,"Create")

# Get unfilled Orders


# print(get_order_details('1547638430614422272', httpClient))
# print(get_order_details('1547638379360027392', httpClient))
# print(get_order_details('1547638276641522432', httpClient))
# print(get_order_details('1547647710017094400', httpClient))


# logging.info(get_transaction_output(1546711925587706624))

# print(getBybitBalances())

# #Cancel Order
# endpoint="/v5/order/cancel"
# method="POST"
# params='{"category":"linear","symbol": "BTCUSDT","orderLinkId": "'+orderLinkId+'"}'
# HTTP_Request(endpoint,method,params,"Cancel")
