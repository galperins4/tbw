# -*- coding: utf-8 -*-
from collections import Counter
from pythark import Delegate
from pythark import Account
from pythark import Block
import time
import json
import os.path

#move to config
delegate = ''
interval = 4
tx_fee = 'yes'
voter_share = 0.70
delegate_share = 0.30
reserve = ''
delegate_addr = ''
tbw_rewards = {} #blank dictionary for rewards
block = 0 # set default block to 0, will update from call or json later
block_count = 0 # running counter for payouts

def allocate(lb, pk):
    #create temp log / export output for block  rewards
    log = {}
    json_export = {}
    rewards_check = 0
    voter_check = 0
    
    #get voters / share / block reward same time
    d = Delegate()
    block_voters = d.get_voters(pk)
    
    #check if new voters first before allocating - need to create new key in dict
    new_voter(block_voters)
    
    #get total votes
    approval = int(d.search_delegates(delegate)['delegates'][0]['vote'])
    
    #get block reward
    block_reward = int(lb['blocks'][0]['reward'])
    fee_reward = int(lb['blocks'][0]['totalFee'])
    total_reward = int(lb['blocks'][0]['totalForged'])
    
    #calculate delegate and voter shares
    vshare = block_reward * voter_share
    dshare = (int(block_reward * delegate_share)) + int(fee_reward)
    
    #assign delegate share
    log[reserve] = dshare
    tbw_rewards[reserve]['unpaid'] += dshare
    
    #loop through the current voters and assign share
    for i in block_voters['accounts']:

        #convert balance from str to int
        i['balance'] = int(i['balance'])
    
        #filter out 0 balances for processing
        if i['balance']>0: 
            i['share_weight']=  round(i['balance']/approval,8) #calc share rate
            i['reward']= int(i['share_weight']*vshare) # calculate block reward
            log[i['address']] = i['reward'] #populate log for block export records
            tbw_rewards[i['address']]['unpaid']+= i['reward'] #add voter reward to unpaid tally in main tbw_rewards_dict
            
            #voter and rewards check
            voter_check+=1
            rewards_check += i['reward']
        
    print('Processed Block:', last_block_height)
    print('Voters processed:', voter_check)
    print('Voter Rewards:', rewards_check)
    print('Delegate Reward:', dshare)
    print('Voter+Delegate Rewards:', (rewards_check+dshare))
    print('Total Block Rewards:', total_reward)
    
    with open('output/log/'+(str(last_block_height))+'-tbw.json', 'w') as f:
        json.dump(tbw_rewards, f)
    
    #check to see if log file exists
    if os.path.exists('output/log/result.json') == False: #does not exists so create
        json_export[last_block_height]=log #create a json export for the block rewards for initial file
         
        #append log to json file for future use
        with open('output/log/result.json', 'a') as fp:
            json.dump(json_export, fp)
            
    else: #read and add block as key
        with open('output/log/result.json') as f:
            json_decoded=json.load(f)
        
        json_decoded[last_block_height] = log
        
        with open('output/log/result.json', 'w') as f:
            json.dump(json_decoded, f)
            
#function to check if a new block was created
def new_block(l,n):
    if (n-l)>0:
        global block
        print('new block', n)
        block = n
        return True
    
    else:
        print('no new block')
        return False
    
#function to check for new voters
def new_voter(v):
    for i in v['accounts']:
        test = i['address'] in tbw_rewards.keys()
        if test == False:
            tbw_rewards[i['address']] = {'unpaid':0, 'paid': 0}

def initialize():
    global block
    global tbw_rewards
    global block_count
    #check for block logs and payment folders on start up
    if os.path.exists('output'):
        pass
    else:
        os.mkdir('output')
        os.mkdir('output/log')
        os.mkdir('output/payment')
    
    d = Delegate()
    #get public key
    pubKey = d.get_delegate(delegate)['delegate']['publicKey']
        
    #get voters
    block_voters = d.get_voters(pubKey)
    
    #check if first run
    if block==0:
        #check to see if the file already exists - means tbw was already running and got restarted
        if os.path.exists('output/log/result.json') == True:
            #open results file and get highest block processed
            with open('output/log/result.json') as json_data:
                test = json.load(json_data)
   
                # get all blocks in a list and get hightest one 
                l = [int(i) for i in test]
                last_processed_block = str((max(l)))
    
            #now open the block-tbw to get the last known balances and input to tbw_rewards to start
            tbw_rewards = json.load(open('output/log/'+last_processed_block+'-tbw.json'))
            #set last bock to most recent one from files
            block = int(last_processed_block)
            block_count = len(l)
        
        else: #initialize paid/unpaid records for voters
            for i in block_voters['accounts']:
                tbw_rewards[i['address']] = {'unpaid':0, 'paid': 0}
    
            #initialize paid/unpaid records for reserve account
            tbw_rewards[reserve] = {'unpaid':0, 'paid': 0}

    return pubKey

def payout():
    #initialize pay_run
    pay_run = {}
    unpaid = {} #payment file

    #get account balance
    acc = Account()
    r = acc.get_balance(delegate_addr)
    bal = int(r['balance'])
    
    #get unpaid balances greater than 0 
    pay_run = {k:v for (k,v) in tbw_rewards.items() if v['unpaid']>0}
    
    #count number of transactions in pay_run
    tx_count = len(pay_run)
    #calculate tx fees needed to cover run in satoshis
    tx_fees = tx_count * 10000000
    
    #get total value of payments for the run
    value = sum(map(Counter, pay_run.values()), Counter())
    total = value['unpaid']
    
    #pay if bal>total
    if bal>total:
        for k,v in tbw_rewards.items():
            if v['unpaid']>0:    
                #process voters
                if k != reserve:
                    print('pay voter', k, v['unpaid'])
                    unpaid[k] = v['unpaid']
                                
                    #subtract unpaid amount and add to paid
                    v['paid'] += v['unpaid'] #add unpaid to paid column
                    v['unpaid'] -= v['unpaid'] #zero out unpaid
    
                #process delegate share
                else:
                    print('pay reserve', k, v['unpaid'])
                    #pay delegate
                    net_pay = v['unpaid']-tx_fees
                    unpaid[k] = net_pay
                    
                    #subtract unpaid amount and add to paid
                    v['paid'] += v['unpaid'] #add unpaid to paid column
                    v['unpaid'] -= v['unpaid'] #zero out unpaid

    else:
        print('not enough in account to pay')
        
    #dump 
    with open('unpaid.json', 'w') as f:
        json.dump(unpaid, f)
    
pubKey = initialize()

while True:
   #MAIN PROGRAM
   #get last block generated 
   #possibly loop every 7 seconds
   b = Block()
   last_block = b.get_blocks(limit=1, generatorPublicKey=pubKey) 
   last_block_height = last_block['blocks'][0]['height']
   #check for new block to process 
   check = new_block(block, last_block_height)

   #if new block allocate
   if check == True:
       allocate(last_block, pubKey)
       block_count +=1
       print("block count:", block_count)
   else:
       time.sleep(7)
        
   if block_count % interval == 0:
       print('run payout function')
       payout()
       block_count +=1
