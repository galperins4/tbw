#!/usr/bin/env python
from pythark import Transport
import json
import os.path
from datetime import datetime


def parse_config():
    """
    Parse the config.json file and return the result.
    """
    with open('config.json') as data_file:
        data = json.load(data_file)
    return data


def create_payrun(network, addr, amt, passphrase, vendor_field="true block weight", secondphrase=""):
    """
    In python you can set optionnal arguments like that, by specifying a default value like vendor_filed, or by leaving
    an empty string like secondphrase.
    """
    transport = Transport()
    resp = transport.post_transaction(
        network, # Network
        addr, # RecipientAddress
        amt, # Amount
        passphrase, # First passphrase, mandatory
        vendor_field, # Vendor field, optionnal
        secondphrase) # Second passphrase, optionnal'''
    
    if resp['success'] == True:
        d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f = open('fail.txt', 'a')
        f.write(d+' '+addr+' '+str(amt)+'\n')
        f.close()
        
    return resp


def get_network(n):
    """
    Not sure about the point of this function but anyway, you only need one return at the end.
    """
    if n == "main":
        net = "ark"
    elif n == "dev":
        net = "dark"
    elif n == "kapu":
        net = "kapu"
    return net

if __name__ == '__main__':
    out = {}
    responses = []
    passphrase = parse_config()['passphrase']  # Get the passphrase from config.json
    secondphrase = parse_config()['secondphrase']  # Get the second passphrase from config.json
    network = get_network(parse_config()['network'])
    if os.path.exists('unpaid.json'): # You don't need to compare to true with python.
        # open results file and get highest block processed
        with open('unpaid.json') as json_data:
            pay = json.load(json_data)
            for k, v in pay.items():
                result = create_payrun(network, k, v, passphrase, "Payed by El Gooso !", secondphrase)
                out[k] = result
                responses.append(out)
            # create paid record
            d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('output/payment/' + d + '-payamt.json', 'w') as f:
                json.dump(pay, f)
            with open('output/payment/' + d + '-paytx.json', 'w') as g:
                json.dump(responses, g)
            # delete unpaid file
            os.remove('unpaid.json')
            # payment run complete
            print('Payment Run Completed!')
    else:
        print("File doesn't exist.")
