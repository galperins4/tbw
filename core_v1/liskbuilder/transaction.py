#!/usr/bin/env python

from liskbuilder.builder import Builder

class TransactionBuilder(Builder):
    
    def create(self, coin, recipientId, amount, secret, secondSecret=None):
        return self.build('transaction.create'+coin+'Transaction', {
			"recipientId": recipientId,
			"amount": amount,
			"secret": secret,
			"secondSecret": secondSecret
        })