import time
import threading
import os
import ccxt
import pandas as pd
from flask import Flask

app = Flask(__name__)

# ⚠️ SIN API (MODO SEGURO)
exchange = ccxt.binance({
    'enableRateLimit': True,
})

# CONFIG
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m'

# ESTADO
data_bot = {"precio": 0, "rsi": 0, "estado": "Iniciando..."}

# RSI
def calcular_rsi(cierres, periodo=14):
    delta = cierres.diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    media_ganancia = ganancia.rolling(window=periodo).mean()
    media_perdida = perdida.rolling(window=periodo).mean()
    rs = media_ganancia / media_perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# MOTOR
def motor():
    while True:
        try:
            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])

            precio = float(df['c'].iloc[-1])
            rsi_val = calcular_rsi(df['c'])

            if pd.isna(rsi_val):
                data_bot["estado"] = "Calculando..."
                time.sleep(10)
                continue

            data_bot["precio"] = precio
            data_bot["rsi"] = round(rsi_val, 2)

            if rsi_val <= 30:
                data_bot["estado"] = "SEÑAL COMPRA"
            elif rsi_val >= 70:
                data_bot["estado"] = "SEÑAL VENTA"
            else:
                data_bot["estado"] = "ESPERANDO"

        except Exception as e:
            data_bot["estado"] = str(e)

        time.sleep(20)

# WEB
@app.route('/')
def home():
    return f"""
    <body style="background-color:black; color:#00FF00; font-family:monospace; text-align:center; padding-top:50px;">
        <h1 style="color:gold;">🦅 AGUILA BOT - SEGURO</h1>
        <h2>PRECIO BTC: {data_bot['precio']}</h2>
        <h2>RSI: {data_bot['rsi']}</h2>
        <h2>{data_bot['estado']}</h2>
        <script>setTimeout(function(){{ location.reload(); }}, 20000);</script>
    </body>
    """

threading.Thread(target=motor, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
