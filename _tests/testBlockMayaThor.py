from utilsMaya.mayaInteraction import getMayaBlock
from utilsThorchain.thorchainInteraction import getBlock
import time

currentblockMaya = 0
currentblockThorchain = 0
lastTimeMaya = time.time()
lastTimeThorchain = time.time()

while True:
    blockMaya = getMayaBlock()
    blockThor = getBlock()
    currentTime = time.time()

    if blockMaya > currentblockMaya:
        elapsedMaya = currentTime - lastTimeMaya
        print(f'New block Maya {blockMaya}, Time elapsed: {elapsedMaya:.2f} seconds')
        currentblockMaya = blockMaya
        lastTimeMaya = currentTime

    if blockThor > currentblockThorchain:
        elapsedThorchain = currentTime - lastTimeThorchain
        print(f'New block Thorchain {blockThor}, Time elapsed: {elapsedThorchain:.2f} seconds')
        currentblockThorchain = blockThor
        lastTimeThorchain = currentTime

    # Optional: sleep for a short duration to prevent excessive CPU usage
    time.sleep(0.2)  # Sleep for 100ms
