import json
import threading
import websocket
import time
import requests
import csv
from datetime import datetime


# "139.180.222.148" "192.248.157.141"

ip_address = "127.0.0.1"
port = "27147"
URL_POOL_MAYA = f"http://{ip_address}:1317/mayachain/pools"
URL_BLOCK_MAYA = f"http://{ip_address}:27147/status"
URL_BLOCK_MAYA_NEW = f"http://{ip_address}:1317/mayachain/lastblock"
current_block = None
block_info = {}
processed_blocks = set()

# Nom du fichier CSV
nom_fichier_csv = "block_info.csv"
 

def get_current_timestamp():
    # Renvoie l'heure actuelle avec une précision à la milliseconde
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def save_to_csv(block_number, source, elapsed_time):
    timestamp = get_current_timestamp()
    with open(nom_fichier_csv, mode='a', newline='', encoding='utf-8') as fichier:
        writer = csv.writer(fichier)
        writer.writerow([timestamp, block_number, source, elapsed_time])


def getMayaBlockLastblock():
    try:
        response = requests.get(url=URL_BLOCK_MAYA_NEW, timeout=3)
        response.raise_for_status()
        data = response.json()
        block_number = min([int(i["mayachain"]) for i in data])
        if block_number not in block_info and block_number not in processed_blocks:
            block_info[block_number] = (time.time(), 'lastBlock')
            print(f"New block {block_number} detected first by Last Block request. Timestamp recorded.")
            save_to_csv(block_number, 'lastBlock', 0)
        elif block_info[block_number][1] != 'lastBlock' and (block_number,'lastBlock') not in processed_blocks:
            start_time = block_info[block_number][0]
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Block {block_number} now received in getMayaBlockLastblock.")
            print(f"Temps écoulé depuis la réception : {elapsed_time} secondes")
            save_to_csv(block_number, 'lastBlock', elapsed_time)
            processed_blocks.add((block_number,'lastBlock'))
        return    
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'getMayaBlockStatus - error type: {type(err).__name__}, error message: {err}')


def getMayaBlockStatus():
    try:
        response = requests.get(url=URL_BLOCK_MAYA, timeout=3)
        response.raise_for_status()
        data = response.json()
        block_number = int(data["result"]["sync_info"]["latest_block_height"])
        if block_number not in block_info and block_number not in processed_blocks:
            block_info[block_number] = (time.time(), 'http')
            print(f"New block {block_number} detected first by HTTP request. Timestamp recorded.")
            save_to_csv(block_number, 'http', 0)
        elif block_info[block_number][1] != 'http' and (block_number,'http') not in processed_blocks:
            start_time = block_info[block_number][0]
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Block {block_number} now received in getMayaBlockStatus.")
            print(f"Temps écoulé depuis la réception WebSocket: {elapsed_time} secondes")
            save_to_csv(block_number, 'http', elapsed_time)
            processed_blocks.add((block_number,'http'))
        return    
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'getMayaBlockStatus - error type: {type(err).__name__}, error message: {err}')


def on_message(ws, message):
    data = json.loads(message)
    block_number = int(data['result']['data']['value']['block']['header']['height'])
    if block_number not in block_info and block_number not in processed_blocks:
        block_info[block_number] = (time.time(), 'websocket')
        print(f"New block {block_number} detected first on WebSocket. Timestamp recorded.")
        save_to_csv(block_number, 'websocket', 0)
    elif block_info[block_number][1] != 'websocket' and (block_number,'websocket') not in processed_blocks:
        start_time = block_info[block_number][0]
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Block {block_number} now received on WebSocket.")
        print(f"Temps écoulé depuis la détection HTTP: {elapsed_time} secondes")
        save_to_csv(block_number, 'websocket', elapsed_time)
        processed_blocks.add((block_number,'websocket'))


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
        print("Subscribed to NewBlock events")
    threading.Thread(target=run).start()

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("### WebSocket Closed ###")

ws_url = f"ws://{ip_address}:{port}/websocket"
ws = websocket.WebSocketApp(ws_url,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

def check_block_status():
    while True:
        getMayaBlockStatus()
        getMayaBlockLastblock()
        time.sleep(0.1)  # Pause de 0.1 seconde entre chaque vérification

# Créer le fichier CSV et écrire l'en-tête
with open(nom_fichier_csv, mode='w', newline='', encoding='utf-8') as fichier:
    writer = csv.writer(fichier)
    writer.writerow(["Timestamp", "Block Number", "Source", "Time"])

# Démarrer le thread de vérification des blocs
threading.Thread(target=check_block_status).start()
ws.run_forever()
