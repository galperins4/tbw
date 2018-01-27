#!/usr/bin/env python

from tbw import parse_config, payout

atomic = 100000000
transaction_fee = .1 * atomic

if __name__ == '__main__':
   
    data, network = parse_config()
    payout()