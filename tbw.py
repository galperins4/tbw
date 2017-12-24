# -*- coding: utf-8 -*-
from collections import Counter
from park.park import Park
import time
import json
import os.path
import subprocess
from datetime import datetime

tbw_rewards = {}  # blank dictionary for rewards
block = 0  # set default block to 0, will update from call or json later
block_count = 0  # running counter for payouts

networks = {
        'ark': ['6e84d08bd299ed97c212c886c98a57e36545c8f5d645ca7eeae63a8bd62d8988', 4001, '1.0.3'],
        'dark': ['578e820911f24e039733b45e4882b73e301f813a0d2c31330dafda84534ffa23', 4002, '1.1.1'],
        'kapu': ['313ea34c8eb705f79e7bc298b788417ff3f7116c9596f5c9875e769ee2f4ede1', 9700, '0.3.0']
           }

def parse_config():
    """
    Parse the config.json file and return the result.
    """
    with open('config.json') as data_file:
        data = json.load(data_file)
             
    return data

def allocate(lb, p):
    data = parse_config()

    # create temp log / export output for block  rewards
    log = {}
    json_export = {}
    rewards_check = 0
    voter_check = 0
    delegate_check = 0
    
    block_voters = get_voters(p, data)
    
    # check if new voters first before allocating - need to create new key in dict
    new_voter(block_voters)
    
    # get total votes
    approval = sum(int(item['balance']) for item in block_voters['accounts']) 
    
    # get block reward
    block_reward = int(lb['blocks'][0]['reward'])
    fee_reward = int(lb['blocks'][0]['totalFee'])
    total_reward = int(lb['blocks'][0]['totalForged'])
    
    # calculate delegate/reserve/other shares
    for k,v in data['keep'].items():
        if k == 'reserve':
            keep = (int(block_reward * v)) + int(fee_reward)
        else:
            keep = (int(block_reward * v))
            
        #assign  shares to log and rewards tracking
        keep_addr = data['pay_addresses'][k]
        log[keep_addr] = keep
        tbw_rewards[keep_addr]['unpaid'] += keep
        
        #increment delegate_check for double check
        delegate_check +=keep
    
    # calculate voter share
    vshare = block_reward * data['voter_share']
    
    # loop through the current voters and assign share
    for i in block_voters['accounts']:

        # convert balance from str to int
        i['balance'] = int(i['balance'])
    
        # filter out 0 balances for processing
        if i['balance'] > 0:
            i['share_weight'] = i['balance'] / approval # calc share rate
            i['reward'] = int(i['share_weight'] * vshare)  # calculate block reward
            log[i['address']] = i['reward']  # populate log for block export records
            tbw_rewards[i['address']]['unpaid'] += i['reward']  # add voter reward to unpaid tally in main tbw_rewards_dict
            
            # voter and rewards check
            voter_check += 1
            rewards_check += i['reward']

    print("""Processed Block: {0}\n
    Voters processed: {1}
    Total Approval: {2}
    Voters Rewards: {3}
    Delegate Reward: {4}
    Voter + Delegate Rewards: {5}
    Total Block Rewards: {6}""".format(last_block_height, voter_check, approval, rewards_check, delegate_check, (rewards_check + delegate_check), total_reward))

    with open('output/log/' + (str(last_block_height)) + '.json', 'w') as f:
        json.dump(tbw_rewards, f)
    
    # check to see if log file exists
    if not os.path.exists('output/log/result.json'):  # does not exists so create
        # create a json export for the block rewards for initial file
        json_export[last_block_height] = log
        # append log to json file for future use
        with open('output/log/result.json', 'a') as fp:
            json.dump(json_export, fp)
            
    else:  # read and add block as key
        with open('output/log/result.json') as f:
            json_decoded = json.load(f)
        
        json_decoded[last_block_height] = log
        
        with open('output/log/result.json', 'w') as f:
            json.dump(json_decoded, f)
            
# function to check if a new block was created
def new_block(l, n):
    if (n - l) > 0:
        global block
        block = n
        return True
    else:
        return False
    
# function to check for new voters
def new_voter(v):
    for i in v['accounts']:
        test = i['address'] in tbw_rewards.keys()
        if not test:
            tbw_rewards[i['address']] = {'unpaid': 0, 'paid': 0}
            
def manage_folders():
    # Rewrited it, now it handles it like it should, don't do anything if the directorys already exists thanks to the
    # exist_ok parameter, and if one of the directory doesn't exists, creates it.
    sub_names = ["log", "payment", "error"]
    for sub_name in sub_names:
        os.makedirs(os.path.join('output', sub_name), exist_ok=True)

def get_highest_block():
    with open('output/log/result.json') as json_data:
        test = json.load(json_data)
        # get all blocks in a list and get hightest one
        l = [int(i) for i in test]
        last_processed_block = str((max(l)))
    return last_processed_block

def get_block_count():
    with open('output/log/result.json') as json_data:
        test = json.load(json_data)
        # get all blocks in a list and get hightest one
        l = [int(i) for i in test]
    return sorted(l)

def get_voters(p, data):
    
    pubKey = data['publicKey'] #grab pubKey
    
    block_voters = p.delegates().voters(pubKey)
    '''    
    try:
        block_voters = p.delegates().voters(pubKey)
    except:
        #fall back to delegate node to grab data needed
        bark = get_network(data, data['delegate_ip'])
        block_voters = bark.delegates().voters(pubKey)
        print('Switched to back-up API node')'''
    
    return block_voters
    
def initialize():
    global block
    global tbw_rewards
    global block_count
    
    data = parse_config() # import config
    park = get_network(data, data['tbw_ip']) # initialize park config
    manage_folders() #check for folders needed
    
    block_voters = get_voters(park, data)
    
    # check if first run
    if block == 0:
        # check to see if the file already exists - means tbw was already running and got restarted
        if os.path.exists('output/log/result.json'):
            # open results file and get highest block processed
            last_processed_block = get_highest_block()
            # now open the block-tbw to get the last known balances and input to tbw_rewards to start
            tbw_rewards = json.load(open('output/log/' + last_processed_block + '.json'))
            # set last block to most recent one from files
            block = int(last_processed_block)
            block_count = len(get_block_count())
            
            #check for new reserve addresses 
            for k,v in data['pay_addresses'].items():
                if v not in tbw_rewards.keys():
                    tbw_rewards[v] = {'unpaid': 0, 'paid': 0}
            
        else:  # initialize paid/unpaid records for voters
            for i in block_voters['accounts']:
                tbw_rewards[i['address']] = {'unpaid': 0, 'paid': 0}
            # initialize paid/unpaid records for reserve account
            for k,v in data['pay_addresses'].items():
                tbw_rewards[v] = {'unpaid': 0, 'paid': 0}
            
def payout():
    data = parse_config()
    min = data['min_payment'] * 100000000
   
    # initialize pay_run
    unpaid = {}  # payment file
    
    # count number of transactions greater than payout threshold
    tx_count = len({k: v for k, v in tbw_rewards.items() if v['unpaid'] > min})
    # calculate tx fees needed to cover run in satoshis
    transaction_fee = 10000000
    tx_fees = tx_count * transaction_fee
   
    # generate pay file
    for k, v in tbw_rewards.items():
        if v['unpaid'] > min:
            # process voters and non-reserve address
            if k != data['pay_addresses']['reserve']:
                unpaid[k] = v['unpaid']
                                
                # subtract unpaid amount and add to paid
                v['paid'] += v['unpaid']  # add unpaid to paid column
                v['unpaid'] -= v['unpaid']  # zero out unpaid
    
            # process delegate share
            else:
                # pay delegate
                net_pay = v['unpaid']-tx_fees
                unpaid[k] = net_pay
                    
                # subtract unpaid amount and add to paid
                v['paid'] += v['unpaid']  # add unpaid to paid column
                v['unpaid'] -= v['unpaid']  # zero out unpaid
        
    # dump
    with open('unpaid.json', 'w') as f:
        json.dump(unpaid, f)
        
    # call process to run payments
    subprocess.Popen(['python3', 'pay.py'])

def get_network(data, ip):
    
    net = Park(ip,
            networks[data['network']][1],
            networks[data['network']][0],
            networks[data['network']][2]
            )

    return net 
   
if __name__ == '__main__':
    
    park = initialize()
    config = parse_config()
    pubKey = config['publicKey']
    while True:
         last_block = park.blocks().blocks({
         "limit": 1,
         "generatorPublicKey": pubKey
         })
        
        
        '''try:
            last_block = park.blocks().blocks({
                                "limit": 1,
                                "generatorPublicKey": pubKey
                                })
        
            print(last_block)

        except:
            #fall back to delegate node to grab data needed
            bark = get_network(config, config['delegate_ip'])
            
            last_block = bark.blocks().blocks({
                                "limit": 1,
                                "generatorPublicKey": pubKey
                                })
            print('Switched to back-up API node')'''
        
        last_block_height = last_block['blocks'][0]['height']
        check = new_block(block, last_block_height)
        
        if check:
            block_count += 1
            print("Current block count : {0}".format(block_count))
            allocate(last_block, park)
            print('\n' + 'Waiting for the next block....' + '\n')
            
                    #set pay flag to help prevent dup payments
            file = open('flag.txt', 'w')
            file.write('N')
            file.close()    

        else:
            time.sleep(7)

        if block_count % config['interval'] == 0:
            # use unpaid check to ensure payment function doesnt run miltiple times in divisible block
            value = sum(map(Counter, tbw_rewards.values()), Counter())
            total = value['unpaid']

            file = open('flag.txt', 'r')
            flag = file.read()
            file.close()

            if total > 0 and flag == 'N':
                #check for any missed blocks                
                #missed_block(b, config['interval'])
                print('Payout started !')
                payout()
                
                #set payout flag to yes until next block
                f = open('flag.txt', 'w')
                f.write('Y')
                file.close()
