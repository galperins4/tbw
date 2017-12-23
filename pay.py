#!/usr/bin/python

from park.park import Park
from tbw import get_network
from datetime import datetime
import json
import os.path

#import random

def parse_config():
    """
    Parse the config.json file and return the result.
    """
    with open('config.json') as data_file:
        data = json.load(data_file)
    return data

def get_peers(n):
    peers = []
    
    p = Peer(n)
    peers = p.get_peers()['peers']

    for peer in peers:
        if (peer['status'] != 'OK') or (peer['version'] != '1.1.1') or (peer['delay'] > 500):
            peers.remove(peer)

    return peers

if __name__ == '__main__':    
    passphrase = parse_config()['passphrase']  # Get the passphrase from config.json
    secondphrase = parse_config()['secondphrase']  # Get the second passphrase from config.json
    reach = parse_config()['reach']
    park = get_network(parse_config())
    
    #get peers
    #p = get_peers(network)
    
    if os.path.exists('unpaid.json'):
        # open unpaid.json file
        with open('unpaid.json') as json_data:
            #load file
            pay = json.load(json_data)
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
                
                transaction = park.transactions().create(k, str(v), msg, passphrase, secondphrase)
                
                out[k] = transaction
            
            #output transaction confirms
            d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('output/payment/' + d + '-paytx.json', 'w') as f:
                json.dump(out, f)
            
            #out payment amounts if we need to resend
            with open('output/payment/' + d + '-payamt.json', 'w') as f:
                json.dump(pay, f)
            
            # payment run complete
            print('Payment Run Completed!')
    else:
        print("File doesn't exist.")
