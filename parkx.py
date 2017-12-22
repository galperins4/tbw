#!/usr/bin/python
from Naked.toolshed.shell import muterun_js
import requests
import json
import os.path
from pythark import Peer
import random
from datetime import datetime

def parse_config():
    """
    Parse the config.json file and return the result.
    """
    with open('config.json') as data_file:
        data = json.load(data_file)
    return data

def get_network(n):
    """
    Map pythark network choices to arky network choices.
    """
    if n == "main":
        name = "ark"
        hex = "0x17"
        hash = "6e84d08bd299ed97c212c886c98a57e36545c8f5d645ca7eeae63a8bd62d8988"
        version = "1.0.3"
    elif n == "dark":
        name = n
        hex = "0x1E"
        hash = "578e820911f24e039733b45e4882b73e301f813a0d2c31330dafda84534ffa23"
        version = "1.1.1"
    elif n == "kapu":
        name = n
        hex = "0x2D"
        hash = "313ea34c8eb705f79e7bc298b788417ff3f7116c9596f5c9875e769ee2f4ede1"
        version = "0.3.0"
    
    return name, hex, hash, version

def get_peers(n):
    peers = []
    
    p = Peer(n)
    peers = p.get_peers()['peers']

    for peer in peers:
        if (peer['status'] != 'OK') or (peer['version'] != '1.1.1') or (peer['delay'] > 500):
            peers.remove(peer)

    return peers

def create_signed_tx(network, recipientId, amount, vendorField, secret, secondSecret=""):

    # file we use to store the tx for ark.js
    transactionScript="output/bake/transaction.js"

    # create the transaction.js from the template
    with open("template", "rt") as fin:
        with open(transactionScript, "wt") as fout:
            for line in fin:
                line=line.replace('{{ network }}', network)
                line=line.replace('{{ recipientId }}', recipientId)
                line=line.replace('{{ amount }}', str(amount))
                line=line.replace('{{ vendorField }}', vendorField)
                line=line.replace('{{ secret }}', secret)
                line=line.replace('{{ secondSecret }}', secondSecret)
                fout.write(line)

    # execute via nodejs and grab the output
    response = muterun_js(transactionScript)

    if response.exitcode == 0:
        # transaction=json.dumps(response.stdout)
        transaction = json.loads(response.stdout.decode('utf-8')) #signed tx as json

    else:
        print(response.stderr)

    return transaction

def broadcast(tx,p,i,h,v):
    responses = {}
    
    #set headers
    headers = {
       "nethash": h,
       "version": v,
       "port": "1"
      }

    #take peers and shuffle the order
    #check length of good peers
    if len(p)<i: #this means there aren't enough peers compared to what we want to broadcast to
        #set peers to full list
        peer_cast = p
    else:
        #normal processing
        random.shuffle(p)
        peer_cast = p[0:i]
      
    #rotate through peers and begin broadcasting:
    count=0
    for i in peer_cast:
        out = {}
        responses = {}
        url = "http://"+i['ip']+":"+str(i['port'])+"/peer/transactions"
        #cycle through and broadcast each tx on each peer and save responses
        for j in tx:
            payload = {"transactions":[j]}
            resp = requests.post(url, headers = headers, json = payload)
            responses[j['recipientId']] = resp.json()
            
        out['Peer'+str(count)] = responses
        count+=1
            
    # create paid record
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('output/payment/' + d + '-paytx.json', 'w') as f:
        json.dump(out, f)
    print(out)
    
if __name__ == '__main__':    
    signed_tx = []
    passphrase = parse_config()['passphrase']  # Get the passphrase from config.json
    secondphrase = parse_config()['secondphrase']  # Get the second passphrase from config.json
    reach = parse_config()['reach']
    network, hex, nethash, version = get_network(parse_config()['network'])
    
    #get peers
    p = get_peers(network)
    
    if os.path.exists('unpaid.json'):
        # open unpaid.json file
        with open('unpaid.json') as json_data:
            #load file
            pay = json.load(json_data)
            # delete unpaid file
            os.remove('unpaid.json')
            
            for k, v in pay.items():
                if k not in parse_config()['pay_addresses'].values():
                    msg = "Goose Voter - True Block Weight"
                else:
                    for key,value in parse_config()['pay_addresses'].items():
                        if k == value:
                             msg = key + " - True Block Weight"
                
                tx = create_signed_tx(hex, k, v, msg, passphrase, secondphrase)
                signed_tx.append(tx)
                
            #broadcast all transaction
            broadcast(signed_tx, p, reach, nethash, version)
            
            d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('output/payment/' + d + '-payamt.json', 'w') as f:
                json.dump(pay, f)
            
            # payment run complete
            print('Payment Run Completed!')
    else:
        print("File doesn't exist.")
