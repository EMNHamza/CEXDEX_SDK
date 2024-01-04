import logging
import requests

from _logs.log_config import test_setup_logging
test_setup_logging()

from utilsBybit.bybit_websocket import startWebsocket
from tools.init import initBalance, initBalanceDict
from testProcess import processGetThorchainBlock, processOpportunityConsumer, processGetMayaBlock, processUpdateDict

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
    
    processUpdateDict_ = Process(target=processUpdateDict, args=(balanceDictShared,lock, sharedCounter))

    processBlockThorchainProducer = Process(target=processGetThorchainBlock, args=(slidingListBlock, BalancesShared, orderbookDataShared, queueOpportunitiesThorchain,queueOpportunitiesToExecute, balanceDictShared, poolDictShared))
    processBlockMayaProducer = Process(target=processGetMayaBlock, args=(slidingListBlock, BalancesShared, orderbookDataShared,queueOpportunitiesMaya,queueOpportunitiesToExecute, balanceDictShared, poolDictShared))
    
    processOpportunityConsumer_ = Process(target=processOpportunityConsumer, args=(queueOpportunitiesToExecute, BalancesShared, lock, balanceDictShared, poolDictShared, sharedCounter))

# ----- 
    
    
    processOrderbookProducer.start()
    eventWebsocketConnected.wait()
    
    processUpdateDict_.start()
    processBlockThorchainProducer.start()
    processBlockMayaProducer.start()

    processOpportunityConsumer_.start()

# ----- 

    processOrderbookProducer.join()
    
    processUpdateDict_.join()
    processBlockThorchainProducer.join()
    processBlockMayaProducer.join()
    
    processOpportunityConsumer_.join()
