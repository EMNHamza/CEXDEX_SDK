# import asyncio
# import logging
# import time 

# # from proto.thorchain.v1.x.thorchain.types.msg_observed_txin_pb2 import MsgObservedTxIn
# # from proto.thorchain.v1.x.thorchain.types.msg_deposit_pb2 import MsgDeposit
# # from proto.decode_tx import AsyncTx
# from typing import Dict, List
# from classes.Message import Message
# from classes.Asset import AssetThorchain
# from classes.OpportunityThorchain import OpportunityThorchain
# from classes.Tx import Tx
# from tools.init import createAsset
# from thorchainCalcul import genericSimulePool
# from tools.myUtils import getPath, isOppNew

# # def checkMemo(memo: str) -> Dict:
# #     memoSplit = memo.split(":")
# #     assetOut = memoSplit[1]
# #     if len(memoSplit) > 3:
# #         amountOut = memoSplit[3]
# #     else:
# #         amountOut = 0
# #     return {"assetOut": assetOut, "amountOut": amountOut}


# # def isTxHashNew(txHash, listDictTxHash):
# #     isNew = False
# #     if any(txHash in dictTxHash.keys() for dictTxHash in listDictTxHash):
# #         isNew = False
# #     else:
# #         isNew = True
# #     return isNew


# # def isSignerNew(txHash, signer, dictTxHash):
# #     isNew = False
# #     if signer in dictTxHash[txHash]["signers"]:
# #         isNew = False
# #     else:
# #         isNew = True
# #     return isNew


# # def isMsgNew(Msg, listMsg):
# #     isNew = False
# #     if any(
# #         Msg.assetIn != msgInList.assetIn
# #         or Msg.assetOut != msgInList.assetOut
# #         or Msg.amountIn != msgInList.amountIn
# #         or Msg.amountOut != msgInList.amountOut
# #         for msgInList in listMsg
# #     ):
# #         isNew = True
# #     else:
# #         isNew = False
# #     return isNew


# # def decodeProto(
# #     listMsg: List[str],
# #     nbNode: int,
# #     currentBlock: float,
# #     dictAssets: Dict,
# #     dictMyAssets: Dict,
# # ) -> List[Message]:
# #     global dictTxHashes
# #     listMsgDecode = []
# #     # msgInit = Message(
# #     #     assetIn="",
# #     #     assetOut="",
# #     #     amountIn=0,
# #     #     amountOut=0,
# #     #     dictTxHash={},
# #     #     typeMsg="",
# #     #     synthIn=True,
# #     #     synthOut=True,
# #     # )
# #     # listMsgDecode.append(msgInit)
# #     msg: Message
# #     for msg in listMsg:
# #         # logging.info("new msg")
# #         decodeMsg = asyncio.run(AsyncTx().decode(msg))
# #         typeMsg = str(decodeMsg.body.messages[0].type_url)

# #         if "MsgDeposit" in typeMsg:
# #             messageDecode = decodeMsgDeposit(msg=decodeMsg)
# #             if messageDecode.assetIn.poolName in dictAssets.keys():
# #                 dictAssets[
# #                     messageDecode.assetIn.poolName
# #                 ].isSynth = messageDecode.assetIn.isSynth
# #                 messageDecode.assetIn = dictAssets[messageDecode.assetIn.poolName]

# #             if messageDecode.assetOut.poolName in dictAssets.keys():
# #                 dictAssets[
# #                     messageDecode.assetOut.poolName
# #                 ].isSynth = messageDecode.assetOut.isSynth
# #                 messageDecode.assetOut = dictAssets[messageDecode.assetOut.poolName]
# #             listMsgDecode.append(messageDecode)

# #         elif "MsgObservedTxIn" in typeMsg:
# #             listMessageDecodeTxIn = decodeMsgTxIn(
# #                 msg=decodeMsg, nbNode=nbNode, currentBlock=currentBlock
# #             )
# #             for msgDecodeTxIn in listMessageDecodeTxIn:
# #                 if msgDecodeTxIn.assetIn.poolName in dictMyAssets.keys():
# #                     dictMyAssets[
# #                         msgDecodeTxIn.assetIn.poolName
# #                     ].isSynth = msgDecodeTxIn.assetIn.isSynth
# #                     msgDecodeTxIn.assetIn = dictMyAssets[msgDecodeTxIn.assetIn.poolName]

# #                 if msgDecodeTxIn.assetOut.poolName in dictMyAssets.keys():
# #                     dictMyAssets[
# #                         msgDecodeTxIn.assetOut.poolName
# #                     ].isSynth = msgDecodeTxIn.assetOut.isSynth
# #                     msgDecodeTxIn.assetOut = dictMyAssets[
# #                         msgDecodeTxIn.assetOut.poolName
# #                     ]

# #                 listMsgDecode.append(msgDecodeTxIn)
# #     # tx: Tx
# #     # for tx in dictTxHashes.values():
# #     #     logging.info(
# #     #         f" each tx {tx.txHash, tx.assetIn.poolName, tx.assetOut.poolName, tx.amountIn, tx.amountOut, tx.isSend, len(tx.signers), tx.timeReceived}"
# #     #     )
# #     return listMsgDecode


# # def decodeMsgDeposit(msg: str) -> Message:
# #     msgEncode = msg.body.messages[0].value
# #     msg = MsgDeposit()
# #     msg.ParseFromString(msgEncode)
# #     memo = msg.memo
# #     extractMemo = checkMemo(memo)

# #     symbolAssetIn = msg.coins[0].asset.symbol
# #     chainAssetIn = msg.coins[0].asset.chain
# #     tickerAssetIn = msg.coins[0].asset.ticker
# #     isSynthIn = str(msg.coins[0].asset.synth)
# #     poolNameAssetIn = (chainAssetIn + "." + symbolAssetIn).upper()
# #     assetIn = createAsset(poolName=poolNameAssetIn)

# #     assetOut = extractMemo["assetOut"]
# #     assetOut = assetOut.upper()
# #     amountIn = msg.coins[0].amount
# #     amountOut = extractMemo["amountOut"]

# #     memoNameAssetOut = assetOut
# #     poolNameAssetOut = memoNameAssetOut.replace("/", ".").upper()
# #     assetOut = createAsset(poolName=poolNameAssetOut)

# #     # if '/' in memoNameAssetOut:
# #     #     assetOutSplit = memoNameAssetOut.split('/')
# #     # if '.' in memoNameAssetOut:
# #     #     assetOutSplit = memoNameAssetOut.split('.')

# #     # chainAssetOut = assetOutSplit[0]
# #     # symbolAssetOut = assetOutSplit[1]
# #     # tickerAssetOut = symbolAssetOut
# #     # nameAssetOut = symbolAssetOut

# #     if isSynthIn == "True":
# #         assetIn.isSynth = True
# #     else:
# #         assetIn.isSynth = False

# #     if "/" in memoNameAssetOut:
# #         assetOut.isSynth = True
# #     else:
# #         assetOut.isSynth = False

# #     msgDecode = Message(
# #         assetIn=assetIn,
# #         assetOut=assetOut,
# #         amountIn=amountIn,
# #         amountOut=amountOut,
# #         typeMsg="MsgDeposit",
# #         dictTxHash={},
# #         synthIn=assetIn.isSynth,
# #         synthOut=assetOut.isSynth,
# #     )

# #     return msgDecode


# # def decodeMsgTxIn(msg, nbNode: int, currentBlock: int):
# #     global dictTxHashes
# #     msgEncode = msg.body.messages[0].value
# #     msg = MsgObservedTxIn()
# #     msg.ParseFromString(msgEncode)
# #     signer = msg.signer
# #     listMsgTxIn = []

# #     for txs in msg.txs:
# #         tx = getTxData(txs=txs)
# #         # logging.info(
# #         #     f" tx early {tx.txHash, tx.assetIn.poolName, tx.assetOut.poolName, tx.amountIn, tx.amountOut, tx.isSend, len(tx.signers), tx.timeReceived}"
# #         # )
# #         if tx.txHash not in dictTxHashes.keys():
# #             # logging.info("new tx")
# #             dictTxHashes[tx.txHash] = tx
# #             dictTxHashes[tx.txHash].signers = [signer]
# #             dictTxHashes[tx.txHash].timeReceived = time.time()

# #         if signer not in dictTxHashes[tx.txHash].signers:
# #             dictTxHashes[tx.txHash].signers.append(signer)

# #             # logging.info(
# #             #     f" tx signer et dicttxhash[txhash] {len(tx.signers), len(dictTxHashes[tx.txHash].signers), tx.signers, dictTxHashes[tx.txHash].signers}"
# #             # )
# #             if (
# #                 len(dictTxHashes[tx.txHash].signers) > (2 / 3) * nbNode
# #                 and not dictTxHashes[tx.txHash].isSend
# #             ):
# #                 dictTxHashes[tx.txHash].isSend = True
# #                 logging.info(
# #                     f"PREDICTION DU SWAP au bloc {currentBlock} - {tx.assetIn.name} to {tx.assetOut.name} for {tx.amountIn} to {tx.amountOut} - {tx.txHash}"
# #                 )
# #                 msgDecode = Message(
# #                     assetIn=tx.assetIn,
# #                     assetOut=tx.assetOut,
# #                     amountIn=tx.amountIn,
# #                     amountOut=tx.amountOut,
# #                     dictTxHash=dictTxHashes[tx.txHash],
# #                     typeMsg="MsgObservedTxIn",
# #                     synthIn=False,
# #                     synthOut=False,
# #                 )
# #                 listMsgTxIn.append(msgDecode)

# #         # timeNow = time.time()
# #         # timer = timeNow - tx.timeReceived
# #         # if timer > timerDeleteTx:
# #         #     del dictTxHashes[tx.txHash]

# #     return listMsgTxIn


# # def getListMsgEncode(responseUnconfirmedTx):
# #     listMsgEncode = []
# #     if int(responseUnconfirmedTx["result"]["n_txs"]) > 0:
# #         for msgEncode in responseUnconfirmedTx["result"]["txs"]:
# #             if msgEncode not in listMsgEncode:
# #                 listMsgEncode.append(msgEncode)
# #     return listMsgEncode


# # def manageMempoolMessage(
# #     message: Message,
# #     responsePool,
# #     dictMyAssets: Dict,
# #     currentBlock: int,
# #     dictMyAssetsPath: Dict,
# # ):
# #     # if int(Message.amountIn) > amountMinToCheckOpportunity and int(Message.amountOut) > amountMinToCheckOpportunity:
# #     # for pool in responsePool:
# #     #     if pool['asset'] == dictMyAssets.values().poolName:
# #     #         logging.info()

# #     responsePool = genericSimulePool(
# #         responsePool=responsePool, message=message, dictMyAssets=dictMyAssets
# #     )
# #     logging.info(f"Après Simu, voir Block d'après")
# #     for pool in responsePool:
# #         for asset in dictMyAssets.values():
# #             if pool["asset"] == asset.poolName:
# #                 logging.info(
# #                     f"Pool {pool['asset'], pool['balance_asset'], pool['balance_rune']}"
# #                 )

# #     oppListAssetIn = createOpportunities(
# #         responsePool=responsePool,
# #         asset=message.assetIn,
# #         typeMsg=message.typeMsg,
# #         dictMyAssets=dictMyAssetsPath,
# #         currentBlock=currentBlock,
# #     )
# #     oppListAssetOut = createOpportunities(
# #         responsePool=responsePool,
# #         asset=message.assetOut,
# #         typeMsg=message.typeMsg,
# #         dictMyAssets=dictMyAssetsPath,
# #         currentBlock=currentBlock,
# #     )
# #     checkListOpportunity(oppList=oppListAssetIn)
# #     checkListOpportunity(oppList=oppListAssetOut)


# # def getTxData(txs: str) -> Tx:
# #     tx = Tx(
# #         assetIn="",
# #         assetOut="",
# #         amountIn=0,
# #         amountOut=0,
# #         memo="",
# #         txHash="",
# #         timeReceived=0,
# #         isSend=False,
# #         signers=[],
# #     )
# #     tx.txHash = txs.tx.id
# #     tx.memo = txs.tx.memo
# #     extractMemo = checkMemo(tx.memo)
# #     symbolAssetIn = txs.tx.coins[0].asset.symbol
# #     chainAssetIn = txs.tx.coins[0].asset.chain
# #     tickerAssetIn = txs.tx.coins[0].asset.ticker
# #     memoNameAssetOut = extractMemo["assetOut"]
# #     tx.amountIn = txs.tx.coins[0].amount
# #     tx.amountOut = extractMemo["amountOut"]

# #     poolNameAssetIn = chainAssetIn + "." + symbolAssetIn
# #     # logging.info(f"poolNameAssetIn {poolNameAssetIn}")
# #     tx.assetIn = createAsset(poolName=poolNameAssetIn)
# #     poolNameAssetOut = memoNameAssetOut.replace("/", ".").upper()
# #     tx.assetOut = createAsset(poolName=poolNameAssetOut)

# #     return tx

