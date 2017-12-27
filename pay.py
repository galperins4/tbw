#!/usr/bin/env python

from tbw import get_network, parse_config
from datetime import datetime
import json
import os.path
import random
import time


def get_peers(park, net):
    peers = []
    networks = json.load(open('networks.json'))
    
    try:
        peers = park.peers().peers()['peers']
        print('peers:', len(peers))
    except BaseException:
        # fall back to delegate node to grab data needed
        bark = get_network(parse_config(), parse_config()['delegate_ip'])
        peers = bark.peers().peers()['peers']
        print('peers:', len(peers))
        print('Switched to back-up API node')

    '''    
    for peer in peers:
        if (peer['status'] != 'OK') or (
                peer['version'] != '1.1.1') or (peer['delay'] > 500):
            peers.remove(peer)'''
            
    f1 = list(filter(lambda x: x['version'] == networks[data['network']]['version'], peers))
    f2 = list(filter(lambda x: x['delay'] < 350, f1))
    f3 = list(filter(lambda x: x['status'] == 'OK', f2))
    f4 = list(filter(lambda x: compare - x['height'] < 153, f3))
    print('filtered peers', len(f4))
    
    return f4

def broadcast(tx, p, park, r):
    out = {}
    responses = {}

    # take peers and shuffle the order
    # check length of good peers
    if len(p) < r:  # this means there aren't enough peers compared to what we want to broadcast to
        # set peers to full list
        peer_cast = p
    else:
        # normal processing
        random.shuffle(p)
        peer_cast = p[0:r]

    # rotate through peers and begin broadcasting:
    count = 0
    for i in peer_cast:
        responses = {}
        # cycle through and broadcast each tx on each peer and save responses
        for j in tx:
            try:
                transaction = park.transport().createTransaction(j)
                responses[j['recipientId']] = transaction
                time.sleep(1)
            except BaseException:
                # fall back to delegate node to grab data needed
                bark = get_network(
                    parse_config(), parse_config()['delegate_ip'])
                transaction = bark.transport().createTransaction(j)
                responses[j['recipientId']] = transaction
                time.sleep(1)

        out['Peer' + str(count)] = responses
        count += 1

    # create paid record
    d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('output/payment/' + d + '-paytx.json', 'w') as f:
        json.dump(out, f)


if __name__ == '__main__':
    signed_tx = []
    data = parse_config()
    # Get the passphrase from config.json
    passphrase = data['passphrase']
    # Get the second passphrase from config.json
    secondphrase = data['secondphrase']
    reach = data['reach']
    park = get_network(data)

    # get peers
    p = get_peers(park, data)

    if os.path.exists('unpaid.json'):
        # open unpaid.json file
        with open('unpaid.json') as json_data:
            # load file
            pay = json.load(json_data)
            time.sleep(5)

            # delete unpaid file
            os.remove('unpaid.json')

            out = {}

            for k, v in pay.items():
                if k not in data['pay_addresses'].values():
                    msg = "Goose Voter - True Block Weight"
                else:
                    for key, value in data['pay_addresses'].items():
                        if k == value:
                            msg = key + " - True Block Weight"
                try:
                    tx = park.transactionBuilder().create(k, str(v), msg, passphrase, secondphrase)
                    signed_tx.append(tx)
                except BaseException:
                    # fall back to delegate node to grab data needed
                    bark = get_network(
                        data, data['delegate_ip'])
                    tx = bark.transactionBuilder().create(k, str(v), msg, passphrase, secondphrase)
                    print('Switched to back-up API node')
                    signed_tx.append(tx)

            broadcast(signed_tx, p, park, reach)

            # write out payment amounts if we need to resend
            d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('output/payment/' + d + '-payamt.json', 'w') as f:
                json.dump(pay, f)

            # payment run complete
            print('Payment Run Completed!')
    else:
        print("File doesn't exist.")
