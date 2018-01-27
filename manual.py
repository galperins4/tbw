#!/usr/bin/env python
from snek.db.snek import SnekDB
from tbw import parse_config
import subprocess

atomic = 100000000
transaction_fee = .1 * atomic

if __name__ == '__main__':
    data, network = parse_config()
    snekdb = SnekDB(data['dbusername'])
    
def payout():
    min = int(data['min_payment'] * atomic)

    # count number of transactions greater than payout threshold
    d_count = len([j for j in snekdb.rewards()])
    v_count = len([i for i in snekdb.voters() if i[1]>min])
    
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

def process_delegate_pmt(fee):
    # process delegate first
    delreward = snekdb.rewards().fetchall()        
    for row in delreward:
        if row[0] == data['pay_addresses']['reserve']:
                
            if data['fixed_deal'] == 'Y':
                amt = fixed_deal()
                totalFees = amt + fee
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
                
def fixed_deal():
    res = 0
    private_deals = data['fixed_deal_amt']
                
    for k,v in private_deals.items():
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
            
    return res

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