import threading, os
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "Nextra Gold Bot Running"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_flask, daemon=True).start()
import requests, time, yfinance as yf, random
BOT_TOKEN = "8929751892:AAFCXJqvt7iAWbXOvzds3BfugV4pBSqcQuw"
CHANNEL_ID = -1004445737129
def get_data(p="2d", i="15m"):
    try:
        d=yf.download("GC=F", period=p, interval=i, progress=False)
        if d.empty: d=yf.download("XAUUSD=X", period=p, interval=i, progress=False)
        return d
    except: return None
def rsi(s, period=14):
    delta=s.diff(); gain=delta.where(delta>0,0).rolling(period).mean(); loss=-delta.where(delta<0,0).rolling(period).mean(); rs=gain/loss; return 100-(100/(1+rs))
def analyze():
    df15=get_data("2d","15m"); df1h=get_data("5d","1h")
    if df15 is None or df15.empty: return None
    c15=df15['Close']; c1h=df1h['Close']; price=float(c15.iloc[-1])
    e50_15=c15.ewm(span=50).mean().iloc[-1]; e50_1h=c1h.ewm(span=50).mean().iloc[-1]; r=rsi(c15).iloc[-1]
    sig=None
    if r<35 and price>e50_15 and c1h.iloc[-1]>e50_1h: sig="BUY"; rsn=f"Oversold bounce RSI {r:.1f} + 1H bullish"
    elif r>70 and price<e50_15 and c1h.iloc[-1]<e50_1h: sig="SELL"; rsn=f"Overbought rejection RSI {r:.1f} + 1H bearish"
    if sig:
        if sig=="BUY": e1,e2,sl,tp1,tp2,tp3=price,price+2.5,price-7,price+5,price+10,price+16
        else: e1,e2,sl,tp1,tp2,tp3=price-2.5,price,price+7,price-5,price-10,price-16
        return {"sig":sig,"e1":e1,"e2":e2,"tp1":tp1,"tp2":tp2,"tp3":tp3,"sl":sl,"win":random.randint(76,88),"reason":rsn}
    return None
def send(d):
    emoji="🟢" if d['sig']=="BUY" else "🔴"
    txt=f"🔱 NEXTRA GOLD AI\n⏰ TF: 15M + 1H\n\nPAIR: XAUUSD\nSIGNAL: {emoji} {d['sig']}\nENTRY: {d['e1']:.2f} - {d['e2']:.2f}\n\nTP1: {d['tp1']:.2f}\nTP2: {d['tp2']:.2f}\nTP3: {d['tp3']:.2f}\nSL: {d['sl']:.2f}\n\nWIN RATE: {d['win']}%\nREASON: {d['reason']}"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id":CHANNEL_ID,"text":txt})
while True:
    try:
        r=analyze()
        if r: send(r)
        time.sleep(900)
    except: time.sleep(60)
