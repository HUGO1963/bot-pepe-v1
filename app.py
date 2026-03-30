import time
import threading
import os
import ccxt
import pandas as pd
from flask import Flask

app = Flask(__name__)

# --- CONFIGURACIÓN COINEX ---
API_KEY = '0CD4EAE1BBAA4628B65AAB8660D8278F'
API_SECRET = '4C7C6BF5D2A82687085E95C28A8A548237800D11FDF4A4C5'

exchange = ccxt.coinex({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})

# --- EL PAR CORRECTO ---
SYMBOL = '1000PEPE/USDT' 
TIMEFRAME = '1m'

data_bot = {"precio": 0, "rsi": 0, "estado": "Iniciando...", "saldo": 0}

def calcular_rsi(cierres, periodo=14):
    delta = cierres.diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    media_ganancia = ganancia.rolling(window=periodo).mean()
    media_perdida = perdida.rolling(window=periodo).mean()
    rs = media_ganancia / media_perdida
    return 100 - (100 / (1 + rs)).iloc[-1]

def motor():
    while True:
        try:
            # Traer tu saldo de 12.51 USDT
            balance = exchange.fetch_balance()
            data_bot["saldo"] = round(balance['free'].get('USDT', 0), 2)
            
            # Mercado
            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
            precio = df['c'].iloc[-1]
            rsi_val = calcular_rsi(df['c'])

            data_bot["precio"] = precio
            data_bot["rsi"] = round(rsi_val, 2)
            data_bot["estado"] = "🦅 CAZANDO EN 1000PEPE"

        except Exception as e:
            data_bot["estado"] = "ERROR: Revisar Conexión"
        time.sleep(15)

@app.route('/')
def home():
    return f"""
    <body style="background-color:black; color:#00FF00; font-family:monospace; text-align:center; padding-top:50px;">
        <h1 style="color:gold;">🦅 AGUILA BOT - COINEX</h1>
        <hr style="width:50%; border:1px solid #333; margin:auto;">
        <h2 style="font-size:32px;">PRECIO PEPE: {data_bot['precio']:.8f}</h2>
        <h2 style="color:lawngreen;">RSI: {data_bot['rsi']}</h2>
        <h2 style="background-color:#222; padding:15px; border-radius:10px; display:inline-block;">{data_bot['estado']}</h2>
        <br><br>
        <h3 style="color:white;">DISPONIBLE: {data_bot['saldo']} USDT</h3>
        <script>setTimeout(function(){{ location.reload(); }}, 10000);</script>
    </body>
    """

threading.Thread(target=motor, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
