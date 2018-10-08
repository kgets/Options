# -*- coding: utf-8 -*-
"""
Created on Sun Aug  5 09:49:11 2018

@author: Kelly G
"""

import pandas as pd
import json
import requests
import datetime


##https://query2.finance.yahoo.com/v7/finance/options/slv/
##https://finance.yahoo.com/quote/SLV/options?date=1579219200
    
## < Functions >

def requestExpirations(ticker):
    url = 'https://query2.finance.yahoo.com/v7/finance/options/'+ticker
    r = requests.get(url)
    if r.json()['optionChain']['error'] is None:
        resp = r.json()['optionChain']['result'][0]['expirationDates']
    else:
        raise Exception('Error With Your Request!')
    return resp

def requestQuote(ticker):
    url = 'https://query2.finance.yahoo.com/v7/finance/options/'+ticker
    r = requests.get(url)
    if r.json()['optionChain']['error'] is None:
        resp = r.json()['optionChain']['result'][0]['quote']
    else:
        raise Exception('Error With Your Request!')
    return resp

def requestOptChain(ticker,calls):
    date = datetime.date.today()
    if calls:
        optType = 'calls'
    else:
        optType = 'puts'
    url = 'https://query2.finance.yahoo.com/v7/finance/options/'+ticker
    strikeList = requestExpirations(ticker)
    returnDf = None
    for unixDate in strikeList:
        r = requests.get(url+'?date='+str(unixDate))
        if returnDf is None:
            returnDf = pd.read_json(json.dumps(r.json()['optionChain']['result'][0]['options'][0][optType]))
        else:
            temp = pd.read_json(json.dumps(r.json()['optionChain']['result'][0]['options'][0][optType]))
            returnDf = pd.concat([returnDf,temp], axis=0, ignore_index=1)
    #add DTE column
    returnDf['DTE'] = (returnDf['expiration'].apply(lambda x: datetime.datetime.fromtimestamp(int(x))+datetime.timedelta(days=1))-date).apply(lambda x: x.days)
    #add logrithmic mid price
    returnDf['logMidPrice'] = round((returnDf['ask']*returnDf['bid'])**0.5,2)
    #readable Dates
    returnDf['expiration'] = returnDf['expiration'].apply(lambda x: (datetime.datetime.fromtimestamp(int(x))+datetime.timedelta(days=1)).strftime('%m-%d-%Y'))
    #get stock price
    quote = r.json()['optionChain']['result'][0]['quote']
    price = round((quote['bid']*quote['ask'])**0.5 , 2)
    #add annualized interest column
    returnDf['Annualized Interest'] = round(((1+(returnDf['logMidPrice']/(returnDf['strike']-returnDf['logMidPrice'])))**(1/(returnDf['DTE']/365))-1)*100,2)
    #drop unneeded columns
    returnDf.drop(['currency','percentChange','contractSize','inTheMoney','lastPrice','lastTradeDate','contractSymbol','change'], axis=1, inplace=True)
    return returnDf
        
## < Main >


ticker = 'slv'
calls = True
optChain = requestOptChain(ticker,calls)
quote = requestQuote(ticker)
price = round((quote['bid']+quote['ask'])/2,2)
#DTE = optChain['expiration'].apply(lambda x: datetime.datetime.strptime(x, '%m-%d-%Y') - date).days
#optChain['Annualized Interest'] = (1+(optChain['logMidPrice']/(optChain['strike']-optChain['logMidPrice'])))**(1/(DTE/365))-1
