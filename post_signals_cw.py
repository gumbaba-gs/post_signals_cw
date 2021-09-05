import requests
import json
import re
import csv 
import pandas as pd
import ccxt
import psycopg2
from config import config

binance = ccxt.binance({
    "options": {"defaultType": "future"},
    "timeout": 30000,
    "apiKey":"CACu04z8RUsFfVcMk8S0PcTw9HzhMYJ8gkJRzXZghUOSHovuhfJO3xV7em9XnhoJ",
    "secret": "IgoyG4X3m21Uixr9TjZhoySDB55LbBkY5N6ZjVA6GpTr8XBC5HyuzP36DKYnfTE2",
    "enableRateLimit": True,
})

def connect(symbol):
    symbol_pair_list = []
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
		
        # create a cursor
        cur = conn.cursor()
        
	# execute a statement
        #symbol = 'LUNA'
        symbol_pair = symbol + 'USDT'
        strat_name = 'CW_' + symbol + 'L'
        category = symbol.lower() + "_cw_long"
        cur.execute("select symbol from public.strategy;")
        db_symbol_pairs =  cur.fetchall()
        for db_symbol_pair in db_symbol_pairs:
            symbol_pair_list.append(re.search('\(\'(.*)\'', str(db_symbol_pair))[1])
        if symbol_pair not in symbol_pair_list:
            print(symbol_pair_list)
            cur.execute("INSERT INTO public.strategy (name, position_type, exchange_type, symbol, version, status, updated_time, created_time, exchange_id) VALUES(%s, 'LONG', 'FUTURES', %s, 0, 'ACTIVE', '2021-06-24 18:00:00.000', '2021-06-24 18:00:00.000', 4) RETURNING id;",(strat_name,symbol_pair))
            # display the PostgreSQL database server version
            start_id = cur.fetchone()[0]       
            conn.commit()
            cur.execute("INSERT INTO public.strategy_conditions (strategy_id, name, time_frame, last_observed, category, condition_group, created_time, sequence, version, condition_sub_group) VALUES(%s, 'buy_long', 1, 1, %s, 'OPEN', '2021-06-24 18:00:00.000', 0, 0, 0);",(start_id,category))
            cur.execute("INSERT INTO public.strategy_conditions (strategy_id, name, time_frame, last_observed, category, condition_group, created_time, sequence, version, condition_sub_group) VALUES(%s, 'sell_long', 1, 1, %s, 'CLOSE', '2021-06-24 18:00:00.000', 0, 0, 0);",(start_id,category))
            conn.commit()
            print(start_id)
	# close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

def option_settings(symbol, leverage):
    symbol_pair = symbol.upper() + "USDT"
    print(symbol_pair)
    print(leverage)
    binance.fapiPrivate_post_leverage({
        "symbol": symbol_pair,
        "leverage": leverage,
    })  
    try:
        binance.fapiPrivatePostMarginType ({
            "symbol": symbol_pair,
            "marginType": 'ISOLATED',
        })
    except:
        pass

def post_singal(position,symbol,price):
    
    webhook_url = "https://irwrfpdk35.execute-api.ap-southeast-2.amazonaws.com/prod/v1/enqueue"

    data = { 
        "name": position + "_long", 
        "price": price, 
        "contracts": (200/float(price)),
        "symbol": symbol.upper() + "USDT", 
        "market": "USDT", 
        "category": symbol.lower() + "_cw_long",
        "timeFrame": 1, 
        "exchange": "BinanceFutures"
    }

    j = requests.post(webhook_url,data=json.dumps(data), headers={'Content-Type': 'application/json'})

def retrieve_messages():
    data = []
    headers = {
        "authorization": "NzQ4ODA3NTQwMDc4NDExODEy.YSEB-w.0lG7KI_jBQaZI4CBa2DLrTJGnrY"
    }
    r = requests.get(
        f"https://discord.com/api/v8/channels/421039487729008650/messages", headers=headers)
    jsonn = json.loads(r.text)
    csvdata = pd.read_csv("signals.csv")
    ids = csvdata['id'].tolist()
    for value in jsonn:
        if int(value['id']) not in ids:
            print(value['id'])
            leverage = re.search('Leverage (.*)x', value['content'])[1]
            symbol = re.search('Buy #(.*)\/', value['content'])[1]
            price = float((re.search('Buy Price: (.*)\s', value['content'])[1]).strip())
            data = [value['id'], re.search('Buy #(.*)\/', value['content'])[1], (re.search('Buy Price: (.*)\s', value['content'])[1]).strip(), value['timestamp'],'open']
            connect(symbol)
            option_settings(symbol,leverage)
            post_singal('buy',symbol, price)
            with open('signals.csv', 'a', encoding='UTF8') as f:
                writer = csv.writer(f)
                writer.writerow(data)

def check_signal_staus():
    csvdata = pd.read_csv("signals.csv")
    variabletomatch="open"
    for idx,row in csvdata.iterrows():   
        tomatch=row["position"]
        if tomatch==variabletomatch:
            print(row["symbol-pair"])
            entry_price = row["price"]
            current_price = binance.fetch_ticker(row["symbol-pair"] + "/USDT")['close']
            gain = ((current_price - entry_price) / entry_price) * 100 
            print('symbol:',row["symbol-pair"] + "/USDT", 'current_price:', current_price, 'gain:', gain)
            if float(gain) >= 0.5:
                csvdata.replace('open','close',inplace=True)
                post_singal('sell',row["symbol-pair"], current_price)
    #os.remove("signals.csv")
    csvdata.to_csv("signals.csv", index=False)

retrieve_messages()
check_signal_staus()