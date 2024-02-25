import pandas as pd

def getAccessToken():
    tokenFile = open("../config/access_token.txt", "r")
    token = tokenFile.readline().replace("\n", "")
    tokenFile.close()
    return token

def instrumentLookup(symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        # get dump of all NSE instruments
        instrument_df = pd.read_json('../instruments/NSE.json')
        return instrument_df[instrument_df.trading_symbol == symbol].instrument_key.values[0]
    except:
        return -1
