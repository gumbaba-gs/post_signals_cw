import requests
import json

price = 47680
position = "long" # "long" or "short"
trade_type = "sell"
symbol = "BTC"
exchange = "ByBitFutures" # BinanceFutures or ByBitFutures"
market = "USDT" # USDT or USD

webhook_url = "https://irwrfpdk35.execute-api.ap-southeast-2.amazonaws.com/prod/v1/enqueue"

data = { 
    "name": trade_type + "_" + position, 
    "price": price, 
    "contracts": 0,
    "symbol": symbol.upper() + "USDT", 
    "market": market, 
    "category": symbol.lower() + "_vu_" + position,
    "timeFrame": 6, 
    "exchange": exchange,
    "TVStrategyVersion": 15
}

r = requests.post(webhook_url,data=json.dumps(data), headers={'Content-Type': 'application/json'})