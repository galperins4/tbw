#!/usr/bin/env python

from snek.db.snek import SnekDB
from snek.db.ark import ArkDB
import time
import json
import os.path
import subprocess

atomic = 100000000
transaction_fee = .1 * atomic

def parse_config():
    """
    Parse the config.json file and return the result.
    """
    with open('config/config.json') as data_file:
        data = json.load(data_file)
        
    with open('config/networks.json') as network_file:
        network = json.load(network_file)

    return data, network

def allocate(lb):
    
    # create temp log / export output for block  rewards
    log = {}
    json_export = {}
    rewards_check = 0
    voter_check = 0
    delegate_check = 0
    
    block_voters = get_voters()

    # get total votes
    approval = sum(int(item[1]) for item in block_voters)

    # get block reward
    block_reward = lb[2]
    fee_reward = lb[3]
    total_reward = block_reward+fee_reward

    # calculate delegate/reserve/other shares
    for k, v in data['keep'].items():
        if k == 'reserve':
            keep = (int(block_reward * v)) + fee_reward
        else:
            keep = (int(block_reward * v))

        # assign  shares to log and rewards tracking
        keep_addr = data['pay_addresses'][k]
        log[keep_addr] = keep
        snekdb.updateDelegateBalance(keep_addr, keep)
        
        # increment delegate_check for double check
        delegate_check += keep

    # calculate voter share
    vshare = block_reward * data['voter_share']

    # loop through the current voters and assign share
    for i in block_voters:

        # convert balance from str to int
        bal = int(i[1])

        # filter out 0 balances for processing
        if bal > 0:
            share_weight = bal / approval  # calc share rate
            
            # calculate block reward
            reward = int(share_weight * vshare)
            
            # populate log for block export records
            log[i[0]] = reward
            
            # update reserve from blacklist assign
            if i[0] == data["blacklist_assign"]:
                snekdb.updateDelegateBalance(i[0], reward)
            else:
                #add voter reward to sql database
                snekdb.updateVoterBalance(i[0], reward)

            # voter and rewards check
            voter_check += 1
            rewards_check += reward

    print(f"""Processed Block: {lb[4]}\n
    Voters processed: {voter_check}
    Total Approval: {approval}
    Voters Rewards: {rewards_check}
    Delegate Reward: {delegate_check}
    Voter + Delegate Rewards: {rewards_check + delegate_check}
    Total Block Rewards: {total_reward}""")

    #mark as processed
    snekdb.markAsProcessed(lb[4])

    # check to see if log file exists
    if not os.path.exists(
            'output/log/result.json'):  # does not exists so create
        # create a json export for the block rewards for initial file
        json_export[lb[4]] = log
        # append log to json file for future use
        with open('output/log/result.json', 'a') as fp:
            json.dump(json_export, fp)

    else:  # read and add block as key
        with open('output/log/result.json') as f:
            json_decoded = json.load(f)

        json_decoded[lb[4]] = log

        with open('output/log/result.json', 'w') as f:
            json.dump(json_decoded, f)


def manage_folders():
    sub_names = ["log", "payment", "error"]
    for sub_name in sub_names:
        os.makedirs(os.path.join('output', sub_name), exist_ok=True)

def black_list(voters):
    #block voters and distribute to voters
    if data["blacklist"] == "block":
        bl_adjusted_voters = []
        for i in voters:
            if i[0] in data["blacklist_addr"]:
                bl_adjusted_voters.append((i[0], 0))
            else:
                bl_adjusted_voters.append((i[0], i[1]))
    
    #block voters and keep in reserve account
    elif data["blacklist"] == "assign":
        bl_adjusted_voters = []
        accum = 0
        
        for i in voters:
            if i[0] in data["blacklist_addr"]:
                accum += i[1]
            else:
                bl_adjusted_voters.append((i[0], i[1]))
        
        bl_adjusted_voters.append((data["blacklist_assign"], accum))

    else:
        bl_adjusted_voters = voters

    return bl_adjusted_voters

def voter_cap(voters):

    # cap processing
    max_wallet = int(data['vote_cap'] * atomic)
    
    if max_wallet > 0:
        cap_adjusted_voters = []
        for i in voters:
            if i[1] > max_wallet and i[0] != data["blacklist_assign"]:
                cap_adjusted_voters.append((i[0], max_wallet))
            else:
                cap_adjusted_voters.append((i[0],i[1]))
                
    else:
        cap_adjusted_voters = voters

    return cap_adjusted_voters

def get_voters():

    #get voters
    initial_voters = arkdb.voters()
    
    #process blacklist:
    bl_adjust = black_list(initial_voters)
    block_voters = voter_cap(bl_adjust)
    
    snekdb.storeVoters(block_voters)    
    
    return block_voters

def get_rewards():
    
    rewards = []
    for k, v in data['pay_addresses'].items():
        rewards.append(v)
    
    snekdb.storeRewards(rewards) 

def del_address(addr):
    for k,v in data['pay_addresses'].items():
        if addr == v:
            msg = k + " - True Block Weight"
            
    return msg

def process_voter_pmt(txfee, min):
    # process voters 
    voters = snekdb.voters().fetchall()
    for row in voters:
        if row[1] > min:               
               
            msg = "Goose Voter - True Block Weight"
            
            if data['cover_tx_fees'] == "Y":
                # update staging records
                snekdb.storePayRun(row[0], row[1], msg)
                # adjust sql balances
                snekdb.updateVoterPaidBalance(row[0])
            
            else:
                net = row[1]-txfee
                #only pay if net payment is greater than 0, accumulate rest
                if net > 0:
                    snekdb.storePayRun(row[0], net, msg)
                    snekdb.updateVoterPaidBalance(row[0])
                
def fixed_deal():
    res = 0
    private_deals = data['fixed_deal_amt']
    
    # check to make sure fixed payment addresses haven't unvoted 
    fix_check = arkdb.voters()
    tmp = {}
    for i in fix_check:
        tmp[i[0]] = i[1]
    
    for k,v in private_deals.items():
        if k in tmp.keys() and tmp[k]>0:
            msg = "Goose Voter - True Block Weight-F"
            # update staging records
            fix = v * atomic
            if data['cover_tx_fees'] == 'Y':
                snekdb.storePayRun(k, fix, msg)
                #accumulate fixed deals balances
                res += (fix + transaction_fee)
            
            else:
                net_fix = fix - transaction_fee
                snekdb.storePayRun(k, net_fix, msg)
                #accumulate fixed deals balances
                res += (net_fix)
        else:
            res += 0
            
    return res

def process_delegate_pmt(fee):
    # process delegate first
    delreward = snekdb.rewards().fetchall()        
    for row in delreward:
        if row[0] == data['pay_addresses']['reserve']:
                
            if data['fixed_deal'] == 'Y':
                amt = fixed_deal()
                if data['cover_tx_fees'] == 'Y':
                    totalFees = amt + fee
                else:
                    totalFees = amt + transaction_fee
                
                net_pay = row[1] - totalFees
            
            else:
                if data['cover_tx_fees'] == 'Y':
                    net_pay = row[1] - fee
                else:
                    net_pay = row[1] - transaction_fee
    
            if net_pay <= 0:
                # delete staged payments to prevent duplicates
                snekdb.deleteStagedPayment()
                
                print("Not enough in reserve to cover transactions")
                print("Update interval and restart")
                quit()
                
            # update staging records
            snekdb.storePayRun(row[0], net_pay, del_address(row[0]))
            
            #adjust sql balances
            snekdb.updateDelegatePaidBalance(row[0])
                
        else:
            if data['cover_tx_fees'] == 'N':
                # update staging records
                net = row[1] - transaction_fee
                if net > 0:
                    snekdb.storePayRun(row[0], net, del_address(row[0]))
                    # adjust sql balances
                    snekdb.updateDelegatePaidBalance(row[0])
                
            else: 
                snekdb.storePayRun(row[0], row[1], del_address(row[0]))
                # adjust sql balances
                snekdb.updateDelegatePaidBalance(row[0])

def payout():
    min = int(data['min_payment'] * atomic)

    # count number of transactions greater than payout threshold
    d_count = len([j for j in snekdb.rewards()])
    
    if data['cover_tx_fees'] == 'Y':
        v_count = len([i for i in snekdb.voters() if i[1]>min])
    else:
        v_count = len([i for i in snekdb.voters() if (i[1]>min and (i[1]-transaction_fee)>0))
    
    if v_count>0:
        print('Payout started!')
        
        tx_count = v_count+d_count
        # calculate tx fees needed to cover run in satoshis
        tx_fees = tx_count * int(transaction_fee)
    
        # process delegate rewards
        process_delegate_pmt(tx_fees)
        
        # process voters 
        process_voter_pmt(transaction_fee, min)

        # call process to run payments
        subprocess.Popen(['python3', 'pay.py'])

def interval_check(bc):
    if bc % data['interval'] == 0:
        # check if there is an unpaid balance for voters
        total = 0
        # get voter balances
        r = snekdb.voters()
        for row in r:
            total += row[1]
                
        print("Total Voter Unpaid:",total)
        
        if total > 0:
            return True
        else: 
            return False
        
def initialize():
    print("First time setup - initializing SQL database....")
    # initalize sqldb object
    snekdb.setup()
    
    # connect to DB and grab all blocks
    print("Importing all prior forged blocks...")
    all_blocks = arkdb.blocks("yes")
        
    # store blocks
    print("Storing all historical blocks and marking as processed...")
    snekdb.storeBlocks(all_blocks)
        
    # mark all blocks as processed
    for row in all_blocks:
        snekdb.markAsProcessed(row[4])
        
    # set block count to rows imported
    block_count = len(all_blocks)
    print("Imported block count:", block_count)
    
    # initialize voters and delegate rewards accounts
    get_voters()
    get_rewards()
    
    print("Initial Set Up Complete. Please re-run script!")
    quit()
    
    
def block_counter():
    c = snekdb.processedBlocks().fetchall()
    return len(c)

if __name__ == '__main__':
    # check for folders needed
    manage_folders()  
    
    # get config data
    data, network = parse_config()

    # initialize db connection
    arkdb = ArkDB(network[data['network']]['db'], data['dbusername'], data['publicKey'])
    
    # check to see if ark.db exists, if not initialize db, etc
    if os.path.exists('ark.db') == False:    
        snekdb = SnekDB(data['dbusername'])
        initialize()
    
    # check for new rewards accounts to initialize if any changed
    snekdb = SnekDB(data['dbusername'])
    get_rewards()

    # set block count        
    block_count = block_counter()

    # processing loop
    while True:
        # get last 50 blocks
        blocks = arkdb.blocks()
        # store blocks
        snekdb.storeBlocks(blocks)
        # check for unprocessed blocks
        unprocessed = snekdb.unprocessedBlocks().fetchall()
          
        # query not empty means unprocessed blocks
        if unprocessed:
            for b in unprocessed:
                
                #allocate
                allocate(b)
                #get new block count
                block_count = block_counter()
                
                #increment count
                print('\n')
                print(f"Current block count : {block_count}")
                
                check = interval_check(block_count)
                if check:
                    payout()
                     
                print('\n' + 'Waiting for the next block....' + '\n')
                # sleep 5 seconds between allocations
                time.sleep(5)

        # pause 30 seconds between runs
        time.sleep(30)
        






