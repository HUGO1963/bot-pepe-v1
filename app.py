import time, threading, os, ccxt, pandas as pd
from flask import Flask
app = Flask(__name__)

# --- CONFIGURACIÓN COINEX ---
API_KEY = '0CD4EAE1BBAA4628B65AAB8660D8278F'
API_SECRET = '4C7C6BF5D2A82687085E95C28A8A548237800D11FDF4A4C5'

exchange = ccxt.coinex({'apiKey': API_KEY, 'secret': API_SECRET, 'enableRateLimit': True})
SYMBOL, TIMEFRAME = '1000PEPE/USDT', '1m'
data_bot = {"precio": 0, "rsi": 0, "estado": "Iniciando...", "saldo": 0}

def motor():
    while True:
        try:
            balance = exchange.fetch_balance()
            data_bot["saldo"] = round(balance['free'].get('USDT', 0), 2)
            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
            data_bot["precio"] = df['c'].iloc[-1]
            delta = df['c'].diff()
            gan, per = delta.clip(lower=0).rolling(14).mean(), -delta.clip(upper=0).rolling(14).mean()
            data_bot["rsi"] = round(100 - (100 / (1 + (gan/per))).iloc[-1], 2)
            data_bot["estado"] = "🦅 CAZANDO EN 1000PEPE"
        except: data_bot["estado"] = "ERROR: Revisar Conexión"
        time.sleep(15)

@app.route('/')
def home():
    return f"""<body style="background:black;color:#00FF00;text-align:center;font-family:monospace;">
    <h1 style="color:gold;">🦅 AGUILA BOT</h1>
    <h2>PRECIO: {data_bot['precio']:.8f} | RSI: {data_bot['rsi']}</h2>
    <h2 style="background:#222;display:inline-block;padding:10px;">{data_bot['estado']}</h2>
    <h3>DISPONIBLE: {data_bot['saldo']} USDT</h3>
    <script>setTimeout(()=>location.reload(), 12000);</script></body>"""

threading.Thread(target=motor, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
