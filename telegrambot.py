import logging
import requests
import datetime
import re
import sys
import asyncio
import time
from telegram import Update
import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

# --- GÜVENLİK VE AYARLAR ---
# 1. Telegram Bot Token (BotFather'dan):
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 2. Amadeus API Bilgileri (developers.amadeus.com'dan):
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")

# Loglama ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Kullanıcı verileri ve Token Hafızası
user_data_store = {}
amadeus_token_store = {
    "token": None,
    "expires_at": 0
}

# Konuşma Adımları
ORIGIN_STATE, DEST_STATE, DATE_STATE = 1, 2, 3

def get_amadeus_token():
    """
    Amadeus API için gerekli olan 'Access Token'ı alır.
    Token süresi dolmuşsa yenisini ister.
    """
    global amadeus_token_store
    
    # Mevcut token geçerli mi kontrol et (30 saniye tolerans - daha güvenli)
    if amadeus_token_store["token"] and time.time() < amadeus_token_store["expires_at"] - 30:
        return amadeus_token_store["token"]

    logger.info("Amadeus Token yenileniyor...")
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET
    }

    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        
        amadeus_token_store["token"] = json_data["access_token"]
        amadeus_token_store["expires_at"] = time.time() + json_data["expires_in"]
        
        logger.info(f"✅ Token başarıyla alındı (Geçerli: {json_data['expires_in']}s)")
        return amadeus_token_store["token"]
    except Exception as e:
        logger.error(f"❌ Token alma hatası: {e}")
        return None

def get_cheapest_flight_amadeus(origin, dest, date):
    """
    Amadeus API üzerinden uçuş arar.
    """
    token = get_amadeus_token()
    if not token:
        return "❌ API yetkilendirme hatası (Amadeus Key/Secret kontrol et)."

    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": dest,
        "departureDate": date,
        "adults": 1,
        "currencyCode": "TRY",
        "max": 1
    }

    logger.info(f"🔎 API İsteği: {origin} → {dest}, Tarih: {date}")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        
        # Detaylı Hata Kontrolleri
        if response.status_code == 401:
            logger.error("❌ Unauthorized - Token veya API Key hatalı")
            return "❌ Yetkilendirme hatası. Amadeus kimlik bilgileri kontrol et."
        
        if response.status_code == 400:
            error_data = response.json().get("errors", [])
            if error_data:
                error_msg = error_data[0].get("title", "Bilinmeyen hata")
                logger.warning(f"⚠️ 400 Hatası: {error_msg}")
            return (f"⚠️ Geçersiz istek - Rota ({origin}-{dest}) veya tarih ({date}) hatalı olabilir. "
                   f"Test ortamında bu rota için veri olmayabilir.")
        
        if response.status_code == 429:
            logger.error("⏱️ Rate limit - çok hızlı istek")
            return "⏱️ Çok hızlı istek gönderdin. Birkaç saniye bekle."
        
        if response.status_code >= 500:
            return "❌ Amadeus sunucusu şu anda hizmet vermiyor. Sonra dene."
        
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.Timeout:
        logger.error("⏱️ Bağlantı timeout")
        return "⏱️ İstek cevap almadan zaman aşımına uğradı. Sunucu yavaş, sonra dene."
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Bağlantı Hatası: {e}")
        return "❌ Sunucuya bağlanılamadı. İnternet bağlantını kontrol et."
    except ValueError:
        logger.error("❌ API geçersiz JSON döndürdü")
        return "❌ API geçersiz yanıt döndürdü."

    # Uçuş verisini kontrol et
    if "data" not in data or not data["data"]:
        logger.warning(f"⚠️ {date} tarihinde {origin}-{dest} uçuşu bulunamadı")
        return (f"⚠️ {date} tarihinde {origin} → {dest} için uçuş bulunamadı.\n\n"
               f"💡 İpuçları:\n"
               f"• Test ortamında veri sınırlı olabilir\n"
               f"• En az 2-3 gün ileri tarih dene\n"
               f"• Havalimanı kodlarını kontrol et (IST, ESB, AYT vb.)")

    try:
        offer = data["data"][0]
        
        # Fiyat
        price = offer["price"]["grandTotal"]
        currency = offer["price"]["currency"]
        
        # Seyahat Detayları
        itineraries = offer["itineraries"][0]
        segments = itineraries["segments"]
        
        first_segment = segments[0]
        last_segment = segments[-1]
        
        # Saatler
        departure_time = first_segment["departure"]["at"].split("T")[1][:5]
        arrival_time = last_segment["arrival"]["at"].split("T")[1][:5]
        
        # Süre
        duration_raw = itineraries["duration"]
        duration_text = duration_raw.replace("PT", "").replace("H", "h ").replace("M", "m")
        
        # Havayolu
        carrier_code = first_segment["carrierCode"]
        airlines = data.get("dictionaries", {}).get("carriers", {})
        carrier_name = airlines.get(carrier_code, carrier_code)
        
        # Booking URL
        booking_url = f"https://www.skyscanner.com.tr/tasimacilik/ucaklar/{origin}/{dest}/"

        return (
            f"🎫 **En Uygun Uçuş**\n\n"
            f"🛫 **Rota:** {origin} ➜ {dest}\n"
            f"📅 **Tarih:** {date}\n"
            f"🕒 **Saat:** {departure_time} - {arrival_time} ({duration_text})\n"
            f"✈️ **Firma:** {carrier_name}\n"
            f"💰 **Fiyat:** {price} {currency}\n\n"
            f"🔗 [Skyscanner'da Kontrol Et]({booking_url})"
        )

    except KeyError as e:
        logger.error(f"❌ Gerekli alan bulunamadı: {e}")
        return "❌ API yanıtında beklenen veri bulunamadı."
    except Exception as e:
        logger.error(f"❌ Veri işleme hatası: {e}", exc_info=True)
        return "❌ Veri işlenirken hata oluştu."

# --- Telegram İşlemleri ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Merhaba! Ben Amadeus destekli uçuş asistanınım.\n\n"
        "🇹🇷 Fiyatları TL olarak getiririm.\n"
        "📅 İstediğin tarihi sorgularım.\n"
        "♾️ Süresiz ücretsiz API kullanıyorum.\n\n"
        "Başlamak için: /setroute"
    )

async def setroute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛫 **Kalkış** havalimanı kodu nedir? (Örn: IST)")
    return ORIGIN_STATE

async def get_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    if len(text) != 3 or not text.isalpha():
        await update.message.reply_text("🚫 Lütfen 3 harfli kod gir (Örn: IST).")
        return ORIGIN_STATE
    
    context.user_data['origin'] = text
    await update.message.reply_text(f"✅ Kalkış: {text}\n🛬 **Varış** havalimanı kodu nedir? (Örn: ESB)")
    return DEST_STATE

async def get_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    if len(text) != 3 or not text.isalpha():
        await update.message.reply_text("🚫 3 harfli kod girmelisin.")
        return DEST_STATE
        
    context.user_data['dest'] = text
    await update.message.reply_text(
        f"✅ Rota: {context.user_data['origin']} ➜ {text}\n"
        "📅 Ne zaman gitmek istiyorsun?\n"
        "Lütfen **YYYY-AA-GG** formatında yaz.\n"
        "(Örnek: 2025-06-15)"
    )
    return DATE_STATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        await update.message.reply_text("🚫 Hatalı format! **YYYY-AA-GG** (Örn: 2025-06-15):")
        return DATE_STATE

    try:
        input_date = datetime.datetime.strptime(text, "%Y-%m-%d").date()
        if input_date < datetime.date.today():
            await update.message.reply_text("🚫 Geçmişe bilet alamazsın :) İleri bir tarih gir:")
            return DATE_STATE
    except ValueError:
        await update.message.reply_text("🚫 Geçersiz bir tarih girdin.")
        return DATE_STATE

    origin = context.user_data['origin']
    dest = context.user_data['dest']
    
    user_data_store[update.effective_user.id] = {
        'origin': origin,
        'dest': dest,
        'date': text
    }

    await update.message.reply_text(
        f"✅ **Plan Hazır!**\n"
        f"✈️ {origin} ➜ {dest}\n"
        f"📅 {text}\n\n"
        "Fiyatı görmek için tıkla: /check"
    )
    context.user_data.clear()
    return ConversationHandler.END

async def check_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data_store:
        await update.message.reply_text("⚠️ Kayıtlı plan yok. Önce /setroute yapmalısın.")
        return

    data = user_data_store[user_id]
    await update.message.reply_text(f"🔎 {data['origin']} ➜ {data['dest']} ({data['date']}) aranıyor...")
    
    # Amadeus API Çağrısı
    result = get_cheapest_flight_amadeus(data['origin'], data['dest'], data['date'])
    await update.message.reply_text(result, parse_mode='Markdown', disable_web_page_preview=True)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 İşlem iptal edildi.")
    context.user_data.clear()
    return ConversationHandler.END

def main():
    if "BURAYA_AMADEUS" in AMADEUS_API_KEY:
        print("[HATA] Lutfen kodun basindaki AMADEUS API bilgilerini doldur!")
        return

    # Windows Event Loop Düzeltmesi
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("setroute", setroute)],
        states={
            ORIGIN_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_origin)],
            DEST_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dest)],
            DATE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_price))
    app.add_handler(conv_handler)

    print("[BILGI] Bot Amadeus destegiyle aktif! Telegram'dan yazabilirsin.")
    app.run_polling()

if __name__ == "__main__":
    main()