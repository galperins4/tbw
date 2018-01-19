
#!/usr/bin/env python

from tbw import parse_config
from snek.db.snek import SnekDB
from park.park import Park
from datetime import datetime
import json
import random
import time

def get_network(d, n, ip="localhost"):

    return Park(
        ip,
        n[d['network']]['port'],
        n[d['network']]['nethash'],
        n[d['network']]['version']
    )

def get_peers(park):
    peers = []
    peerfil= []
    
    try:
        peers = park.peers().peers()['peers']
        print('peers:', len(peers))
    except BaseException:
        # fall back to delegate node to grab data needed
        bark = get_network(data, network, data['delegate_ip'])
        peers = bark.peers().peers()['peers']
        print('peers:', len(peers))
        print('Switched to back-up API node')
        
    # some peers from some reason don't report height, filter out to prevent errors
    for i in peers:
        if "height" in i.keys():
            peerfil.append(i)
    
    #get max height        
    compare = max([i['height'] for i in peerfil]) 
    
    #filter on good peers
    f1 = list(filter(lambda x: x['version'] == network[data['network']]['version'], peerfil))
    f2 = list(filter(lambda x: x['delay'] < 350, f1))
    f3 = list(filter(lambda x: x['status'] == 'OK', f2))
    f4 = list(filter(lambda x: compare - x['height'] < 153, f3))
    print('filtered peers', len(f4))
    
    return f4

def broadcast(tx, p, park, r):
    out = []

    # take peers and shuffle the order
    # check length of good peers
    if len(p) < r:  # this means there aren't enough peers compared to what we want to broadcast to
        # set peers to full list
        peer_cast = p
    else:
        # normal processing
        random.shuffle(p)
        peer_cast = p[0:r]

    #broadcast to localhost/relay first
    for j in tx:
        records=[]
        try:
            transaction = park.transport().createTransaction(j)         
            records.extend((j['recipientId'], j['amount'], transaction['transactionIds'][0]))
            time.sleep(1)
        
        except BaseException:
            # fall back to delegate node to grab data needed
            bark = get_network(data, network, data['delegate_ip'])
            transaction = bark.transport().createTransaction(j)
            records.extend((j['recipientId'], j['amount'], transaction['transactionIds'][0]))
            time.sleep(1)
            
        out.append(records)
    
    snekdb.storeTransactions(out)
    
     # rotate through peers and begin broadcasting:
    for i in peer_cast:
        ip = i['ip']
        peer_park = get_network(data, network, ip)
        # cycle through and broadcast each tx on each peer and save responses
        for j in tx:    
            try:
                transaction = peer_park.transport().createTransaction(j)
                time.sleep(1)
            except:
                print("error")
 
if __name__ == '__main__':
   
    signed_tx = []
    data, network = parse_config()
    snekdb = SnekDB(data['dbusername'])
    
    # Get the passphrase from config.json
    passphrase = data['passphrase']
    # Get the second passphrase from config.json
    secondphrase = data['secondphrase']
    reach = data['reach']
    park = get_network(data, network)

    # get peers
    p = get_peers(park)

    pay = snekdb.stagedPayment().fetchall()
    
    if pay:
        for i in pay:              
            try:
                tx = park.transactionBuilder().create(i[0], str(i[1]), i[2], passphrase, secondphrase)
                signed_tx.append(tx)
            except BaseException:
                    # fall back to delegate node to grab data needed
                    bark = get_network(
                            data, data['delegate_ip'])
                    tx = bark.transactionBuilder().create(i[0], str(i[1]), i[2], passphrase, secondphrase)
                    print('Switched to back-up API node')
                    signed_tx.append(tx)
                
        broadcast(signed_tx, p, park, reach)
        snekdb.deleteStagedPayment()

        # payment run complete
        print('Payment Run Completed!')
