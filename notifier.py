import requests

# 🔧 Replace with your actual Telegram Bot token and chat ID
TELEGRAM_TOKEN =7623383153:AAHGF3VTXruX0BZijd9BxExgJwJv_SdYPpw
TELEGRAM_CHAT_ID =1448932058

def send_telegram_alert(signal: dict) -> bool:
    message = f"""
📊 *{signal['pair']} Signal Alert*

*Action:* {signal['action']}
*Trend:* {signal['trend_direction'].title()}
*Confidence:* {signal['confidence_level']}%
*Entry Price:* {signal['entry_price']}
*Live Price:* {signal['live_price']}
*Distance to Entry:* {round(signal['distance_to_entry'], 5)}
*Take Profit:* {signal['take_profit']}
*Stop Loss:* {signal['stop_loss']}
🟢 *Entry Ready:* {'✅ YES' if signal['entry_ready'] else '❌ NO'}

_Reason:_ {signal['reason']}
    """.strip()

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ Telegram send failed: {e}")
        return False
