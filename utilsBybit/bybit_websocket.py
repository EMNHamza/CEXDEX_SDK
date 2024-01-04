from time import sleep
from utilsBybit.bybit_utils import getOrderbookUSDCPairSymbols
from pybit.unified_trading import WebSocket
from utilsBybit.api_config_manager import load_config
from multiprocessing import Manager
import json
import logging

def startWebsocket(shared_orderbook_data, eventWebsocketConnected):
    # Load configuration for API
    config = load_config()
    api_key = config.get("api_key")
    api_secret = config.get("secret_key")

    # Setup WebSocket connection for private data with authentication
    ws_private = WebSocket(
        testnet=False,
        channel_type="spot",
        api_key=api_key,
        api_secret=api_secret,
        ping_interval=20,
        ping_timeout=10,
        retries=20,
        restart_on_error=True,
        trace_logging=False,
    )

    orderbook_data = {}

    # Callback function to update orderbook data
    def handle_orderbook(message, symbol):
        data = message["data"]
        shared_orderbook_data[symbol] = data

    # Function to subscribe to an orderbook stream for a given symbol
    def subscribe_to_orderbook(symbol):
        ws_private.orderbook_stream(
            depth=50,
            symbol=symbol,
            callback=lambda message: handle_orderbook(message, symbol)
        )

    # List of symbols to subscribe to
    symbols = getOrderbookUSDCPairSymbols()

    # print(symbols)

    # Subscribe to orderbooks for each symbol
    for symbol in symbols:
        subscribe_to_orderbook(symbol)

    if ws_private.is_connected():
        logging.info("WebSocket bybit is already connected.")
        eventWebsocketConnected.set()
    else:
        # Attendez que ws_private soit connecté
        while not ws_private.is_connected():
            sleep(0.2)  # Attendre un peu avant de vérifier à nouveau

    # Une fois que ws_private est connecté, définissez l'événement et enregistrez le log
    logging.info("WebSocket bybit is now connected.")
    eventWebsocketConnected.set()
    # Main loop
    try:
        while True:
            sleep(2)
            # Print or process orderbook data as needed
            # print(shared_orderbook_data)
    except KeyboardInterrupt:
        print("WebSocket bybit process terminated.")
    finally:
        # Clean up and close WebSocket connection
        ws_private.exit()


# This allows the script to be run standalone for testing
# This is to run the script standalone for testing
if __name__ == "__main__":
    with Manager() as manager:
        shared_orderbook_data = manager.dict()
        startWebsocket(shared_orderbook_data)