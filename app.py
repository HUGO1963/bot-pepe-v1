import time
import threading
import os
import ccxt
import pandas as pd
from flask import Flask

app = Flask(__name__)

# API (CAMBIAR DESPUÉS)
API_KEY = '0CD4EAE1BBAA4628B65AAB8660D8278F'
API_SECRET = '4C7C6BF5D2A82687085E95C28A8A548237800D11FDF4A4C5'

exchange = ccxt.coinex({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})

# CONFIG
SYMBOL = 'PEPE/USDT'
TIMEFRAME = '1m'
MONTO_USDT = 5

# RANGO
PRECIO_MIN = 0.00000850
PRECIO_MAX = 0.00001250

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
            pepe = balance['free'].get('PEPE', 0)

            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])

            precio = float(df['c'].iloc[-1])
            rsi = calcular_rsi(df['c'])

            # Evita RSI inválido
            if pd.isna(rsi):
                time.sleep(30)
                continue

            data_bot["precio"] = precio
            data_bot["rsi"] = round(rsi, 2)
            data_bot["saldo"] = round(usdt, 4)

            # FUERA DE RANGO
            if precio < PRECIO_MIN or precio > PRECIO_MAX:
                data_bot["estado"] = "FUERA DE RANGO - BOT DETENIDO"

                if en_posicion and pepe > 0:
                    try:
                        exchange.create_market_sell_order(SYMBOL, pepe)
                        en_posicion = False
                        data_bot["estado"] = "SALIO DEL RANGO - VENDIDO"
                    except Exception as e:
                        data_bot["estado"] = "ERROR VENTA FUERA RANGO"

            else:
                # COMPRA
                if rsi <= 30 and not en_posicion and usdt >= MONTO_USDT:
                    cantidad = MONTO_USDT / precio
                    try:
                        exchange.create_market_buy_order(SYMBOL, cantidad)
                        en_posicion = True
                        data_bot["estado"] = "COMPRADO"
                    except Exception as e:
                        data_bot["estado"] = "ERROR COMPRA"

                # VENTA
                elif rsi >= 70 and en_posicion and pepe > 0:
                    try:
                        exchange.create_market_sell_order(SYMBOL, pepe)
                        en_posicion = False
                        data_bot["estado"] = "VENDIDO"
                    except Exception as e:
                        data_bot["estado"] = "ERROR VENTA"

                else:
                    data_bot["estado"] = "EN RANGO - ESPERANDO"

        except Exception as e:
            data_bot["estado"] = "ERROR GENERAL"

        time.sleep(30)

# WEB
@app.route('/')
def home():
    return f"""
    <body style="background-color:black; color:#00FF00; font-family:monospace; text-align:center;">
        <h1>AGUILA BOT - PEPE</h1>
        <h2>PRECIO: {data_bot['precio']}</h2>
        <h2>RSI: {data_bot['rsi']}</h2>
        <h2>{data_bot['estado']}</h2>
        <h3>USDT: {data_bot['saldo']}</h3>
        <p>RANGO: {PRECIO_MIN} - {PRECIO_MAX}</p>
        <script>setTimeout(function(){{ location.reload(); }}, 30000);</script>
    </body>
    """

# INICIO
threading.Thread(target=motor, daemon=True).start()

# PUERTO RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
