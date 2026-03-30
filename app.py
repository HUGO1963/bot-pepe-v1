import time, threading, os, ccxt, pandas as pd
from flask import Flask

app = Flask(__name__)

# --- CONFIGURACIÓN ---
API_KEY = '8D9B0B4872544713BB5987467562E601'
API_SECRET = 'B8A35FC096757EE430B005A1D4BFE4B7399BF075CCF1E5E4'
exchange = ccxt.coinex({'apiKey': API_KEY, 'secret': API_SECRET, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})

datos = {"saldo": "Cargando...", "precio": 0, "rsi": 0, "hora": "Esperando..."}

def motor():
    while True:
        try:
            balance = exchange.fetch_balance()
            datos["saldo"] = balance['total'].get('USDT', 0)
            bars = exchange.fetch_ohlcv('1000PEPE/USDT', timeframe='1m', limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
            delta = df['c'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss)))
            datos["precio"] = df['c'].iloc[-1]
            datos["rsi"] = round(rsi.iloc[-1], 2)
            datos["hora"] = time.strftime('%H:%M:%S')
        except Exception as e:
            datos["hora"] = f"Error: {e}"
        time.sleep(20)

threading.Thread(target=motor, daemon=True).start()

@app.route('/')
def home():
    return f"""
    <h1>AGUILA BOT v1.2 (Modo Liviano)</h1>
    <hr>
    <h2>💰 SALDO: {datos['saldo']} USDT</h2>
    <h3>📈 PRECIO PEPE: {datos['precio']}</h3>
    <h3>📊 RSI: {datos['rsi']}</h3>
    <p>Ultima vuelta: {datos['hora']} (Mar del Plata)</p>
    <script>setTimeout(function(){{ location.reload(); }}, 20000);</script>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
