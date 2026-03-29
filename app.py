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

# CONFIGURACIÓN
SYMBOL = 'PEPE/USDT'
TIMEFRAME = '1m'
MONTO_USDT = 5

# RANGO DE OPERACIÓN
PRECIO_MIN = 0.00000850
PRECIO_MAX = 0.00001250

# ESTADO DEL BOT
data_bot = {"precio": 0, "rsi": 0, "estado": "Iniciando...", "saldo": 0}
en_posicion = False

# FUNCIÓN RSI MANUAL (Sustituye a pandas_ta para evitar errores)
def calcular_rsi(cierres, periodo=14):
    delta = cierres.diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    media_ganancia = ganancia.rolling(window=periodo).mean()
    media_perdida = perdida.rolling(window=periodo).mean()
    rs = media_ganancia / media_perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# MOTOR DEL BOT
def motor():
    global en_posicion
    while True:
        try:
            balance = exchange.fetch_balance()
            usdt = balance['free'].get('USDT', 0)
            pepe = balance['free'].get('PEPE', 0)

            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])

            precio = df['c'].iloc[-1]
            rsi_val = calcular_rsi(df['c'])

            if pd.isna(rsi_val):
                data_bot["estado"] = "Calculando indicadores..."
                time.sleep(10)
                continue

            data_bot["precio"] = precio
            data_bot["rsi"] = round(rsi_val, 2)
            data_bot["saldo"] = round(usdt, 4)

            # CONTROL DE RANGO
            if precio < PRECIO_MIN or precio > PRECIO_MAX:
                data_bot["estado"] = "FUERA DE RANGO - PROTECCIÓN"
                if en_posicion and pepe > 0:
                    try:
                        exchange.create_market_sell_order(SYMBOL, pepe)
                        en_posicion = False
                        data_bot["estado"] = "VENTA FUERA RANGO"
                    except:
                        data_bot["estado"] = "ERROR VENTA RANGO"
            else:
                # LÓGICA RSI 30/70
                if rsi_val <= 30 and not en_posicion and usdt >= MONTO_USDT:
                    cantidad = MONTO_USDT / precio
                    try:
                        exchange.create_market_buy_order(SYMBOL, cantidad)
                        en_posicion = True
                        data_bot["estado"] = "COMPRADO"
                    except:
                        data_bot["estado"] = "ERROR COMPRA"
                elif rsi_val >= 70 and en_posicion and pepe > 0:
                    try:
                        exchange.create_market_sell_order(SYMBOL, pepe)
                        en_posicion = False
                        data_bot["estado"] = "VENDIDO"
                    except:
                        data_bot["estado"] = "ERROR VENTA"
                else:
                    data_bot["estado"] = "EN RANGO - CAZANDO"

        except Exception as e:
            data_bot["estado"] = "ERROR CONEXIÓN COINEX"

        time.sleep(30)

# WEB
@app.route('/')
def home():
    return f"""
    <body style="background-color:black; color:#00FF00; font-family:monospace; text-align:center; padding-top:50px;">
        <h1 style="color:gold;">🦅 AGUILA BOT - COINEX</h1>
        <hr style="width:50%; border:1px solid #333;">
        <h2 style="font-size:32px;">PRECIO PEPE: {data_bot['precio']:.8f}</h2>
        <h2 style="color:lawngreen;">RSI: {data_bot['rsi']}</h2>
        <h2 style="background-color:#222; padding:15px; border-radius:10px; display:inline-block;">{data_bot['estado']}</h2>
        <h3>DISPONIBLE: {data_bot['saldo']} USDT</h3>
        <p style="color:#666;">RANGO: {PRECIO_MIN:.8f} - {PRECIO_MAX:.8f}</p>
        <script>setTimeout(function(){{ location.reload(); }}, 20000);</script>
    </body>
    """

threading.Thread(target=motor, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
