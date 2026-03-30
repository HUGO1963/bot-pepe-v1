import time, threading, os, ccxt, pandas as pd
from flask import Flask

app = Flask(__name__)

# --- CONFIGURACIÓN COINEX ---
API_KEY = '8D9B0B4872544713BB5987467562E601'
API_SECRET = 'B8A35FC096757EE430B005A1D4BFE4B7399BF075CCF1E5E4'

# Conexión profesional con manejo de errores
try:
    exchange = ccxt.coinex({
        'apiKey': API_KEY, 
        'secret': API_SECRET, 
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
except Exception as e:
    print(f"Error de conexión inicial: {e}")

SYMBOL = '1000PEPE/USDT'
TIMEFRAME = '1m'

# Diccionario de datos para la web
data_bot = {
    "precio": 0,
    "rsi": 0,
    "estado": "Iniciando sistema...",
    "saldo": 0,
    "ultima_actualizacion": "Nunca"
}

# --- LÓGICA DEL MOTOR (EL ÁGUILA) ---
def motor():
    print("Motor iniciado...")
    while True:
        try:
            # 1. Obtener Saldo
            balance = exchange.fetch_balance()
            data_bot["saldo"] = round(balance['total'].get('USDT', 0), 2)

            # 2. Obtener Velas y Calcular RSI
            bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
            df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
            
            # Cálculo de RSI
            delta = df['c'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            data_bot["precio"] = df['c'].iloc[-1]
            data_bot["rsi"] = round(rsi.iloc[-1], 2)
            data_bot["ultima_actualizacion"] = time.strftime('%H:%M:%S')

            # 3. Lógica de Trading
            actual_rsi = data_bot["rsi"]
            if actual_rsi < 30:
                data_bot["estado"] = "🔥 OPORTUNIDAD DE COMPRA (RSI BAJO)"
            elif actual_rsi > 70:
                data_bot["estado"] = "🧊 ZONA DE VENTA (RSI ALTO)"
            else:
                data_bot["estado"] = "🦅 ÁGUILA VIGILANDO..."

        except Exception as e:
            data_bot["estado"] = f"Reconectando: {e}"
        
        time.sleep(30)

# Iniciar motor en hilo separado para que Flask no se trabe
threading.Thread(target=motor, daemon=True).start()

# --- INTERFAZ WEB (PARA RENDER) ---
@app.route('/')
def home():
    color_rsi = "white"
    if data_bot["rsi"] > 70: color_rsi = "#ff4d4d"
    if data_bot["rsi"] < 30: color_rsi = "#00ffcc"
    
    return f"""
    <html>
    <head>
        <title>AGUILA BOT - {SYMBOL}</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body {{ background: #0e1117; color: white; font-family: 'Segoe UI', sans-serif; text-align: center; padding-top: 50px; }}
            .container {{ background: #1a1c23; display: inline-block; padding: 40px; border-radius: 20px; border: 1px solid #333; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
            h1 {{ color: #00ff00; margin-bottom: 10px; }}
            .data {{ font-size: 24px; margin: 20px 0; }}
            .status {{ background: #333; padding: 10px; border-radius: 10px; font-weight: bold; color: yellow; }}
            .update {{ font-size: 12px; color: #666; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦅 ÁGUILA BOT v1.1</h1>
            <p>Operando en: <b>{SYMBOL}</b></p>
            <hr style="border: 0.5px solid #444;">
            <div class="data">
                <p>💰 SALDO: <span style="color:#00ff00;">{data_bot['saldo']} USDT</span></p>
                <p>📈 PRECIO: {data_bot['precio']}</p>
                <p>📊 RSI: <span style="color:{color_rsi};">{data_bot['rsi']}</span></p>
            </div>
            <div class="status">{data_bot['estado']}</div>
            <div class="update">Última actualización: {data_bot['ultima_actualizacion']} (Mar del Plata)</div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Render usa el puerto que le asigna el sistema
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
