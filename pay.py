#!/usr/bin/python

from tbw import get_network
from datetime import datetime
import json
import os.path
import random
import time

def parse_config():
    """
    Parse the config.json file and return the result.
    """
    with open('config.json') as data_file:
        data = json.load(data_file)
    
    return data

def get_peers(n):
    peers = []
    
    try:
        peers = n.peers().peers()['peers']
    except:
        #fall back to delegate node to grab data needed
        bark = get_network(parse_config(), parse_config()['delegate_ip'])
        peers = bark.peers().peers()['peers']
        print('Switched to back-up API node')

    for peer in peers:
        if (peer['status'] != 'OK') or (peer['version'] != '1.1.1') or (peer['delay'] > 500):
            peers.remove(peer)

    return peers

def broadcast(tx,p,park,r):
    out = {}
    responses = {}
    
    #take peers and shuffle the order
    #check length of good peers
    if len(p)<r: #this means there aren't enough peers compared to what we want to broadcast to
        #set peers to full list
        peer_cast = p
    else:
        #normal processing
        random.shuffle(p)
        peer_cast = p[0:r]
   
    #rotate through peers and begin broadcasting:
    count=0
    for i in peer_cast:
        responses = {}
        #cycle through and broadcast each tx on each peer and save responses
        for j in tx:
             try:
                 transaction = park.transport().createTransaction(j)
                 responses[j['recipientId']] = transaction
                 time.sleep(1)
             except:
                 #fall back to delegate node to grab data needed
                 bark = get_network(parse_config(), parse_config()['delegate_ip'])
                 transaction = bark.transport().createTransaction(j)
                 responses[j['recipientId']] = transaction
                 time.sleep(1)
        
        out['Peer'+str(count)] = responses
        count+=1
            
    #create paid record
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('output/payment/' + d + '-paytx.json', 'w') as f:
        json.dump(out, f)

if __name__ == '__main__':    
    signed_tx = []
    passphrase = parse_config()['passphrase']  # Get the passphrase from config.json
    secondphrase = parse_config()['secondphrase']  # Get the second passphrase from config.json
    reach = parse_config()['reach']
    park = get_network(parse_config())
    
    #get peers
    p = get_peers(park)
    
    if os.path.exists('unpaid.json'):
        # open unpaid.json file
        with open('unpaid.json') as json_data:
            #load file
            pay = json.load(json_data)
            time.sleep(5)
            
            # delete unpaid file
            os.remove('unpaid.json')
            
            out = {}
        
            for k, v in pay.items():
                if k not in parse_config()['pay_addresses'].values():
                    msg = "Goose Voter - True Block Weight"
                else:
                    for key,value in parse_config()['pay_addresses'].items():
                        if k == value:
                             msg = key + " - True Block Weight"
                try:
                    tx = park.transactionBuilder().create(k, str(v), msg, passphrase, secondphrase)
                    signed_tx.append(tx)
                except:
                    #fall back to delegate node to grab data needed
                    bark = get_network(parse_config(), parse_config()['delegate_ip'])
                    tx = bark.transactionBuilder().create(k, str(v), msg, passphrase, secondphrase)
                    print('Switched to back-up API node')
                    signed_tx.append(tx)
       
            broadcast(signed_tx, p, park, reach)
            
            #write out payment amounts if we need to resend
            d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('output/payment/' + d + '-payamt.json', 'w') as f:
                json.dump(pay, f)
            
            # payment run complete
            print('Payment Run Completed!')
    else:
        print("File doesn't exist.")
