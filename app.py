import time
import threading
import os
import ccxt
import pandas as pd
from flask import Flask

app = Flask(__name__)

# SIN API (modo seguro)
exchange = ccxt.binance({
    'enableRateLimit': True,
})

SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m'

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
            data_bot["estado"] = "Conectando..."

            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])

            precio = float(df['c'].iloc[-1])
            rsi_val = calcular_rsi(df['c'])

            if pd.isna(rsi_val):
                data_bot["estado"] = "Calculando..."
                time.sleep(5)
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
            data_bot["estado"] = "ERROR: " + str(e)

        time.sleep(20)

# 🔥 ARRANQUE FORZADO (IMPORTANTE)
def start_bot():
