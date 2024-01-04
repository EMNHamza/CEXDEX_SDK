from multiprocessing import Process, Queue, Manager, Event, Lock

manager = Manager()

sharedCounter = manager.Value('i', 0)

sharedCounter.value = sharedCounter.value + 1

print(f'sharedCounter {sharedCounter}')