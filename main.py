import threading, os, datetime
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    sym, name = get_symbol_name()
    return f"Nextra Bot Running - Today: {name} ({sym})"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_flask, daemon=True).start()

import requests, time, yfinance as yf, random

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8929751892:AAFCXJqvt7iAWbXOvzds3BfugV4pBSqcQuw")
CHANNEL_ID = -1004445737129

# === المنطق الجديد: ذهب بالاسبوع - بيتكوين بالويكند ===
def get_symbol_name():
    weekday = datetime.datetime.utcnow().weekday()
    if weekday in [5, 6]:  # السبت =5 الأحد=6
        return "BTC-USD", "BITCOIN ₿"
    else:
        return "XAUUSD", "GOLD 🟡"

def get_data(p="2d", i="15m"):
    symbol, asset_name = get_symbol_name()
    try:
        if "BTC" in symbol:
            # بيتكوين شغال 24/7
            d = yf.download("BTC-USD", period=p, interval=i, progress=False)
        else:
            # ذهب - جرب GC=F أول وبعدين XAUUSD
            d = yf.download("GC=F", period=p, interval=i, progress=False)
            if d.empty:
                d = yf.download("XAUUSD=X", period=p, interval=i, progress=False)
        return d
    except:
        return None

def rsi(s, period=14):
    delta=s.diff(); gain=delta.where(delta>0,0); loss=-delta.where(delta<0,0)
    avg_gain=gain.ewm(alpha=1/period).mean(); avg_loss=loss.ewm(alpha=1/period).mean()
    rs=avg_gain/avg_loss
    return 100-(100/(1+rs))

def analyze():
    df15=get_data("2d","15m"); df1h=get_data("7d","1h")
    if df15 is None or df15.empty or df1h is None or df1h.empty:
        return None
    try:
        # تبسيط: نفس منطقك القديم بس مع الاسم الجديد
        c15=df15['Close']; c1h=df1h['Close']
        if isinstance(c15, type(df15)): c15=c15.iloc[:,0]
        if isinstance(c1h, type(df1h)): c1h=c1h.iloc[:,0]
        
        e50_15=c15.ewm(span=50).mean().iloc[-1]
        e200_15=c15.ewm(span=200).mean().iloc[-1]
        rsi15=rsi(c15).iloc[-1]
        
        price=c15.iloc[-1]
        symbol, asset_name = get_symbol_name()

        sig=None
        if price > e50_15 and e50_15 > e200_15 and rsi15 > 50 and rsi15 < 75:
            sig="BUY"
        elif price < e50_15 and e50_15 < e200_15 and rsi15 < 50 and rsi15 > 25:
            sig="SELL"

        if sig:
            return {"symbol":symbol, "asset":asset_name, "price":price, "signal":sig, "rsi":rsi15}
        return None
    except Exception as e:
        print(f"Analyze error: {e}")
        return None

def send_telegram(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id":CHANNEL_ID, "text":msg, "parse_mode":"HTML"})
    except Exception as e:
        print(e)

# Loop رئيسي
def main_loop():
    while True:
        res=analyze()
        if res:
            txt = f"""
🚀 <b>{res['asset']} SIGNAL - {res['signal']}</b>

Symbol: {res['symbol']}
Price: {res['price']:.2f}
RSI: {res['rsi']:.1f}
Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

Entry: {res['price']:.2f}
"""
            send_telegram(txt)
        time.sleep(3600)  # كل ساعة

threading.Thread(target=main_loop, daemon=True).start()
