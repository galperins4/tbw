import psycopg2

class ArkDB:
    def __init__(self, db, u, pw, pk):
        self.connection = psycopg2.connect(
            dbname = db,
            user = u,
            password= pw,
            host='localhost',
            port='5432'
        )
		 
        self.PublicKey = pk
        self.BlockPublicKey = '\\x' + self.PublicKey
		
        self.cursor=self.connection.cursor()

    def blocks(self, i='no'):
        
        #if i is yes, first run grab every block forged for history
        if i == 'yes':
            try:
                self.cursor.execute("""SELECT "id","timestamp","reward","totalFee","height" FROM blocks WHERE "generatorPublicKey" = '{0}' ORDER BY "height" DESC""".format(self.BlockPublicKey))
                return self.cursor.fetchall()
            except Exception as e:
                print(e)
                
        #else just grab last 50 for normal processing
        else:
            try:
                self.cursor.execute("""SELECT "id","timestamp","reward","totalFee","height" FROM blocks WHERE "generatorPublicKey" = '{0}' ORDER BY "height" DESC LIMIT 50""".format(self.BlockPublicKey))
                return self.cursor.fetchall()
            except Exception as e:
                print(e)

    def listen_transactions(self, row):
        try:
            self.cursor.execute("""SELECT "id","senderId", "amount", "fee", "vendorField" FROM transactions WHERE "rowId" > {0} ORDER BY "rowId" DESC""".format(row))
            return self.cursor.fetchall()
        except Exception as e:
            print(e)	    
	    
    def last_transaction(self):
        try:
            self.cursor.execute("""SELECT "id","rowId" FROM transactions ORDER BY "rowId" DESC LIMIT 1""")
            return self.cursor.fetchall()
        except Exception as e:
            print(e)	 
		
    def voters(self):
        try:
            self.cursor.execute("""SELECT "accountId" FROM mem_accounts2delegates WHERE "dependentId" = '{0}'""".format(self.PublicKey))

            voters=[]

            for addr in self.cursor.fetchall():
                self.cursor.execute("""SELECT "address","balance" FROM mem_accounts WHERE "address" = '{0}'""".format(addr[0]))

                voters.append(self.cursor.fetchone())

            return voters
        except Exception as e:
            print(e)

    def votes(self, voters):
        totalVotes=0

        for voter in voters:
            totalVotes+=voter[1]

        return totalVotes
