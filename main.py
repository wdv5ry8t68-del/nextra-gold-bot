import os, datetime, threading, time, requests
import yfinance as yf
from flask import Flask

app = Flask(__name__)

# === المنطق الجديد: ذهب بالاسبوع - بيتكوين بالويكند ===
def get_symbol_name():
    weekday = datetime.datetime.utcnow().weekday()
    if weekday in [5, 6]:  # السبت=5 الأحد=6
        return "BTC-USD", "BITCOIN ₿"
    else:
        return "GC=F", "GOLD 🟡"

@app.route('/')
def home():
    sym, name = get_symbol_name()
    return f"Nextra Bot Running - Today: {name} ({sym}) - {datetime.datetime.utcnow()}"

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8929751892:AAFCXJqvt7iAWbXOvzds3BfugV4pBSqcQuw") # تأكد من التوكن ب Environment
CHANNEL_ID = -1004445737129

def rsi(s, period=14):
    delta=s.diff(); gain=delta.where(delta>0,0); loss=-delta.where(delta<0,0)
    avg_gain=gain.ewm(alpha=1/period).mean(); avg_loss=loss.ewm(alpha=1/period).mean()
    rs=avg_gain/avg_loss
    return 100-(100/(1+rs))

def analyze():
    symbol, asset_name = get_symbol_name()
    try:
        df = yf.download(symbol, period="2d", interval="15m", progress=False)
        if df.empty: return None
        c = df['Close']
        if hasattr(c, 'iloc') and c.ndim > 1: c = c.iloc[:,0]
        
        e50 = c.ewm(span=50).mean().iloc[-1]
        e200 = c.ewm(span=200).mean().iloc[-1]
        r = rsi(c).iloc[-1]
        price = c.iloc[-1]

        sig=None
        if price > e50 and e50 > e200 and 50 < r < 75: sig="BUY"
        elif price < e50 and e50 < e200 and 25 < r < 50: sig="SELL"
        
        if sig:
            return {"symbol":symbol, "asset":asset_name, "price":price, "signal":sig, "rsi":r}
        return None
    except Exception as e:
        print(f"Analyze error: {e}")
        return None

def send_telegram(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id":CHANNEL_ID, "text":msg, "parse_mode":"HTML"}, timeout=10)
    except: pass

def main_loop():
    while True:
        res=analyze()
        if res:
            txt = f"🚀 <b>{res['asset']} SIGNAL - {res['signal']}</b>\n\nSymbol: {res['symbol']}\nPrice: {res['price']:.2f}\nRSI: {res['rsi']:.1f}\nTime: {datetime.datetime.utcnow().strftime('%H:%M UTC')}"
            send_telegram(txt)
        time.sleep(3600)

# شغل اللوب بالخلفية
threading.Thread(target=main_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
@app.route('/calc')
def calc():
    return """
<!DOCTYPE html>
<html dir="rtl">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NEXTRA Risk Calculator</title>
<style>
body{background:#0f0f0f;color:white;font-family:Arial;padding:20px;direction:rtl}
.box{background:#1a1a1a;padding:20px;border-radius:15px;max-width:400px;margin:auto}
input{width:100%;padding:12px;margin:8px 0;border-radius:10px;border:none;background:#2a2a2a;color:white;font-size:16px}
button{width:100%;padding:14px;background:#00ff88;border:none;border-radius:10px;font-size:18px;font-weight:bold;margin-top:10px}
.result{background:#222;padding:15px;border-radius:10px;margin-top:15px;line-height:1.8}
span{color:#00ff88;font-weight:bold}
</style>
</head>
<body>
<div class="box">
<h2>📊 NEXTRA | حاسبة المخاطرة</h2>
<input id="entry" type="number" placeholder="سعر الدخول مثلا 3873">
<input id="sl" type="number" placeholder="وقف الخسارة مثلا 3869">
<input id="tp" type="number" placeholder="الهدف مثلا 3887">
<input id="balance" type="number" placeholder="رصيدك $ مثلا 1000">
<button onclick="calcRR()">احسب 🔥</button>
<div id="res" class="result" style="display:none"></div>
</div>
<script>
function calcRR(){
 let e=parseFloat(entry.value), s=parseFloat(sl.value), t=parseFloat(tp.value), b=parseFloat(balance.value)||1000;
 if(!e||!s||!t){alert("عبي كل الخانات");return}
 let risk=Math.abs(e-s);
 let reward=Math.abs(t-e);
 let rr=(reward/risk).toFixed(2);
 let riskMoney=(b*0.01).toFixed(2);
 document.getElementById('res').style.display='block';
 document.getElementById('res').innerHTML=`
 ✅ المخاطرة: <span>${risk.toFixed(2)} $</span><br>
 ✅ الربح: <span>${reward.toFixed(2)} $</span><br>
 📈 Risk/Reward: <span>1 : ${rr}</span><br>
 💰 لو راس مالك ${b}$ وبتخاطر 1% = <span>${riskMoney}$</span><br>
 ${rr>=2?'🔥 صفقة ممتازة!': rr>=1.5?'⚠️ مقبولة':'❌ لا تدخل - RR ضعيف'}
 `;
}
</script>
</body>
</html>
    """
