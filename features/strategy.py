from __future__ import print_function
import time
import upstox_client
from upstox_client.rest import ApiException
from pprint import pprint
import logging
import sys

# Configure OAuth2 access token for authorization: OAUTH2
configuration = upstox_client.Configuration()

file1 = open("./config/access_token.txt", "r")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler('./logs/logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)


logger.addHandler(file_handler)
#logger.addHandler(stdout_handler)
token = file1.readline().replace("\n", "")
#logger.info(token)
configuration.access_token = token
file1.close() 
# create an instance of the API class
# create an instance of the API class
api_instance = upstox_client.MarketQuoteApi(upstox_client.ApiClient(configuration))
symbol = 'NSE_INDEX|Nifty Bank' # str | Comma separated list of symbols
interval = '1d' # str | Interval to get ohlc data
api_version = 'v2' # str | API Version Header

try:
    # Market quotes and instruments - OHLC quotes
    api_response = api_instance.get_market_quote_ohlc(symbol, interval, api_version)
    logger.info(api_response)

except ApiException as e:
    logger.error("Exception when calling MarketQuoteApi->get_market_quote_ohlc: %s\n" % e)
