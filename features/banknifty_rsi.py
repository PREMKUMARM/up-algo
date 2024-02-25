#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 23:41:42 2023

@author: pkumarm2
"""
from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os
import numpy as np
import upstox_client
from upstox_client.rest import ApiException
import pandas as pd

cwd = os.getcwd()

# Configure OAuth2 access token for authorization: OAUTH2
configuration = upstox_client.Configuration()
api_version = 'v2'

file1 = open("./config/access_token.txt", "r")
token = file1.readline().replace("\n", "")
# generate trading session

configuration.access_token = token
file1.close()

# get dump of all NSE instruments
instrument_df = pd.read_json('./instruments/NSE.json')
api_instance = upstox_client.HistoryApi()


def instrumentLookup(instrument_df, symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.trading_symbol == symbol].instrument_key.values[0]
    except:
        return -1


def fetchOHLC(ticker, interval, duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df, ticker)
    api_response = api_instance.get_historical_candle_data(instrument, 'month', dt.date.today(), api_version)
    data = pd.DataFrame(api_response.data.candles)
    data.columns =['date', 'open', 'high', 'low', 'close', 'volume', 'test']
    #print(data)
    data.set_index("date", inplace=True)
    return data


def rsi(df, n):
    "function to calculate RSI"
    delta = df["close"].diff().dropna()
    u = delta * 0
    d = u.copy()
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]
    u[u.index[n-1]] = np.mean(u[:n])  # first value is average of gains
    u = u.drop(u.index[:(n-1)])
    d[d.index[n-1]] = np.mean(d[:n])  # first value is average of losses
    d = d.drop(d.index[:(n-1)])
    rs = u.ewm(com=n, min_periods=n).mean()/d.ewm(com=n, min_periods=n).mean()
    return 100 - 100 / (1+rs)


ohlc = fetchOHLC("BANKNIFTY", '1minute', 15)
rsi = rsi(ohlc, 14)
print(rsi)
