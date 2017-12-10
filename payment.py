#!/usr/bin/env python
from pythark import Transport
import json
import os.path
from datetime import datetime

passphrase = ""
secondphrase = ""
responses = []

def create_payrun(addr, amt):
    
    transport = Transport()
    
    #payout
    resp = transport.post_transaction(
    "dark", # Network
    addr, # RecipientAddress
    amt, # Amount
    passphrase, # First passphrase, mandatory
    "test_true block weight", # Vendor field, optionnal
    secondphrase) # Second passphrase, optionnal'''
    
    return resp
    
def main():
    if os.path.exists('unpaid.json') == True:
        #open results file and get highest block processed
        with open('unpaid.json') as json_data:  
            pay = json.load(json_data)
        
            for k,v in pay.items():
                print(k,v)
                result = create_payrun(k,v)
                responses.append(result)
            
            #create paid record
            with open('output//payment//'+str(datetime.now().date())+'-payamt.json', 'w') as f:
                json.dump(pay, f)
                
            with open('output//payment//'+str(datetime.now().date())+'-paytx.json', 'w') as g:
                json.dump(responses, g)   
                
        #delete unpaid file        
        os.remove('unpaid.json')
        #payment run complete
        print('Payment Run Completed!')

main()
    
   