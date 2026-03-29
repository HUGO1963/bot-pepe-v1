import time
import threading
import os
import ccxt
import pandas as pd
from flask import Flask

app = Flask(__name__)

# API (COINEX)
API_KEY = '0CD4EAE1BBAA4628B65AAB8660D8278F'
API_SECRET = '4C7C6BF5D2A82687085E95C28A8A548237800D11FDF4A4C5'

exchange = ccxt.coinex({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})

# CONFIGURACIÓN (MODO PRUEBA)
SYMBOL = 'BTC/USDT'   # 👈 SOLO TEST
TIMEFRAME = '1m'
MONTO_USDT = 5

# RANGO
PRECIO_MIN = 0
PRECIO_MAX = 999999999

# ESTADO
data_bot = {"precio": 0, "rsi": 0, "estado": "Iniciando...", "saldo": 0}
en_posicion = False

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
    global en_posicion

    while True:
        try:
            balance = exchange.fetch_balance()
            usdt = balance['free'].get('USDT', 0)

            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])

            precio = float(df['c'].iloc[-1])
            rsi_val = calcular_rsi(df['c'])

            if pd.isna(rsi_val):
                data_bot["estado"] = "Calculando indicadores..."
                time.sleep(10)
                continue

            data_bot["precio"] = precio
            data_bot["rsi"] = round(rsi_val, 2)
            data_bot["saldo"] = round(usdt, 4)

            # SOLO SEÑALES (NO OPERA)
            if rsi_val <= 30:
                data_bot["estado"] = "SEÑAL DE COMPRA (RSI BAJO)"
            elif rsi_val >= 70:
                data_bot["estado"] = "SEÑAL DE VENTA (RSI ALTO)"
            else:
                data_bot["estado"] = "ESPERANDO SEÑAL"

        except Exception as e:
            data_bot["estado"] = str(e)

        time.sleep(30)

# WEB
@app.route('/')
def home():
    return f"""
    <body style="background-color:black; color:#00FF00; font-family:monospace; text-align:center; padding-top:50px;">
        <h1 style="color:gold;">🦅 AGUILA BOT - TEST</h1>
        <h2>PRECIO: {data_bot['precio']}</h2>
        <h2>RSI: {data_bot['rsi']}</h2>
        <h2>{data_bot['estado']}</h2>
        <h3>USDT: {data_bot['saldo']}</h3>
        <script>setTimeout(function(){{ location.reload(); }}, 20000);</script>
    </body>
    """

# INICIO
threading.Thread(target=motor, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
