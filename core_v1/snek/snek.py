import sqlite3
from datetime import datetime

class SnekDB:
    def __init__(self, u):
        self.connection=sqlite3.connect('/home/'+u+'/tbw/ark.db')
        self.cursor=self.connection.cursor()

    def commit(self):
        return self.connection.commit()

    def execute(self, query, args=[]):
        return self.cursor.execute(query, args)

    def executemany(self, query, args):
        return self.cursor.executemany(query, args)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def setup(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS blocks (id varchar(64), timestamp int, reward int, totalFee bigint, height int, processed_at varchar(64) null)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS voters (address varchar(36), u_balance bigint, p_balance bigint, share float )")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS transactions (address varchar(36), amount varchar(64), id varchar(64), processed_at varchar(64) )")
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS delegate_rewards (address varchar(36), u_balance bigint, p_balance bigint )")
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS staging (address varchar(36), payamt bigint, msg varchar(64), processed_at varchar(64) null )")

        self.connection.commit()

    def storePayRun(self, address, amount, msg):
        staging=[]

        staging.append((address, amount, msg, None))

        self.executemany("INSERT INTO staging VALUES (?,?,?,?)", staging)

        self.commit()
    
    def storeBlocks(self, blocks):
        newBlocks=[]

        for block in blocks:
            self.cursor.execute("SELECT id FROM blocks WHERE id = ?", (block[0],))

            if self.cursor.fetchone() is None:
                newBlocks.append((block[0], block[1], block[2], block[3], block[4], None))

        self.executemany("INSERT INTO blocks VALUES (?,?,?,?,?,?)", newBlocks)

        self.commit()

    def storeVoters(self, voters, share):
        newVoters=[]

        for voter in voters:
            self.cursor.execute("SELECT address FROM voters WHERE address = ?", (voter[0],))

            if self.cursor.fetchone() is None:
                newVoters.append((voter[0], 0, 0, share))

        self.executemany("INSERT INTO voters VALUES (?,?,?,?)", newVoters)

        self.commit()
        
    def storeRewards(self, delegate):
        newRewards=[]

        for d in delegate:
            self.cursor.execute("SELECT address FROM delegate_rewards WHERE address = ?", (d,))

            if self.cursor.fetchone() is None:
                newRewards.append((d, 0, 0))

        self.executemany("INSERT INTO delegate_rewards VALUES (?,?,?)", newRewards)

        self.commit()
        
    def storeTransactions(self, tx):
        newTransactions=[]
        
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for t in tx:
            self.cursor.execute("SELECT id FROM transactions WHERE id = ?", (t[2],))
            
            if self.cursor.fetchone() is None:
                newTransactions.append((t[0], t[1], t[2], ts))
                
        self.executemany("INSERT INTO transactions VALUES (?,?,?,?)", newTransactions)
        
        self.commit()
        
    def markAsProcessed(self, block):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("UPDATE blocks SET processed_at = '{0}' WHERE height = '{1}'".format(ts, block))
        self.commit()

    def blocks(self):
        return self.cursor.execute("SELECT * FROM blocks")

    def processedBlocks(self):
        return self.cursor.execute("SELECT * FROM blocks WHERE processed_at NOT NULL")

    def unprocessedBlocks(self):
        return self.cursor.execute("SELECT * FROM blocks WHERE processed_at IS NULL ORDER BY height")
    
    def stagedArkPayment(self):
        return self.cursor.execute("SELECT rowid, * FROM staging WHERE processed_at IS NULL LIMIT 40")

    def stagedLiskPayment(self):
        return self.cursor.execute("SELECT rowid, * FROM staging WHERE processed_at IS NULL LIMIT 20")

    def processStagedPayment(self, rows):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')		
        for i in rows:
            self.cursor.execute("UPDATE staging SET processed_at = '{0}' WHERE rowid = {1}".format(ts, i))	

        self.commit()
	
    def deleteStagedPayment(self):
        self.cursor.execute("DELETE FROM staging WHERE processed_at NOT NULL")
        self.commit()

    def voters(self):
        return self.cursor.execute("SELECT * FROM voters ORDER BY u_balance DESC")
    
    def rewards(self):
        return self.cursor.execute("SELECT * FROM delegate_rewards")

    def transactions(self):
        return self.cursor.execute("SELECT * FROM transactions")

    def updateVoterBalance(self, address, balance):
        self.cursor.execute("UPDATE voters SET u_balance = u_balance + {0} WHERE address = '{1}'".format(balance, address))
        self.commit()

    def updateVoterShare(self, address, share):
        self.cursor.execute("UPDATE voters SET share = {0} WHERE address = '{1}'".format(share, address))
        self.commit()

    def getVoterShare(self, address):
        return self.cursor.execute("SELECT share FROM voters WHERE address = '{0}'".format(address))
        
    def updateDelegateBalance(self, address, balance):
        self.cursor.execute("UPDATE delegate_rewards SET u_balance = u_balance + {0} WHERE address = '{1}'".format(balance, address))
        self.commit()
        
    def updateVoterPaidBalance (self, address):
        self.cursor.execute("UPDATE voters SET p_balance = p_balance + u_balance WHERE address = '{0}'".format(address))
        self.cursor.execute("UPDATE voters SET u_balance = u_balance - u_balance WHERE address = '{0}'".format(address))
        self.commit()
        
    def updateDelegatePaidBalance (self, address, amount):
        self.cursor.execute("UPDATE delegate_rewards SET p_balance = p_balance + {0} WHERE address = '{1}'".format(amount, address))
        self.cursor.execute("UPDATE delegate_rewards SET u_balance = u_balance - {0} WHERE address = '{1}'".format(amount, address))
        self.commit()
