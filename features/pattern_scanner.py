# -*- coding: utf-8 -*-
"""
Zerodha Kite Connect - candlestick pattern scanner

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""

import pandas as pd
import datetime as dt
import os
import time
import numpy as np
import utils as utils
import Symbols as sb
import upstox_client
from upstox_client.rest import ApiException

cwd = os.getcwd()

configuration = upstox_client.Configuration()
api_version = 'v2'

# generate trading session
access_token = utils.getAccessToken()
configuration.access_token = access_token
api_instance = upstox_client.HistoryApi()


def fetchOHLC(ticker, interval, duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = utils.instrumentLookup(ticker)
    api_response = api_instance.get_historical_candle_data(instrument, 'month', dt.date.today(), api_version)
    data = pd.DataFrame(api_response.data.candles)
    data.columns =['date', 'open', 'high', 'low', 'close', 'volume', 'test']
    data.set_index("date", inplace=True)
    return data


def doji(ohlc_df):
    """returns dataframe with doji candle column"""
    df = ohlc_df.copy()
    avg_candle_size = abs(df["close"] - df["open"]).median()
    df["doji"] = abs(df["close"] - df["open"]) <= (0.05 * avg_candle_size)
    return df


def maru_bozu(ohlc_df):
    """returns dataframe with maru bozu candle column"""
    df = ohlc_df.copy()
    avg_candle_size = abs(df["close"] - df["open"]).median()
    df["h-c"] = df["high"]-df["close"]
    df["l-o"] = df["low"]-df["open"]
    df["h-o"] = df["high"]-df["open"]
    df["l-c"] = df["low"]-df["close"]
    df["maru_bozu"] = np.where((df["close"] - df["open"] > 2*avg_candle_size) &
                               (df[["h-c", "l-o"]].max(axis=1) < 0.005 *
                                avg_candle_size), "maru_bozu_green",
                               np.where((df["open"] - df["close"] > 2*avg_candle_size) &
                               (abs(df[["h-o", "l-c"]]).max(axis=1) < 0.005*avg_candle_size), "maru_bozu_red", False))
    df.drop(["h-c", "l-o", "h-o", "l-c"], axis=1, inplace=True)
    return df


def hammer(ohlc_df):
    """returns dataframe with hammer candle column"""
    df = ohlc_df.copy()
    df["hammer"] = (((df["high"] - df["low"]) > 3*(df["open"] - df["close"])) &
                    ((df["close"] - df["low"])/(.001 + df["high"] - df["low"]) > 0.6) &
                    ((df["open"] - df["low"])/(.001 + df["high"] - df["low"]) > 0.6)) & \
                   (abs(df["close"] - df["open"]) >
                    0.1 * (df["high"] - df["low"]))
    return df


def shooting_star(ohlc_df):
    """returns dataframe with shooting star candle column"""
    df = ohlc_df.copy()
    df["sstar"] = (((df["high"] - df["low"]) > 3*(df["open"] - df["close"])) &
                   ((df["high"] - df["close"])/(.001 + df["high"] - df["low"]) > 0.6) &
                   ((df["high"] - df["open"])/(.001 + df["high"] - df["low"]) > 0.6)) & \
        (abs(df["close"] - df["open"]) > 0.1 * (df["high"] - df["low"]))
    return df


def levels(ohlc_day):
    """returns pivot point and support/resistance levels"""
    high = round(ohlc_day["high"][-1], 2)
    low = round(ohlc_day["low"][-1], 2)
    close = round(ohlc_day["close"][-1], 2)
    pivot = round((high + low + close)/3, 2)
    r1 = round((2*pivot - low), 2)
    r2 = round((pivot + (high - low)), 2)
    r3 = round((high + 2*(pivot - low)), 2)
    s1 = round((2*pivot - high), 2)
    s2 = round((pivot - (high - low)), 2)
    s3 = round((low - 2*(high - pivot)), 2)
    return (pivot, r1, r2, r3, s1, s2, s3)


def trend(ohlc_df, n):
    "function to assess the trend by analyzing each candle"
    df = ohlc_df.copy()
    df["up"] = np.where(df["low"] >= df["low"].shift(1), 1, 0)
    df["dn"] = np.where(df["high"] <= df["high"].shift(1), 1, 0)
    if df["close"][-1] > df["open"][-1]:
        if df["up"][-1*n:].sum() >= 0.7*n:
            return "uptrend"
    elif df["open"][-1] > df["close"][-1]:
        if df["dn"][-1*n:].sum() >= 0.7*n:
            return "downtrend"
    else:
        return None


def res_sup(ohlc_df, ohlc_day):
    """calculates closest resistance and support levels for a given candle"""
    level = ((ohlc_df["close"][-1] + ohlc_df["open"][-1]) /
             2 + (ohlc_df["high"][-1] + ohlc_df["low"][-1])/2)/2
    p, r1, r2, r3, s1, s2, s3 = levels(ohlc_day)
    l_r1 = level-r1
    l_r2 = level-r2
    l_r3 = level-r3
    l_p = level-p
    l_s1 = level-s1
    l_s2 = level-s2
    l_s3 = level-s3
    lev_ser = pd.Series([l_p, l_r1, l_r2, l_r3, l_s1, l_s2, l_s3], index=[
                        "p", "r1", "r2", "r3", "s1", "s2", "s3"])
    sup = lev_ser[lev_ser > 0].idxmin()
    res = lev_ser[lev_ser < 0].idxmax()
    return (eval('{}'.format(res)), eval('{}'.format(sup)))


def candle_type(ohlc_df):
    """returns the candle type of the last candle of an OHLC DF"""
    candle = None
    if doji(ohlc_df)["doji"][-1] == True:
        candle = "doji"
    if maru_bozu(ohlc_df)["maru_bozu"][-1] == "maru_bozu_green":
        candle = "maru_bozu_green"
    if maru_bozu(ohlc_df)["maru_bozu"][-1] == "maru_bozu_red":
        candle = "maru_bozu_red"
    if shooting_star(ohlc_df)["sstar"][-1] == True:
        candle = "shooting_star"
    if hammer(ohlc_df)["hammer"][-1] == True:
        candle = "hammer"
    print("candle", ": ", candle)
    return candle


def candle_pattern(ticker, ohlc_df, ohlc_day):
    """returns the candle pattern identified"""
    pattern = None
    signi = "low"
    action = ""
    buy_sell = ""
    avg_candle_size = abs(ohlc_df["close"] - ohlc_df["open"]).median()
    sup, res = res_sup(ohlc_df, ohlc_day)

    if (sup - 1.5*avg_candle_size) < ohlc_df["close"][-1] < (sup + 1.5*avg_candle_size):
        signi = "HIGH"

    if (res - 1.5*avg_candle_size) < ohlc_df["close"][-1] < (res + 1.5*avg_candle_size):
        signi = "HIGH"

    if candle_type(ohlc_df) == 'doji' \
            and ohlc_df["close"][-1] > ohlc_df["close"][-2] \
            and ohlc_df["close"][-1] > ohlc_df["open"][-1]:
        pattern = "doji_bullish"
        action = "Buy CE - Price may increase"
        buy_sell = "buy"

    if candle_type(ohlc_df) == 'doji' \
            and ohlc_df["close"][-1] < ohlc_df["close"][-2] \
            and ohlc_df["close"][-1] < ohlc_df["open"][-1]:
        pattern = "doji_bearish"
        action = "Buy PE - Price may decrease"
        buy_sell = "sell"

    if candle_type(ohlc_df) == "maru_bozu_green":
        pattern = "maru_bozu_bullish"
        action = "Buy CE - Price may increase"
        buy_sell = "buy"

    if candle_type(ohlc_df) == "maru_bozu_red":
        pattern = "maru_bozu_bearish"
        action = "Buy PE - Price may decrease"
        buy_sell = "sell"

    if trend(ohlc_df.iloc[:-1, :], 7) == "uptrend" and candle_type(ohlc_df) == "hammer":
        pattern = "hanging_man_bearish"
        action = "Buy PE - Price may decrease"
        buy_sell = "sell"

    if trend(ohlc_df.iloc[:-1, :], 7) == "downtrend" and candle_type(ohlc_df) == "hammer":
        pattern = "hammer_bullish"
        action = "Buy CE - Price may increase"
        buy_sell = "buy"

    if trend(ohlc_df.iloc[:-1, :], 7) == "uptrend" and candle_type(ohlc_df) == "shooting_star":
        pattern = "shooting_star_bearish"
        action = "Buy PE - Price may decrease"
        buy_sell = "sell"

    if trend(ohlc_df.iloc[:-1, :], 7) == "uptrend" \
            and candle_type(ohlc_df) == "doji" \
            and ohlc_df["high"][-1] < ohlc_df["close"][-2] \
            and ohlc_df["low"][-1] > ohlc_df["open"][-2]:
        pattern = "harami_cross_bearish"
        action = "Buy PE - Price may decrease"
        buy_sell = "sell"

    if trend(ohlc_df.iloc[:-1, :], 7) == "downtrend" \
            and candle_type(ohlc_df) == "doji" \
            and ohlc_df["high"][-1] < ohlc_df["open"][-2] \
            and ohlc_df["low"][-1] > ohlc_df["close"][-2]:
        pattern = "harami_cross_bullish"
        action = "Buy CE - Price may increase"
        buy_sell = "buy"

    if trend(ohlc_df.iloc[:-1, :], 7) == "uptrend" \
            and candle_type(ohlc_df) != "doji" \
            and ohlc_df["open"][-1] > ohlc_df["high"][-2] \
            and ohlc_df["close"][-1] < ohlc_df["low"][-2]:
        pattern = "engulfing_bearish"
        action = "Buy PE - Price may decrease"
        buy_sell = "sell"

    if trend(ohlc_df.iloc[:-1, :], 7) == "downtrend" \
            and candle_type(ohlc_df) != "doji" \
            and ohlc_df["close"][-1] > ohlc_df["high"][-2] \
            and ohlc_df["open"][-1] < ohlc_df["low"][-2]:
        pattern = "engulfing_bullish"
        action = "Buy CE - Price may increase"
        buy_sell = "buy"

    if pattern != None and signi == "HIGH":
        print("{} :: Significance - {}, Pattern - {}".format(ticker, signi, pattern))
        #print("---> Action:: {}".format(action))
        print("---> Buy or Sell:: {}".format(buy_sell))

        """ qty = utils.calculateQty(ohlc_df["close"][-1])
        if qty > 0:
            placeMKOrder(ticker, buy_sell, qty) """

    return "Significance - {}, Pattern - {}".format(signi, pattern)


def placeMKOrder(symbol, buy_sell, quantity):
    # Place an intraday stop loss order on NSE - handles market orders converted to limit orders

    # Check no open quantity for this symbol
    """ canProceed = utils.validateSymbol(symbol)
    if canProceed == True:
        utils.placeMarketOrder(symbol, buy_sell, quantity)
    else:
        print("Symbol already exists with open quantity, not placing orders now") """


##############################################################################################
tickers = sb.indices()

def main():
    for ticker in tickers:
        try:
            ohlc = fetchOHLC(ticker, '5minute', 5)
            ohlc_day = fetchOHLC(ticker, 'day', 30)
            ohlc_day = ohlc_day.iloc[:-1, :]
            cp = candle_pattern(ticker, ohlc, ohlc_day)
            print(ticker, ": ", cp)
        except:
            print("skipping for ", ticker)


# Continuous execution
starttime = time.time()
# 60 seconds times 60 meaning the script will run for 1 hr
timeout = time.time() + 60*60*1
while time.time() <= timeout:
    try:
        print("**********************{}**************************".format(
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
        main()
        print("*******************************************************************")
        # 300 second interval between each new execution
        time.sleep(300 - ((time.time() - starttime) % 300.0))
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        exit()
