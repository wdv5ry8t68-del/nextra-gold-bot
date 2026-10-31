import os
import requests
import yfinance as yf
import pandas as pd
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = "8929751892:AAFCXJqvt7iAWbXOvzds3BfugV4pBSqcQuw"
CHAT_ID = "-1004445737129"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        r = requests.post(url, json=data, timeout=15)
        print("Telegram result:", r.text)
        return r.text
    except Exception as e:
        print(e)
        return str(e)

def get_data():
    try:
        btc = yf.download("BTC-USD", period="3d", interval="1h", auto_adjust=True)
        if btc.empty:
            return None
        # fix multiindex if exists
        if isinstance(btc.columns, pd.MultiIndex):
            btc.columns = btc.columns.get_level_values(0)
        btc['SMA50'] = btc['Close'].rolling(50).mean()
        delta = btc['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain / loss
        btc['RSI'] = 100 - (100/(1+rs))
        return btc.dropna()
    except Exception as e:
        print("get_data error", e)
        return None

@app.route('/')
def home():
    df = get_data()
    price = float(df.iloc[-1]['Close']) if df is not None else 0
    return f"Nextra Bot Live ✅ - BTC {price:.2f} - /test للتجربة"

@app.route('/test')
def test():
    df = get_data()
    price = float(df.iloc[-1]['Close']) if df is not None else 108000
    msg = f"✅ تيست ناجح NEXTRA!\n\nالبوت مربوط صح 100%\n\nسعر BTC الحالي: {price:.2f}$\nقناة NEXTRA جاهزة 🔥"
    result = send_telegram(msg)
    return f"<h2>تم الارسال لقناة NEXTRA!</h2><p>{result}</p><p>السعر: {price}</p>"

@app.route('/scan')
def scan():
    df = get_data()
    if df is None:
        return "فشل جلب البيانات"
    last = df.iloc[-1]
    prev = df.iloc[-2]
    close = float(last['Close'])
    sma50 = float(last['SMA50'])
    rsi = float(last['RSI'])
    
    signal = None
    if close > sma50 and 45 < rsi < 78 and rsi > float(prev['RSI']):
        signal = "BUY"
    elif close < sma50 and 22 < rsi < 55 and rsi < float(prev['RSI']):
        signal = "SELL"
    
    if signal:
        entry = close
        if signal == "BUY":
            sl = entry * 0.992
            tp1 = entry * 1.008
            tp2 = entry * 1.015
            tp3 = entry * 1.025
            emoji = "🟢"
        else:
            sl = entry * 1.008
            tp1 = entry * 0.992
            tp2 = entry * 0.985
            tp3 = entry * 0.975
            emoji = "🔴"
        
        msg = f"""📊 NEXTRA | {signal} SIGNAL {emoji}

🔹 Asset: BTCUSD
🔹 Direction: {signal}

🔸 Entry: {entry:.0f}
🔸 Stop Loss: {sl:.0f}
🔸 Take Profit 1: {tp1:.0f}
🔸 Take Profit 2: {tp2:.0f}
🔸 Take Profit 3: {tp3:.0f} (Runner)

⚖️ Risk: 1%
📈 Reason: {signal} above/below SMA50 + RSI {rsi:.1f}
#BTC #NEXTRA"""
        send_telegram(msg)
        return f"اشارة {signal} مرسلة - {entry}"
    else:
        return f"لا اشارة الان - سعر {close:.2f} - RSI {rsi:.1f} فوق SMA50: {close>sma50}"

@app.route('/calc')
def calc():
    return """<!DOCTYPE html><html dir="rtl"><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>NEXTRA Calc</title><style>body{background:#0f0f0f;color:white;font-family:Arial;padding:20px;direction:rtl}.box{background:#1a1a1a;padding:20px;border-radius:15px;max-width:400px;margin:auto}input{width:100%;padding:12px;margin:8px 0;border-radius:10px;border:none;background:#2a2a2a;color:white;font-size:16px}button{width:100%;padding:14px;background:#00ff88;border:none;border-radius:10px;font-size:18px;font-weight:bold;margin-top:10px}.result{background:#222;padding:15px;border-radius:10px;margin-top:15px;line-height:1.8}span{color:#00ff88;font-weight:bold}</style></head><body><div class="box"><h2>📊 NEXTRA | حاسبة المخاطرة</h2><input id="entry" type="number" placeholder="دخول 3873"><input id="sl" type="number" placeholder="ستوب 3869"><input id="tp" type="number" placeholder="هدف 3887"><input id="balance" type="number" placeholder="رصيد 1000"><button onclick="calcRR()">احسب 🔥</button><div id="res" class="result" style="display:none"></div></div><script>function calcRR(){let e=parseFloat(entry.value),s=parseFloat(sl.value),t=parseFloat(tp.value),b=parseFloat(balance.value)||1000;if(!e||!s||!t){alert("عبي كل الخانات");return}let risk=Math.abs(e-s);let reward=Math.abs(t-e);let rr=(reward/risk).toFixed(2);document.getElementById('res').style.display='block';document.getElementById('res').innerHTML=`مخاطرة: <span>${risk.toFixed(2)}</span><br>ربح: <span>${reward.toFixed(2)}</span><br>RR: <span>1:${rr}</span><br>${rr>=2?'🔥 ممتازة':rr>=1.5?'⚠️ مقبولة':'❌ ضعيفة'}`}</script></body></html>"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
