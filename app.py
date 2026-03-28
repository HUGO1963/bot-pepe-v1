import os
from flask import Flask
from binance.client import Client
import pandas as pd
import pandas_ta as ta

app = Flask(__name__)

# Configuración básica
SYMBOL = 'PEPEUSDT'
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
INVESTMENT = 5.0

@app.route('/')
def dashboard():
    # Tablero verde sobre negro
    return """
    <body style="background-color:black;color:#00FF00;font-family:monospace;padding:20px;">
        <h1>BOT PEPE - RSI 30/70</h1>
        <p>Estado: Activo</p>
        <p>Ubicación: Virginia (Render)</p>
    </body>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
