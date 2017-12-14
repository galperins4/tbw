#!/usr/bin/env python
from pythark import Transport
import json
import os.path
from datetime import datetime

#import config
with open('config.json', encoding='utf-8') as data_file:
    data = json.loads(data_file.read())

passphrase = data['passphrase']
secondphrase = data['secondphrase']
responses = []

def create_payrun(addr, amt):
    
    transport = Transport()
    
    #payout
    resp = transport.post_transaction(
    network, # Network
    addr, # RecipientAddress
    amt, # Amount
    passphrase, # First passphrase, mandatory
    "true block weight", # Vendor field, optionnal
    secondphrase) # Second passphrase, optionnal'''
    
    return resp
    
def main():
    out={}
    if os.path.exists('unpaid.json') == True:
        #open results file and get highest block processed
        with open('unpaid.json') as json_data:  
            pay = json.load(json_data)
        
            for k,v in pay.items():
                #print(k,v)
                result = create_payrun(k,v)
                out[k]=result
                responses.append(out)
            
            
            
            #create paid record
            d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('output/payment/'+d+'-payamt.json', 'w') as f:
                json.dump(pay, f)
                
            with open('output/payment/'+d+'-paytx.json', 'w') as g:
                json.dump(responses, g)   
                
        #delete unpaid file        
        os.remove('unpaid.json')
        #payment run complete
        print('Payment Run Completed!')

def get_network(n):
    if n == "main":
        net ="ark"
        return net
    elif n == "dev":
        net ="dark"
        return net
    elif n == "kapu":
        return n             
 
network = get_network(data['network'])

main()

        
    
   
