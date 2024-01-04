import logging
import requests

from _logs.log_config import setup_logging
setup_logging()

from utilsBybit.bybit_websocket import startWebsocket
from utilsThorchain.thorchainWebsocket import startWebsocketThorchain
from utilsMaya.mayaWebsocket import startWebsocketMaya


from tools.init import initBalance, initBalanceDict
from _processesTest import processGetThorchainBlock, processOpportunityConsumer, processGetMayaBlock, processUpdateDict

from multiprocessing import Process, Queue, Manager, Event, Lock
from collections import deque


if __name__ == "__main__":
    httpClient = requests.Session()
    manager = Manager()

    slidingListBlock = deque(maxlen=3)
    slidingListBlock.append(0)
    slidingListBlock.append(0)
    slidingListBlock.append(0)

    queueBlockThorchain = Queue()
    queueBlockMaya = Queue()
    queueOpportunitiesToExecute = Queue()
    queueOpportunitiesThorchain = Queue()
    queueOpportunitiesMaya = Queue()
    
    lock = Lock()

    eventWebsocketConnected = Event()
    
    BalancesShared = manager.Namespace()
    BalancesShared = initBalance()
    
    orderbookDataShared = manager.dict()
    poolDictShared = manager.dict()
    balanceDictShared = manager.dict()
    
    balanceDictInit = initBalanceDict()
    balanceDictShared.update(balanceDictInit)
    
    sharedCounter = manager.Value('i', 0)

# ----- 

    processOrderbookProducer = Process(target=startWebsocket, args=(orderbookDataShared,eventWebsocketConnected))
    
    processThorchainWebsocket = Process(target=startWebsocketThorchain, args=(BalancesShared, orderbookDataShared, queueOpportunitiesThorchain,queueOpportunitiesToExecute, balanceDictShared, poolDictShared))
    processMayaWebsocket = Process(target=startWebsocketMaya, args=(BalancesShared, orderbookDataShared, queueOpportunitiesThorchain,queueOpportunitiesToExecute, balanceDictShared, poolDictShared))

    processUpdateDict_ = Process(target=processUpdateDict, args=(balanceDictShared,lock, sharedCounter))

    # processBlockThorchainProducer = Process(target=processGetThorchainBlock, args=(slidingListBlock, BalancesShared, orderbookDataShared, queueOpportunitiesThorchain,queueOpportunitiesToExecute, balanceDictShared, poolDictShared))
    # processBlockMayaProducer = Process(target=processGetMayaBlock, args=(slidingListBlock, BalancesShared, orderbookDataShared,queueOpportunitiesMaya,queueOpportunitiesToExecute, balanceDictShared, poolDictShared))
    
    processOpportunityConsumer_ = Process(target=processOpportunityConsumer, args=(queueOpportunitiesToExecute, BalancesShared, lock, balanceDictShared, poolDictShared, sharedCounter))

# ----- 
    
    processOrderbookProducer.start()
    eventWebsocketConnected.wait()

    processUpdateDict_.start()
    
    processThorchainWebsocket.start()
    # processBlockMayaProducer.start()

    # processMayaWebsocket.start()
        
    


    processOpportunityConsumer_.start()

# # ----- 

    processOrderbookProducer.join()
    
    processUpdateDict_.join()
    processThorchainWebsocket.join()
    # processMayaWebsocket.join()
    
    processOpportunityConsumer_.join()
