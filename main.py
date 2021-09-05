import websocket
import json

def send_json_requests(ws, request):
    ws.send(json.dumps(request))

def receive_json_response(ws):
    response = ws.recv()
    if response:
        return json.loads(response)

ws = websocket.WebSocket()
ws.connect("wss://gateway.discord.gg/?v=6&encoding=json")
heartbeat_interval = receive_json_response(ws)["d"]["heartbeat_interval"]

token = "NzQ4ODA3NTQwMDc4NDExODEy.YSEB-w.0lG7KI_jBQaZI4CBa2DLrTJGnrY"

payload = {
    "op": 1,
    "d": {
        "token": token,
        "intents": 513,
        "properties": {
            "$os": 'linux',
            "$browser": 'chrome',
            "device": 'pc'
        }
    }
}

send_json_requests(ws,payload)

while True:
    event = receive_json_response(ws)
    try:
        # content = event['d']['content']
        # print({content})
        print(event)
    except:
        pass