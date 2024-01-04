import express from 'express'
import { Client } from '@xchainjs/xchain-thorchain';
import { Network } from '@xchainjs/xchain-client';
import { cosmosclient } from '@cosmos-client/core';
import { buildDepositTx } from '@xchainjs/xchain-thorchain';
import { buildUnsignedTx } from '@xchainjs/xchain-thorchain';
import { baseAmount, Chain } from '@xchainjs/xchain-util';
import { CosmosSDKClient } from '@xchainjs/xchain-cosmos';
import { pswEncoded } from './psw.js'

import Long from "long"

export const DEFAULT_GAS_LIMIT_VALUE = '4000000'

const phrase = Buffer.from(pswEncoded, 'base64').toString('utf-8');

// const node = 'http://149.248.56.20'

const chainIds = {
  [Network.Mainnet]: 'thorchain-mainnet-v1',
  [Network.Stagenet]: 'chain-id-stagenet',
  [Network.Testnet]: 'chain-id-testnet',
}

const thorClient = new Client({ phrase, network: Network.Mainnet, chainIds })

const privKey = thorClient.getPrivateKey()
const signerPubkey = privKey.pubKey()
const fromAddress = 'thor19syh8vdjthkay5wmvsf83zhj0c9nxw0tyg2yy4'


async function deposit(asset_in, amount_in, memo_in, sequence, accountnum) {
  const start = Date.now()
  thorClient.setClientUrl({
    mainnet: {
      node: 'http://192.248.157.141:1317',
      rpc: 'http://192.248.157.141:27147',
    }
  })

  var asset_ok = { chain: Chain.THORChain, symbol: 'null', ticker: 'null', synth: true }

  if (asset_in == 'ETH/ETH') {
    asset_ok = { chain: Chain.Ethereum, symbol: 'ETH', ticker: 'ETH', synth: true }
  }

  if (asset_in == 'BNB/ETH-1C9') {
    asset_ok = { chain: Chain.Binance, symbol: 'ETH-1C9', ticker: 'ETH-1C9', synth: true }
  }

  if (asset_in == 'ETH/USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48') {
    asset_ok = { chain: Chain.Ethereum, symbol: 'USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48', ticker: 'USDC-0XA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48', synth: true }
  }

  if (asset_in == 'ETH/DAI-0X6B175474E89094C44DA98B954EEDEAC495271D0F') {
    asset_ok = { chain: Chain.Ethereum, symbol: 'DAI-0X6B175474E89094C44DA98B954EEDEAC495271D0F', ticker: 'DAI-0X6B175474E89094C44DA98B954EEDEAC495271D0F', synth: true }
  }

  if (asset_in == 'BTC/BTC') {
    asset_ok = { chain: Chain.Bitcoin, symbol: 'BTC', ticker: 'BTC', synth: true }
  }


  if (asset_in == 'BNB/BTCB-1DE') {
    asset_ok = { chain: Chain.Binance, symbol: 'BTCB-1DE', ticker: 'BTCB-1DE', synth: true }
  }

  if (asset_in == 'ETH/WBTC-0X2260FAC5E5542A773AA44FBCFEDF7C193BC2C599') {
    asset_ok = { chain: Chain.Ethereum, symbol: 'WBTC-0X2260FAC5E5542A773AA44FBCFEDF7C193BC2C599', ticker: 'WBTC-0X2260FAC5E5542A773AA44FBCFEDF7C193BC2C599', synth: true }
  }


  if (asset_in == 'BNB/BUSD-BD1') {
    asset_ok = { chain: Chain.Binance, symbol: 'BUSD-BD1', ticker: 'BUSD-BD1', synth: true }
  }

  if (asset_in == 'THOR.RUNE') {
    asset_ok = { chain: Chain.THORChain, symbol: 'RUNE', ticker: 'RUNE', synth: false }
  }

  if (asset_in == 'ETH/USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7') {
    asset_ok = { chain: Chain.Ethereum, symbol: 'USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7', ticker: 'USDT-0XDAC17F958D2EE523A2206206994597C13D831EC7', synth: true }
  }

  if (asset_in == 'AVAX/USDT-0X9702230A8EA53601F5CD2DC00FDBC13D4DF4A8C7') {
    asset_ok = { chain: Chain.Avalanche, symbol: 'USDT-0X9702230A8EA53601F5CD2DC00FDBC13D4DF4A8C7', ticker: 'USDT-0X9702230A8EA53601F5CD2DC00FDBC13D4DF4A8C7', synth: true }
  }

  if (asset_in == 'AVAX/USDC-0XB97EF9EF8734C71904D8002F8B6BC66DD9C48A6E') {
    asset_ok = { chain: Chain.Avalanche, symbol: 'USDC-0XB97EF9EF8734C71904D8002F8B6BC66DD9C48A6E', ticker: 'USDC-0XB97EF9EF8734C71904D8002F8B6BC66DD9C48A6E', synth: true }
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

  const txBuilder = buildUnsignedTx({
    cosmosSdk: thorClient.getCosmosClient().sdk,
    txBody: depositTxBody,
    signerPubkey: cosmosclient.codec.instanceToProtoAny(signerPubkey),
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
  const fromAddressAcc = cosmosclient.AccAddress.fromString(fromAddress)
  const account = await thorClient.getCosmosClient().getAccount(fromAddressAcc)
  const { account_number: accountNumber } = account
  if (!accountNumber) throw Error('Deposit failed - could not get account number ${accountNumber}')
  let current_sequence = account.sequence
  return current_sequence
}

async function get_account_number() {
  const fromAddress = thorClient.getAddress()
  const fromAddressAcc = cosmosclient.AccAddress.fromString(fromAddress)
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
      node: 'http://192.248.157.141:1317',
      rpc: 'http://192.248.157.141:27147'
    }

  }
  client.setClientUrl(client_url)

  client.cosmosClient = new CosmosSDKClient({
    server: client.getClientUrl().node,
    chainId: client.getChainId(Network.Mainnet),
    prefix: 'thor',
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


app.listen(5000, function () {
  console.log("Server is running on port 5000");
});