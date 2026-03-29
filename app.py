import os
import time
import threading
import ccxt
import pandas as pd
import pandas_ta as ta
from flask import Flask

app = Flask(__name__)

# CREDENCIALES AGUILA BOT
ID_ACCESO = '0CD4EAE1BBAA4628B65AAB8660D8278F'
CLAVE_SECRETA = '4C7C6BF5D2A82687085E95C28A8A548237800D11FDF4A4C5'

exchange = ccxt.coinex({
    'apiKey': ID_ACCESO,
    'secret': CLAVE_SECRETA,
    'enableRateLimit': True,
})

# Memoria compartida
data_bot = {"precio": 0, "rsi": 0, "estado": "Iniciando...", "saldo": 0}

def motor_escorpion():
    while True:
        try:
            # Datos de PEPE y Saldo
            balance = exchange.fetch_balance()
            data_bot["saldo"] = balance['free'].get('USDT', 0)
            
            bars = exchange.fetch_ohlcv('PEPE/USDT', timeframe='1m', limit=50)
            df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
            
            # Cálculo de RSI 14
            rsi_val = ta.rsi(df['c'], length=14).iloc[-1]
            data_bot["rsi"] = round(rsi_val, 2)
            data_bot["precio"] = df['c'].iloc[-1]

            # Lógica 30/70
            if rsi_val <= 30:
                data_bot["estado"] = "ZONA DE COMPRA (RSI BAJO)"
            elif rsi_val >= 70:
                data_bot["estado"] = "ZONA DE VENTA (RSI ALTO)"
            else:
                data_bot["estado"] = "ACECHANDO (ESPERANDO SEÑAL)"

        except:
            data_bot["estado"] = "Reconectando..."
        time.sleep(30)

@app.route('/')
def home():
    return f"""
    <body style="background-color:black; color:#00FF00; font-family:monospace; padding:20px; text-align:center;">
        <h1 style="border:2px solid #00FF00; display:inline-block; padding:10px;">AGUILA BOT - PEPE</h1>
        <hr color="#00FF00">
        <h2 style="font-size:45px;">PRECIO: {data_bot['precio']}</h2>
        <h2 style="font-size:45px;">RSI: {data_bot['rsi']}</h2>
        <h2 style="background-color:#002200; padding:10px;">{data_bot['estado']}</h2>
        <hr color="#00FF00">
        <h3>SALDO EN COINEX: {data_bot['saldo']} USDT</h3>
        <script>setTimeout(function(){{ location.reload(); }}, 30000);</script>
    </body>
    """

if __name__ == "__main__":
    threading.Thread(target=motor_escorpion, daemon=True).start()
    # Puerto dinámico: Render elige el que necesita
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)
