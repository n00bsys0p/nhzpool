#!/usr/bin/env python

# author: brendan@shellshockcomputer.com.au

import ConfigParser
from bottle import route, install, run, template, static_file, response, PasteServer#, debug
from bottle_sqlite import SQLitePlugin
import json
import urllib
import urllib2
import datetime

config = ConfigParser.RawConfigParser()
config.read('config.ini')

install(SQLitePlugin(dbfile=(config.get("pool", "database"))))

@route('/api/btime')
def blocktime():
    response.headers['Cache-Control'] = 'public, max-age=100'
    payload = {
        'requestType': 'getForging',
        'secretPhrase': config.get("pool", "poolphrase")
    }
    opener = urllib2.build_opener(urllib2.HTTPHandler())
    data = urllib.urlencode(payload)
    forging = json.loads(opener.open(config.get("pool", "nhzhost")+'/nhz', data=data).read())
    getdl = forging["deadline"]
    dl = str(datetime.timedelta(seconds=getdl))
    return {'blocktime': dl}

@route('/api/accounts')
def apiaccounts(db):
    response.headers['Cache-Control'] = 'public, max-age=3600'
    getlastheight = db.execute("SELECT height FROM blocks ORDER BY timestamp DESC").fetchone()
    lastheight = getlastheight[0]
    c = db.execute("SELECT ars, heightfrom, heightto, amount FROM leased WHERE heightto > %s" % (lastheight)).fetchall()
    accounts = json.dumps( [dict(ix) for ix in c], separators=(',',':'))   
    return accounts

@route('/api/blocks')
def apiblocks(db):
    response.headers['Cache-Control'] = 'public, max-age=1800'
    c = db.execute("SELECT height, timestamp, totalfee FROM blocks WHERE totalfee > 0 ORDER BY timestamp DESC").fetchall()
    blocks = json.dumps( [dict(ix) for ix in c], separators=(',',':'))
    return blocks

@route('/api/leased')
def apileased():
    getaccounts = json.loads(urllib2.urlopen(config.get("pool", "nhzhost")+"/nhz?requestType=getAccount&account="+config.get("pool", "poolaccount")).read())
    leasebal = getaccounts['effectiveBalanceNHZ']
    return {'blocktime': leasebal}

@route('/api/payouts')
def apipayouts(db):
    response.headers['Cache-Control'] = 'public, max-age=3600'
    c = db.execute("SELECT account, fee, payment FROM payouts DESC").fetchall()
    pays = json.dumps( [dict(ix) for ix in c], separators=(',',':'))
    return pays

@route('/api/paid')
def apipaid(db):
    response.headers['Cache-Control'] = 'public, max-age=3600'
    c = db.execute("SELECT blocktime, account, percentage, amount FROM accounts WHERE paid>0 ORDER BY blocktime DESC").fetchall()   
    pays = json.dumps( [dict(ix) for ix in c], separators=(',',':'))
    return pays

@route('/api/unpaid')
def apiunpaid(db):
    response.headers['Cache-Control'] = 'public, max-age=3600'
    c = db.execute("SELECT blocktime, account, percentage, amount FROM accounts WHERE paid=0 ORDER BY blocktime DESC").fetchall()   
    pays = json.dumps( [dict(ix) for ix in c], separators=(',',':'))
    return pays
    
            
@route('/')
def default(db):
    response.headers['Cache-Control'] = 'public, max-age=3600'
    poolaccount = config.get("pool", "poolaccountrs")
    poolfee = config.get("pool", "feePercent")
    db.text_factory = str
    d = db.execute("SELECT height, timestamp, totalfee FROM blocks ORDER BY timestamp DESC limit 1")
    getlastheight = d.fetchone()
    lastheight = getlastheight[0]
    c = db.execute("SELECT ars, heightto, amount FROM leased WHERE heightto > %s" % (lastheight))
    result = c.fetchall()
    e = db.execute("SELECT height, timestamp, totalfee FROM blocks ORDER BY timestamp DESC limit 5")
    block = e.fetchall()
    getaccounts = json.loads(urllib2.urlopen(config.get("pool", "nhzhost")+"/nhz?requestType=getAccount&account="+config.get("pool", "poolaccount")).read())
    leasebal = getaccounts['effectiveBalanceNHZ'] 
    output = template('default', pa=poolaccount, fee=poolfee, rows=result, blocks=block, nhzb=leasebal)
    return output

@route('/static/:path#.+#', name='static')
def static(path):
    response.headers['Cache-Control'] = 'public, max-age=2592000'
    return static_file(path, root='static')

@route('/favicon.ico')
def get_favicon():
    response.headers['Cache-Control'] = 'public, max-age=2592000'
    return static('favicon.ico')

@route('/accounts')
def accounts(db):
    response.headers['Cache-Control'] = 'public, max-age=43200'   
    output = template('accounts')
    return output

@route('/blocks')
def blocks(db):
    response.headers['Cache-Control'] = 'public, max-age=43200'
    output = template('blocks')
    return output

@route('/payouts')
def payouts(db):
    response.headers['Cache-Control'] = 'public, max-age=43200'   
    output = template('payouts')
    return output

@route('/unpaid')
def unpaid(db):
    response.headers['Cache-Control'] = 'public, max-age=43200'
    output = template('unpaid')
    return output

@route('/paid')
def paid(db):
    response.headers['Cache-Control'] = 'public, max-age=43200'   
    output = template('paid')
    return output
	
#debug(True)    
run(server=PasteServer, port=8810, host='0.0.0.0')
