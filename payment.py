#!/usr/bin/env python
from pythark import Transport
import json
import os.path
from datetime import datetime
import arky.core
import arky.rest


def parse_config():
    """
    Parse the config.json file and return the result.
    """
    with open('config.json') as data_file:
        data = json.load(data_file)
    return data


def create_payrun(network, addr, amt, passphrase, vendor_field="true block weight", secondphrase=""):
    """
    Create payment run
    """
    '''
    transport = Transport()
    resp = transport.post_transaction(
        network, # Network
        addr, # RecipientAddress
        amt, # Amount
        passphrase, # First passphrase, mandatory
        vendor_field, # Vendor field, optionnal
        secondphrase) # Second passphrase, optionnal'''
    
    arky.rest.use(network)
    resp = arky.core.sendToken(amount=amt, recipientId=addr, secret=passphrase, secondSecret=secondphrase,vendorField=vendor_field)
    
    # convert broadcast to float
    bcast = float(resp['broadcast'].replace("%",""))
    
    if resp['success'] != True and bcast < 51:
        d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f = open('output/error/fail.txt', 'a')
        f.write(d+' '+addr+' '+str(amt)+' '+resp['broadcast']+'\n')
        f.close()
    
    return resp


def get_network(n):
    """
    Map pythark network choices to arky network choices.
    """
    if n == "main":
        net = "ark"
    else:
        net = n
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
                
                result = create_payrun(network, k, v, passphrase, msg, secondphrase)
                out[k] = result
            
            #create response output
            responses.append(out)
            # create paid record
            d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('output/payment/' + d + '-payamt.json', 'w') as f:
                json.dump(pay, f)
            
            #with open('output/payment/' + d + '-paytx.json', 'w') as g:
             #   json.dump(responses, g)
              
            #let's try with a txt file - DEBUGGING
            h = open('output/payment/'+d+'-paytx.txt', 'a')
            h.write(str(responses))
            h.close()
            
            # payment run complete
            print('Payment Run Completed!')
    else:
        print("File doesn't exist.")
