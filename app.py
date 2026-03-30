import time, threading, os, ccxt, pandas as pd
from flask import Flask

app = Flask(__name__)

# --- CONFIGURACIÓN COINEX ---
# Estas son tus llaves nuevas con permiso de LEER y TRADEAR
API_KEY = '8D9B0B4872544713BB5987467562E601'
API_SECRET = 'B8A35FC096757EE430B005A1D4BFE4B7399BF075CCF1E5E4'

# Conexión con el mercado (Modo Swaps para ver tus USDT de futuros)
exchange = ccxt.coinex({
    'apiKey': API_KEY, 
    'secret': API_SECRET, 
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

SYMBOL = '1000PEPE/USDT'
TIMEFRAME = '1m'

data_bot = {
    "precio": 0,
    "rsi": 0,
    "estado": "Iniciando Águila...",
    "saldo": 0
}

# --- MOTOR DE TRADING ---
def motor():
    while True:
        try:
            # 1. Actualizar Saldo Real
            balance = exchange.fetch_balance()
            data_bot["saldo"] = round(balance['total'].get('USDT', 0), 2)

            # 2. Calcular RSI y Precio
            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
            delta = df['c'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            data_bot["precio"] = df['c'].iloc[-1]
            data_bot["rsi"] = round(rsi.iloc[-1], 2)
            data_bot["estado"] = "🦅 Vigilando el mercado..."

        except Exception as e:
            data_bot["estado"] = f"Error: {e}"
        
        time.sleep(30)

threading.Thread(target=motor, daemon=True).start()

# --- INTERFAZ VISUAL ---
@app.route('/')
def home():
    return f"""
    <body style="background:#121212; color:white; font-family:sans-serif; text-align:center; padding-top:50px;">
        <h1 style="color:#00ff00;">🦅 AGUILA BOT v1.0</h1>
        <hr style="width:300px; border:1px solid #333;">
        <div style="font-size:1.5em; margin:20px;">
            <p>💰 DISPONIBLE: <span style="color:yellow;">{data_bot['saldo']} USDT</span></p>
            <p>📈 PRECIO PEPE: {data_bot['precio']}</p>
            <p>📊 RSI (14): {data_bot['rsi']}</p>
        </div>
        <p>ESTADO: {data_bot['estado']}</p>
    </body>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
