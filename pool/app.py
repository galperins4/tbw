from flask import Flask, render_template
import requests
from snek.db.snek import SnekDB



def parse_pool():

    with open('pool.json') as data_file:
        data = json.load(data_file)
        
    with open('config/networks.json') as network_file:
        network = json.load(network_file)

    return data, network

app = Flask(__name__)

@app.route('/')
def index():    
    url = 'http://:4002/api/delegates'
    r = requests.get(url)

    s = {}

    #get everything except for voters
    for i in r.json()['delegates']:
        if i['username'] == 'ark_galp':
            pubKey = i['publicKey']
            s['forged'] = i['producedblocks']
            s['missed'] = i['missedblocks']
            s['rank'] = i['rate']
            s['productivity'] = i['productivity']
            if s['rank'] <= 51:
                s['forging'] = 'Forging
            else:
                s['forging'] = 'Standby'

    url2 = 'http://:4002/api/delegates/voters'
    params = {'publicKey': pubKey}

    r2 = requests.get(url2, params = params)
    s['votes'] = len(r2.json()['accounts'])

    voter_data = snekdb.voters().fetchall()
    
    #rows = [['addr1',0,345], ['addr2',200,300],['addr2',200,300],['addr2',200,300],['addr2',200,300],['addr2',200,300],['addr2',200,300],['addr2',200,300],['addr2',200,300], ['addr2',200,300], ['addr2',200,300], ['addr2',200,300], ['addr2',200,300]]
    
    return render_template('index.html', node=s, row=voter_data)

@app.route('/payments')
def payments():
    
    data = snekdb.transactions().fetchall()
    tx_data=[]
    for i in data:
        l = [i[0], int(i[1]), i[2], i[3]]
        tx_data.append(l)
    
    
    '''
    rows = [['addr1',100000000000,'asdlkfjasdlfkj', '01-01-01'],
            ['addr2',200000000000,'asdlkfjasdlfkj', '01-01-01'],
            ['addr3',300000000000,'asdlkfjasdlfkj', '01-01-01'],
            ['addr4',400000000000,'asdlkfjasdlfkj', '01-01-01']]
    '''
    return render_template('payments.html', row=tx_data)

if __name__ == '__main__':
    #data, network = parse_config() 
    snekdb = SnekDB("")
    #app.run()
    app.run(host='')
