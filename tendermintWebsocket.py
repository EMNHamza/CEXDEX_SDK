import websocket
import json
import threading
from collections import defaultdict
from classes.TendermintEvent import SwapModification, SinglePoolModification, BlockPoolModifications
from _processesTest import processGetMayaBlock
import requests
import time 
import re
import copy
import logging
import multiprocessing
from multiprocessing import Process, Queue, Manager, Event, Lock
from classes.Balances import Balances
from typing import Dict, List


logging.basicConfig(filename='/root/BOT_REFONTE/logs.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Test de Logging")

# "139.180.222.148"
ip_address = "45.32.176.178"
port = "27147"
URL_POOL_MAYA = f"http://{ip_address}:1317/mayachain/pools"
URL_BLOCK_MAYA = f"http://{ip_address}:27147/status"
URL_BLOCK_MAYA_NEW = f"http://{ip_address}:1317/mayachain/lastblock"


def getMayaBlockStatus():
    try:
        block = int(requests.get(url=URL_BLOCK_MAYA, timeout=3).json()["result"]["sync_info"]["latest_block_height"])
        return block
    except Exception as err:
        logging.error(f'getMayaBlockStatus - error getting data from {URL_BLOCK_MAYA}: {err}')
        return None

def getBlockPoolModifications(data):
    block = None
    swapModifications = []

    if 'block' in data['result']['data']['value'] and 'header' in data['result']['data']['value']['block']:
        block = data['result']['data']['value']['block']['header']['height']

    if 'events' in data['result']:
        swap_coin_events = data['result']['events'].get('swap.coin', [])
        swap_emit_events = data['result']['events'].get('swap.emit_asset', [])

        for swap_coin, swap_emit in zip(swap_coin_events, swap_emit_events):
            assetIn_name, assetIn_amount = parse_asset_string(swap_coin)
            assetOut_name, assetOut_amount = parse_asset_string(swap_emit)

            swapAssetIn = SinglePoolModification(assetIn_name, assetIn_amount, isSynth(assetIn_name), isCacao(assetIn_name))
            swapAssetOut = SinglePoolModification(assetOut_name, assetOut_amount, isSynth(assetOut_name), isCacao(assetOut_name))
            swapModification = SwapModification(getPoolName(swapAssetIn,swapAssetOut), swapAssetIn, swapAssetOut)
            swapModifications.append(swapModification)
            logging.info(swapModification)
    return BlockPoolModifications(block, swapModifications)

def getPoolName(swapAssetIn, swapAssetOut):
    if 'CACAO' not in swapAssetIn.assetName:
        return swapAssetIn.assetName.replace('/', '.')
    elif 'CACAO' not in swapAssetOut.assetName:
        return swapAssetOut.assetName.replace('/', '.')
    else:
        logging.error("Get Pool Name error")
        return None

def parse_asset_string(asset_string):
    parts = asset_string.split()
    if len(parts) == 2:
        amount, asset_name = parts
        try:
            amount = int(amount)
            return asset_name, amount
        except ValueError:
            logging.error(f"Invalid number format in asset: {asset_string}")
            return asset_name, 0
    else:
        logging.error(f"Invalid asset string format: {asset_string}")
        return "", 0

def isSynth(assetName):
    return '/' in assetName

def isCacao(assetName):
    # Implémentez la logique pour déterminer si l'actif est cacao.
    return 'CACAO' in assetName  # Exemple, remplacez par votre logique.

def getMayaBlockLastblock():
    try:
        data = requests.get(url=URL_BLOCK_MAYA_NEW, timeout=3).json()
        block = min([int(i["mayachain"]) for i in data])
        return block
    except Exception as err:
        logging.error(f'getMayaBlockLastblock - error getting data from {URL_BLOCK_MAYA_NEW}: {err}')
        return None

def getMayaPools():
    try:
        pools = requests.get(url=URL_POOL_MAYA, timeout=3).json()
        return pools
    except Exception as err:
        logging.error(f'getMayaPools - error getting data from {URL_POOL_MAYA}: {err}')
        return None

def updatePoolDataDoubleSwap(swapModifications : list[SwapModification], poolList):
    newPoolList = poolList
    for swapModification in swapModifications:
        # Trouver l'entrée correspondante dans le dictionnaire d'actifs
        asset_info = next((asset for asset in newPoolList if asset["asset"] == swapModification.poolName), None)
        
        if not asset_info:
            print(f"updatePoolData - Asset not found: {swapModification.poolName}")
            continue

        # Mise à jour de la balance en fonction de swapAssetIn
        if swapModification.swapAssetIn.isNativeAsset:
            asset_info["balance_cacao"] = str(int(asset_info["balance_cacao"]) + swapModification.swapAssetIn.amount)
        elif not swapModification.swapAssetIn.isSynth:
            asset_info["balance_asset"] = str(int(asset_info["balance_asset"]) + swapModification.swapAssetIn.amount)
        
        # Mise à jour de la balance en fonction de swapAssetOut
        if swapModification.swapAssetOut.isNativeAsset:
            asset_info["balance_cacao"] = str(int(asset_info["balance_cacao"]) - swapModification.swapAssetOut.amount)
        elif not swapModification.swapAssetOut.isSynth:
            asset_info["balance_asset"] = str(int(asset_info["balance_asset"]) - swapModification.swapAssetOut.amount)

    return newPoolList


def updatePoolDataWithFeesDeduction(poolModifications: list[SinglePoolModification], poolList: list):
    for modification in poolModifications:
        # Trouver l'entrée correspondante dans le dictionnaire de pools
        pool_info = next((pool for pool in poolList if pool["asset"] == modification.assetName), None)

        if not pool_info:
            print(f"updatePoolDataWithFeesDeduction - Pool not found: {modification.assetName}")
            continue

        # Mise à jour de la balance de la pool
        # Supposons que la balance est stockée en tant que chaîne de caractères
        pool_info["balance_cacao"] = str(int(pool_info["balance_cacao"]) - modification.amount)

    return poolList


def updatePoolDataWithPoolRewards(poolModifications: list[SinglePoolModification], poolList: list):
    for modification in poolModifications:
        # Trouver l'entrée correspondante dans le dictionnaire de pools
        pool_info = next((pool for pool in poolList if pool["asset"] == modification.assetName), None)

        if not pool_info:
            print(f"updatePoolDataWithPoolRewards - Pool not found: {modification.assetName}")
            continue

        # Mise à jour de la balance de la pool
        # Supposons que la balance est stockée en tant que chaîne de caractères
        pool_info["balance_cacao"] = str(int(pool_info["balance_cacao"]) + modification.amount)

    return poolList


def convert_list_to_dict(pools_list):
    return {pool["asset"]: pool for pool in pools_list}


def compare_pools(pools_list1, pools_list2):
    pool_dict1 = convert_list_to_dict(pools_list1)
    pool_dict2 = convert_list_to_dict(pools_list2)
    isDifferent = False
    for asset, asset_info in pool_dict1.items():
        if asset in pool_dict2:
            other_asset_info = pool_dict2[asset]

            # Comparer les balances
            if asset_info["balance_cacao"] != other_asset_info["balance_cacao"] or asset_info["balance_asset"] != other_asset_info["balance_asset"]:
                logging.info(f"Difference found in asset: {asset}")
                difference_cacao = int(asset_info["balance_cacao"]) - int(other_asset_info["balance_cacao"])
                difference_asset = int(asset_info["balance_asset"]) - int(other_asset_info["balance_asset"])
                logging.info(f"balance_cacao difference: {difference_cacao}")
                logging.info(f"balance_asset difference: {difference_asset}")
                isDifferent=True
        else:
            logging.info(f"Asset {asset} found in first pool but not in second pool.")

    return isDifferent


def getFeeDeduction(data):
    fee_coins = data['result']['events'].get('fee.coins', [])
    fee_pool_deduct = data['result']['events'].get('fee.pool_deduct', [])
    
    pool_modifications = []

    for index, fee_coin in enumerate(fee_coins):
        # Extraire le montant numérique au début de la chaîne
        amount_str = re.match(r'^\d+', fee_coin)
        amount_fee_coin = int(amount_str.group()) if amount_str else 0

        # Supprimer uniquement les chiffres au début du nom de la pool
        pool_name = re.sub(r'^\d+\s+', '', fee_coin)
        # Remplacer la barre oblique par un point si elle est présente
        isSynthBool = isSynth(pool_name)
        pool_name = pool_name.replace("/", ".")
        # Convertir le montant de la déduction en entier
        deduction_amount = int(fee_pool_deduct[index])


        # Ajouter une modification supplémentaire si le pool n'est pas MAYA.CACAO
        if pool_name != "MAYA.CACAO":
            modification_deduction = SinglePoolModification(pool_name, -deduction_amount, False, True)
            pool_modifications.append(modification_deduction)
            modification_fee_coin = SinglePoolModification(pool_name, amount_fee_coin, isSynthBool, False)
            pool_modifications.append(modification_fee_coin)

    return pool_modifications


def getPoolReward(data):
    pool_modifications = []
    
    # Parcourir tous les éléments dans les événements
    for key, value in data['result']['events'].items():
        if key.startswith("rewards.") and not key.startswith("rewards.bond_reward"):
            # Extraire le nom de la pool en supprimant "rewards."
            pool_name = key.replace("rewards.", "")
            pool_name = pool_name.replace("/", ".")
            # Supposer que la valeur est une liste et prendre le premier élément
            amount = int(value[0]) if value else 0
            # Créer une instance de SinglePoolModification
            modification = SinglePoolModification(pool_name, amount, False, True)
            pool_modifications.append(modification)

    return pool_modifications

def getGasPoolModifications(data):
    gas_assets = data['result']['events'].get('gas.asset', [])
    gas_cacao_amounts = data['result']['events'].get('gas.cacao_amt', [])
    gas_asset_amounts = data['result']['events'].get('gas.asset_amt', [])
    
    gas_pool_modifications = []

    for index, gas_asset in enumerate(gas_assets):
        gas_asset = gas_asset.replace("/", ".")
        # Créer une instance pour gas.cacao_amt
        if index < len(gas_cacao_amounts):
            cacao_amount = int(gas_cacao_amounts[index])
            modification_cacao = SinglePoolModification(gas_asset, cacao_amount, False, True)
            gas_pool_modifications.append(modification_cacao)

        # Créer une instance pour gas.asset_amt
        if index < len(gas_asset_amounts):
            asset_amount = int(gas_asset_amounts[index])
            modification_asset = SinglePoolModification(gas_asset, -asset_amount, False, False)
            gas_pool_modifications.append(modification_asset)

    return gas_pool_modifications

def getAddLiquidityModifications(data):
    pools = data['result']['events'].get('add_liquidity.pool', [])
    cacao_amounts = data['result']['events'].get('add_liquidity.cacao_amount', [])
    asset_amounts = data['result']['events'].get('add_liquidity.asset_amount', [])
    
    liquidity_modifications = []

    for index, pool in enumerate(pools):
        # Créer une instance pour cacao_amount
        pool = pool.replace("/", ".")
        
        if index < len(cacao_amounts):
            cacao_amount = int(cacao_amounts[index])
            modification_cacao = SinglePoolModification(pool, cacao_amount, False, True)
            liquidity_modifications.append(modification_cacao)

        # Créer une instance pour asset_amount
        if index < len(asset_amounts):
            asset_amount = int(asset_amounts[index])
            modification_asset = SinglePoolModification(pool, asset_amount, True, False)
            liquidity_modifications.append(modification_asset)

    return liquidity_modifications

def updatePoolDataWithSinglePoolModifications(poolModifications: list[SinglePoolModification], poolList: list):
    for modification in poolModifications:
        # Trouver l'entrée correspondante dans le dictionnaire de pools
        pool_info = next((pool for pool in poolList if pool["asset"] == modification.assetName), None)

        if not pool_info:
            print(f"updatePoolDataWithSinglePoolModifications - Pool not found: {modification.assetName}")
            continue

        # Mise à jour de la balance de la pool
        if modification.isNativeAsset:
            # Mise à jour de la balance en cacao
            pool_info["balance_cacao"] = str(int(pool_info["balance_cacao"]) + modification.amount)
        elif not modification.isSynth:
            # Mise à jour de la balance en actif
            pool_info["balance_asset"] = str(int(pool_info["balance_asset"]) + modification.amount)

    return poolList

def log_single_line(info_dict):
    # Convertit le dictionnaire en une chaîne de caractères où chaque paire clé/valeur est séparée par des virgules
    info_str = ', '.join(f"{key}: {value}" for key, value in info_dict.items())
    logging.info(f'info_str')

diffNumber=0

def updatePool(data, currentPool):
        poolModifications = getBlockPoolModifications(data)
        feeDeduction = getFeeDeduction(data)
        poolReward = getPoolReward(data)
        gasModification = getGasPoolModifications(data)
        addLiquidity = getAddLiquidityModifications(data)


        updatedPools = updatePoolDataDoubleSwap(poolModifications.swapModificationList, currentPool)
        updatedPools = updatePoolDataWithSinglePoolModifications(feeDeduction, updatedPools)
        updatedPools = updatePoolDataWithSinglePoolModifications(poolReward, updatedPools)
        updatedPools = updatePoolDataWithSinglePoolModifications(gasModification, updatedPools)
        updatedPools = updatePoolDataWithSinglePoolModifications(addLiquidity, updatedPools)

        return updatedPools

def getAllModification(data):
        feeDeduction = getFeeDeduction(data)
        poolReward = getPoolReward(data)
        gasModification = getGasPoolModifications(data)
        addLiquidity = getAddLiquidityModifications(data)
        allModifications = addLiquidity + gasModification + poolReward + feeDeduction
        return allModifications

def process_message(message):
    global diffNumber
    try:
        if 'data' not in message or 'result' not in message:
            logging.error("Message does not contain 'result' or 'data'")
            return
        
        currentPool = getMayaPools()
        copiedPool = copy.deepcopy(currentPool)

        data = json.loads(message)
        # logging.info(f"poolData : {data}")
        
        logging.info(f"Node block : {getMayaBlockLastblock()}")
        block = int(data['result']['data']['value']['block']['header']['height'])
        logging.info("BLOCK HEIGHT : {}".format(block))
        swap_coin_events = data['result']['events'].get('swap.coin', [])
        swap_emit_events = data['result']['events'].get('swap.emit_asset', [])
        logging.info("Received swap_coin_events: {}".format(swap_coin_events))
        logging.info("Received swap_emit_events: {}".format(swap_emit_events))

        if 'result' in data:
            
            updatedPools = updatePool(data, currentPool)
            allModifications = getAllModification(data)
            newPools = getMayaPools()    

            while newPools == copiedPool:
                time.sleep(0.2)
                newPools = getMayaPools()  
            
            logging.info(f"Node block for new pool : {getMayaBlockLastblock()} at block height {block}")

            modified_assets = set(mod.assetName for mod in allModifications)
            index = 0
            for pool in newPools:
                if pool["asset"] in modified_assets:
                    logging.info(f"Initial pool : {copiedPool[index]}")
                    logging.info(f"Updated pool : {updatedPools[index]}")
                    logging.info(f"New pool : {newPools[index]}")
                index += 1            

            isDifferent = compare_pools(newPools, updatedPools)
            currentPool = updatedPools

        else:
            logging.info("'result' not found in message")
        
        if isDifferent:
        #     logging.info(f"poolData : {message}")
            diffNumber = diffNumber+1
            logging.info(f"diffNumber = {diffNumber}")
        
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from message")


def on_message(ws, message):
        # Lancer un nouveau processus pour chaque message reçu
    process = multiprocessing.Process(target=process_message, args=(message,))
    process.start()

def printModifiedPoolInfo(poolModifications, poolList):
    modified_assets = set(mod.assetName for mod in poolModifications)
    index = 0
    for pool in poolList:
        if pool["asset"] in modified_assets:
            print(pool)
        index = index +1

def aggregate_assets(asset_list, IsAssetIn):
    # Créer un dictionnaire pour stocker les sommes des assets
    asset_sums = defaultdict(int)

    # Itérer sur chaque élément de la liste
    for asset in asset_list:
        # Séparer le nombre et le nom de l'asset
        parts = asset.split()
        if len(parts) == 2:
            number, asset_name = parts
            try:
                # Normaliser le nom de l'asset pour avoir le format "chaine.asset"
                normalized_asset_name = asset_name.replace('/', '.')
                # Ajouter le nombre à la somme de l'asset correspondant
                asset_sums[normalized_asset_name] += int(number)
            except ValueError:
                print(f"Invalid number format in asset: {asset}")

    # Convertir les résultats en objets SinglePoolModification
    pool_modifications = []
    for asset, total in asset_sums.items():
        amount = total if IsAssetIn else -total
        pool_modifications.append(SinglePoolModification(asset, amount))

    return pool_modifications

def on_error(ws, error):
    logging.error("Error: {}".format(error))
    reconnect()

def on_close(ws, close_status_code, close_msg):
    logging.info("### WebSocket Closed ###")

def reconnect():
    global ws  # Assurez-vous d'utiliser la variable globale ws
    if not ws.sock or not ws.sock.connected:
        time.sleep(0.5)
        ws.run_forever(ping_timeout=20, ping_interval=30)
    else:
        logging.info("WebSocket is already open")

def on_open(ws):
    def run(*args):
        subscribe_message = {
            "jsonrpc": "2.0",
            "method": "subscribe",
            "id": 0,
            "params": {
                "query": "tm.event='NewBlock'"
            }
        }
        ws.send(json.dumps(subscribe_message))
        logging.info("Subscribed to NewBlock events")
    threading.Thread(target=run).start()

ws_url = f"ws://{ip_address}:{port}/websocket"
ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)

ws.run_forever(ping_timeout=20, ping_interval=30)


def startWebsocketThorchain(shared_orderbook_data, eventWebsocketConnected):
    # Existing startWebsocket code until the WebSocket connection setup

    # Setup WebSocket handlers
    ws_url = f"ws://{ip_address}:{port}/websocket"
    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.run_forever(ping_timeout=20, ping_interval=30)