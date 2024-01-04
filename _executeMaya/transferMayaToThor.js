import express from 'express'
import cosmosclient from '@cosmos-client/core';
import { CosmosSDKClient } from '@xchainjs/xchain-cosmos';
import { Client, buildTransferTx } from '@xchainjs/xchain-mayachain';
import { Network } from '@xchainjs/xchain-client';
import { buildDepositTx } from '@xchainjs/xchain-mayachain';
import { buildUnsignedTx } from '@xchainjs/xchain-mayachain';
import { baseAmount } from '@xchainjs/xchain-util';

import Long from "long"

export const DEFAULT_GAS_LIMIT_VALUE = '4000000'

const phrase = 'ethics scheme kangaroo enroll snake rug brand champion finish kiss scare title';

// const node = 'http://149.248.56.20'

const chainIds = {
  [Network.Mainnet]: 'mayachain-mainnet-v1',
  [Network.Stagenet]: 'mayachain-stagenet',
  [Network.Testnet]: 'chain-id-testnet',
}


const nodePublicMaya = 'http://localhost'


const thorClient = new Client({ phrase, network: Network.Mainnet, chainIds })

const privKey = thorClient.getPrivateKey()
const signerPubkey = privKey.pubKey()
const fromAddress = 'maya19syh8vdjthkay5wmvsf83zhj0c9nxw0tyl5gj9'


async function deposit(asset_in, amount_in, memo_in, sequence, accountnum) {
  const start = Date.now()
  thorClient.setClientUrl({
    mainnet: {
      node: 'http://localhost:1317',
      rpc: 'http://localhost:27147',
    }
  })

  var asset_ok = { chain: 'THOR', symbol: 'null', ticker: 'null', synth: true }

  if (asset_in == 'ETH/ETH') {
    asset_ok = { chain: 'ETH', symbol: 'ETH', ticker: 'ETH', synth: true }
  }


  if (asset_in == 'ETH/USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48') {
    asset_ok = { chain: 'ETH', symbol: 'USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48', ticker: 'USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48', synth: true }
  }


  if (asset_in == 'BTC/BTC') {
    asset_ok = { chain: 'BTC', symbol: 'BTC', ticker: 'BTC', synth: true }
  }

  if (asset_in == 'THOR/RUNE') {
    asset_ok = { chain: 'THOR', symbol: 'RUNE', ticker: 'RUNE', synth: true }
  }

  if (asset_in == 'ETH/USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7') {
    asset_ok = { chain: 'ETH', symbol: 'USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7', ticker: 'USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7', synth: true }
  }

  if (asset_in == 'MAYA.CACAO') {
    asset_ok = { chain: 'MAYA', symbol: 'CACAO', ticker: 'CACAO', synth: false }
  }

  amount_in = baseAmount(amount_in)

  const depositTxBody = await buildDepositTx({
    msgNativeTx: {
      memo: memo_in,
      signer: fromAddress,
      coins: [
        {
          asset: asset_ok,
          amount: amount_in.amount().toString(),
        },
      ],
    },
    nodeUrl: thorClient.getClientUrl().node,
    chainId: thorClient.getChainId(),
  })


  const transferTxBody = await buildTransferTx({
    fromAddress: fromAddress,
    toAddress: "maya1g98cy3n9mmjrpn0sxmn63lztelera37n8yyjwl",
    assetAmount: amount_in,
    assetDenom: "thor/rune", // A MODIF SI PAS DU RUNE IN 
    memo: memo_in,
    nodeUrl: thorClient.getClientUrl().node,
    chainId: thorClient.getChainId(),
  })

  const txBuilder = buildUnsignedTx({
    cosmosSdk: thorClient.getCosmosClient().sdk,
    txBody: depositTxBody,
    signerPubkey: cosmosclient.default.codec.instanceToProtoAny(signerPubkey),
    gasLimit: Long.fromString(DEFAULT_GAS_LIMIT_VALUE),
    sequence: sequence,
  })

  const txHash = await thorClient.getCosmosClient().signAndBroadcast(txBuilder, privKey, accountnum)

  if (!txHash) throw Error('Invalid transaction hash: ${txHash}')

  const duration = Date.now() - start
  console.log(duration + 'ms')
  return txHash
}

async function get_sequence() {
  const fromAddress = thorClient.getAddress()
  const fromAddressAcc = cosmosclient.default.AccAddress.fromString(fromAddress)
  const account = await thorClient.getCosmosClient().getAccount(fromAddressAcc)
  const { account_number: accountNumber } = account
  if (!accountNumber) throw Error('Deposit failed - could not get account number ${accountNumber}')
  let current_sequence = account.sequence
  return current_sequence
}

async function get_account_number() {
  const fromAddress = thorClient.getAddress()
  const fromAddressAcc = cosmosclient.default.AccAddress.fromString(fromAddress)
  const account = await thorClient.getCosmosClient().getAccount(fromAddressAcc)
  const { account_number: accountNumber } = account
  if (!accountNumber) throw Error('Deposit failed - could not get account number ${accountNumber}')
  return accountNumber
}

async function init_sequence() {
  let new_sequence = await get_sequence()
  return new_sequence.low
}

function init_client(client) {
  var client_url = {
    [Network.Mainnet]: {
      node: 'http://localhost:1317',
      rpc: 'http://localhost:27147'
    }

  }
  client.setClientUrl(client_url)

  client.cosmosClient = new CosmosSDKClient({
    server: client.getClientUrl().node,
    chainId: client.getChainId(Network.Mainnet),
    prefix: 'maya',
  })
}

init_client(thorClient)
let new_sequence = 0
let accountnum = 0
let nb_tx = 0
let txhash = ''
const app = express();

app.get('/deposit', async (req, res) => {

  if (new_sequence == 0) {
    new_sequence = await init_sequence()
    new_sequence = new_sequence - 1
    accountnum = await get_account_number()
  }

  console.log(nb_tx)

  try {
    const { amount1, asset1, memo1 } = req.query;
    new_sequence += 1
    txhash = await deposit(asset1, amount1, memo1, new_sequence, accountnum)

    nb_tx += 1
    res.json(txhash)
  }

  catch (e) {
    console.log(e)
    new_sequence = await init_sequence()
    accountnum = await get_account_number()
    console.log(nb_tx)
  }
  return txhash
})


app.listen(8000, function () {
  console.log("Server is running on port 8000");
});